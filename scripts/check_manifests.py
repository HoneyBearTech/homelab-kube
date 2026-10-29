"""Policy check for the repository's Kubernetes manifests and public files.

Rules (docs/security.md#policy):
  pinned-chart     an Argo CD Application's Helm chart has an exact version (1.2.3), never a range or "latest"
  pinned-git       a git source follows this repository's main branch, or another repository's full commit SHA
  pinned-image     every container image is pinned as name:tag@sha256:<digest>
  no-secret        no Secret objects are committed
  no-privileged    no privileged containers, host network, host PID or host IPC
  public-safe      no private IP addresses, internal domains (.lan, .internal, .home.arpa) or names matching the
                   PUBLIC_SAFE_DENY regular expression in any committed text file

A manifest may opt out of one rule with the annotation  homelab-kube/allow-<rule>: "<reason>"  (public-safe and
no-secret can't be waived). Exits 1 and prints one line per finding if anything fails.

  python scripts/check_manifests.py [repo dir] [--sbom FILE]   (--sbom writes a CycloneDX list of the charts)
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator

REPO_URL = "https://github.com/HoneyBearTech/homelab-kube.git"
MANIFEST_DIRS = ("bootstrap", "apps", "manifests")
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".toml", ".in", ".txt", ".json"}
SKIP_DIRS = {".git", ".venv", "node_modules", "fixtures", ".ruff_cache", ".pytest_cache"}
ALLOW_PREFIX = "homelab-kube/allow-"
UNWAIVABLE = {"no-secret", "public-safe"}

SEMVER = re.compile(r"^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
IPV4 = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])")
INTERNAL_DOMAIN = re.compile(r"\b[a-z0-9-]+\.(?:lan|home\.arpa|internal)\b", re.IGNORECASE)
# Site-specific names (the owner's domains, host names) are never written here: CI passes them as a regular
# expression in the PUBLIC_SAFE_DENY secret, and a local run can set the same variable.
DENY_ENV = "PUBLIC_SAFE_DENY"
# RFC 5737 documentation ranges may appear in examples.
EXAMPLE_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]

POD_KINDS = {"Pod", "Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob"}


def pod_spec(doc: dict[str, Any]) -> dict[str, Any] | None:
    """Return the pod spec of a workload object, or None."""
    kind = doc.get("kind")
    spec = doc.get("spec") or {}
    if kind == "Pod":
        return spec
    if kind == "CronJob":
        return (((spec.get("jobTemplate") or {}).get("spec") or {}).get("template") or {}).get("spec")
    if kind in POD_KINDS:
        return (spec.get("template") or {}).get("spec")
    return None


def allowed(doc: dict[str, Any], rule: str) -> bool:
    """Whether the object waives a rule with a non-empty reason."""
    annotations = (doc.get("metadata") or {}).get("annotations") or {}
    return rule not in UNWAIVABLE and bool(str(annotations.get(ALLOW_PREFIX + rule, "")).strip())


def app_sources(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the source(s) of an Argo CD Application."""
    spec = doc.get("spec") or {}
    sources = list(spec.get("sources") or [])
    if spec.get("source"):
        sources.append(spec["source"])
    return sources


def check_application(doc: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """Yield (rule, message) for an Argo CD Application's sources."""
    for source in app_sources(doc):
        revision = str(source.get("targetRevision", ""))
        if "chart" in source:
            if not SEMVER.match(revision) and not allowed(doc, "pinned-chart"):
                yield "pinned-chart", f"chart {source['chart']} has version {revision!r}, not an exact version"
        elif source.get("repoURL") == REPO_URL:
            if revision != "main" and not allowed(doc, "pinned-git"):
                yield "pinned-git", f"this repository must be followed at main, not {revision!r}"
        elif not COMMIT_SHA.match(revision) and not allowed(doc, "pinned-git"):
            yield "pinned-git", f"{source.get('repoURL')} at {revision!r}, not a full commit SHA"


def check_workload(doc: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """Yield (rule, message) for a workload's images and host access."""
    spec = pod_spec(doc)
    if spec is None:
        return
    for key in ("hostNetwork", "hostPID", "hostIPC"):
        if spec.get(key) is True and not allowed(doc, "no-privileged"):
            yield "no-privileged", f"{key} is on"
    for container in (spec.get("initContainers") or []) + (spec.get("containers") or []):
        name = container.get("name", "?")
        image = str(container.get("image", ""))
        if not DIGEST.search(image) and not allowed(doc, "pinned-image"):
            yield "pinned-image", f"container {name}: image {image!r} isn't pinned by digest"
        privileged = (container.get("securityContext") or {}).get("privileged") is True
        if privileged and not allowed(doc, "no-privileged"):
            yield "no-privileged", f"container {name} is privileged"


def check_document(doc: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """Yield (rule, message) for one Kubernetes object."""
    kind = doc.get("kind")
    if kind == "Secret":
        yield "no-secret", "Secret objects must not be committed"
    if kind == "Application" and str(doc.get("apiVersion", "")).startswith("argoproj.io/"):
        yield from check_application(doc)
    yield from check_workload(doc)


def manifest_files(root: Path) -> list[Path]:
    """Every YAML file under the manifest directories."""
    found: list[Path] = []
    for name in MANIFEST_DIRS:
        base = root / name
        if base.is_dir():
            found += sorted(p for p in base.rglob("*") if p.suffix in {".yaml", ".yml"})
    return found


def text_files(root: Path) -> list[Path]:
    """Every committed-looking text file, outside tool and fixture directories."""
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix in TEXT_SUFFIXES and not SKIP_DIRS.intersection(p.relative_to(root).parts)
    )


def public_safety(path: Path, text: str, deny: re.Pattern[str] | None = None) -> Iterator[str]:
    """Yield a message for every private address, internal domain or denied name in a file."""
    for number, line in enumerate(text.splitlines(), 1):
        for match in IPV4.finditer(line):
            try:
                address = ipaddress.ip_address(match.group(1))
            except ValueError:
                continue
            if address.is_private and not address.is_loopback and not any(address in n for n in EXAMPLE_NETS):
                yield f"{path}:{number}: private address {address}"
        for pattern, label in ((INTERNAL_DOMAIN, "internal domain"), (deny, "denied name")):
            found = pattern.search(line) if pattern else None
            if found:
                yield f"{path}:{number}: {label} {found.group(0)}"


def check(root: Path, deny: re.Pattern[str] | None = None) -> tuple[list[str], list[dict[str, Any]]]:
    """Check a repository; return the findings and every Application (for the SBOM)."""
    findings: list[str] = []
    applications: list[dict[str, Any]] = []
    for path in manifest_files(root):
        rel = path.relative_to(root)
        try:
            docs = [d for d in yaml.safe_load_all(path.read_text(encoding="utf-8")) if d is not None]
        except yaml.YAMLError as error:
            findings.append(f"{rel}: not valid YAML ({error})")
            continue
        for doc in docs:
            if not isinstance(doc, dict) or "kind" not in doc or "apiVersion" not in doc:
                findings.append(f"{rel}: a document without kind and apiVersion")
                continue
            if doc["kind"] == "Application":
                applications.append(doc)
            name = (doc.get("metadata") or {}).get("name", "?")
            findings += [f"{rel}: {doc['kind']}/{name}: [{rule}] {msg}" for rule, msg in check_document(doc)]
    for path in text_files(root):
        rel = path.relative_to(root)
        findings += [f"[public-safe] {line}" for line in public_safety(rel, path.read_text(encoding="utf-8"), deny)]
    return findings, applications


def sbom(applications: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a CycloneDX 1.6 document listing every Helm chart the Applications deploy."""
    components = []
    for doc in applications:
        for source in app_sources(doc):
            if "chart" in source:
                version = str(source["targetRevision"])
                components.append(
                    {
                        "type": "application",
                        "name": source["chart"],
                        "version": version,
                        "purl": f"pkg:helm/{source['chart']}@{version}?repository_url={source['repoURL']}",
                    },
                )
    components.sort(key=lambda c: (c["name"], c["version"]))
    return {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1, "components": components}


def main(argv: list[str] | None = None) -> int:
    """Run the check; print findings; optionally write the SBOM."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--sbom", type=Path, help="write a CycloneDX SBOM of the Helm charts here")
    args = parser.parse_args(argv)
    deny_text = os.environ.get(DENY_ENV, "").strip()
    findings, applications = check(args.root, re.compile(deny_text, re.IGNORECASE) if deny_text else None)
    for finding in findings:
        print(finding)
    if findings:
        print(f"{len(findings)} finding(s)", file=sys.stderr)
        return 1
    if args.sbom:
        args.sbom.write_text(json.dumps(sbom(applications), indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(applications)} Application(s), every rule met")
    return 0


if __name__ == "__main__":
    sys.exit(main())
