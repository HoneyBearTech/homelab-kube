import json
import re
from pathlib import Path

import check_manifests as cm
import pytest

REPO = Path(__file__).resolve().parent.parent

APP = """
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: demo
  namespace: argocd
{annotations}
spec:
  project: default
  source:
{source}
  destination:
    server: https://kubernetes.default.svc
    namespace: demo
"""

CHART = """    repoURL: https://charts.example.com/
    chart: demo
    targetRevision: {rev}"""

DEPLOYMENT = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
{annotations}
spec:
  template:
    spec:
      {host}
      containers:
        - name: web
          image: {image}
          {sc}
"""

PINNED = "example/web:1.0@sha256:" + "a" * 64


def make_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def app(source: str, annotations: str = "") -> str:
    return APP.format(source=source, annotations=annotations)


def deployment(image: str = PINNED, host: str = "", sc: str = "", annotations: str = "") -> str:
    return DEPLOYMENT.format(image=image, host=host, sc=sc, annotations=annotations)


def findings(tmp_path: Path, files: dict[str, str], deny: str | None = None) -> list[str]:
    root = make_repo(tmp_path, files)
    return cm.check(root, re.compile(deny) if deny else None)[0]


def test_the_repository_itself_passes() -> None:
    found, applications = cm.check(REPO)
    assert found == []
    assert {a["metadata"]["name"] for a in applications} >= {"root", "headlamp"}


def test_exact_chart_version_passes(tmp_path: Path) -> None:
    assert findings(tmp_path, {"apps/a.yaml": app(CHART.format(rev="1.2.3"))}) == []


@pytest.mark.parametrize("rev", ["1.2.*", "~1.2", ">=1.0.0", "latest", ""])
def test_loose_chart_version_fails(tmp_path: Path, rev: str) -> None:
    found = findings(tmp_path, {"apps/a.yaml": app(CHART.format(rev=f'"{rev}"'))})
    assert len(found) == 1
    assert "[pinned-chart]" in found[0]


def test_chart_waiver_needs_a_reason(tmp_path: Path) -> None:
    empty = '  annotations:\n    homelab-kube/allow-pinned-chart: ""'
    reason = '  annotations:\n    homelab-kube/allow-pinned-chart: "testing a release candidate"'
    assert findings(tmp_path, {"apps/a.yaml": app(CHART.format(rev="latest"), empty)})
    assert findings(tmp_path, {"apps/a.yaml": app(CHART.format(rev="latest"), reason)}) == []


def test_own_repo_must_follow_main(tmp_path: Path) -> None:
    source = f"    repoURL: {cm.REPO_URL}\n    targetRevision: {{rev}}\n    path: apps"
    assert findings(tmp_path, {"apps/a.yaml": app(source.format(rev="main"))}) == []
    found = findings(tmp_path, {"apps/b.yaml": app(source.format(rev="HEAD"))})
    assert "[pinned-git]" in found[0]


def test_other_git_repo_needs_a_commit_sha(tmp_path: Path) -> None:
    source = "    repoURL: https://git.example.com/x.git\n    targetRevision: {rev}\n    path: deploy"
    assert findings(tmp_path, {"apps/a.yaml": app(source.format(rev="c" * 40))}) == []
    assert "[pinned-git]" in findings(tmp_path, {"apps/b.yaml": app(source.format(rev="v1.0.0"))})[0]


def test_multiple_sources_are_checked(tmp_path: Path) -> None:
    text = app("").replace(
        "  source:\n",
        "  sources:\n    - repoURL: https://charts.example.com/\n      chart: a\n      targetRevision: latest\n",
    )
    assert "[pinned-chart]" in findings(tmp_path, {"apps/a.yaml": text})[0]


def test_unpinned_image_fails(tmp_path: Path) -> None:
    assert findings(tmp_path, {"manifests/x/d.yaml": deployment()}) == []
    found = findings(tmp_path, {"manifests/x/d.yaml": deployment(image="example/web:1.0")})
    assert "[pinned-image]" in found[0]


@pytest.mark.parametrize(
    ("host", "sc"),
    [("hostNetwork: true", ""), ("hostPID: true", ""), ("", "securityContext: {privileged: true}")],
)
def test_privileged_fails_unless_waived(tmp_path: Path, host: str, sc: str) -> None:
    found = findings(tmp_path, {"manifests/x/d.yaml": deployment(host=host, sc=sc)})
    assert "[no-privileged]" in found[0]
    waiver = '  annotations:\n    homelab-kube/allow-no-privileged: "needs the host network"'
    assert findings(tmp_path, {"manifests/x/d.yaml": deployment(host=host, sc=sc, annotations=waiver)}) == []


def test_cronjob_and_pod_images_are_checked(tmp_path: Path) -> None:
    cron = (
        "apiVersion: batch/v1\nkind: CronJob\nmetadata: {name: c}\nspec:\n  jobTemplate:\n    spec:\n"
        "      template:\n        spec:\n          containers: [{name: c, image: busybox}]\n"
    )
    pod = "apiVersion: v1\nkind: Pod\nmetadata: {name: p}\nspec:\n  initContainers: [{name: i, image: busybox}]\n"
    found = findings(tmp_path, {"manifests/x/c.yaml": cron, "manifests/x/p.yaml": pod})
    assert len(found) == 2


def test_secrets_fail_even_with_a_waiver(tmp_path: Path) -> None:
    manifest = (
        "apiVersion: v1\nkind: Secret\nmetadata:\n  name: s\n  annotations:\n"
        '    homelab-kube/allow-no-secret: "please"\n'
    )
    assert "[no-secret]" in findings(tmp_path, {"manifests/x/s.yaml": manifest})[0]


def test_bad_yaml_and_bare_documents_fail(tmp_path: Path) -> None:
    found = findings(tmp_path, {"apps/a.yaml": "a: [", "apps/b.yaml": "just: a mapping\n"})
    assert any("not valid YAML" in f for f in found)
    assert any("without kind" in f for f in found)


def test_private_addresses_and_internal_domains_fail(tmp_path: Path) -> None:
    text = (REPO / "tests/fixtures/unsafe.md").read_text()
    found = findings(tmp_path, {"docs/x.md": text})
    assert len(found) == 4
    assert all(f.startswith("[public-safe] docs/x.md:") for f in found)


def test_version_numbers_are_not_addresses(tmp_path: Path) -> None:
    assert findings(tmp_path, {"docs/x.md": "chart 10.11.6 and 1.2.3.4.5 and 999.1.1.1\n"}) == []


def test_denied_names_come_from_the_environment(tmp_path: Path) -> None:
    files = {"README.md": "see example-site.org\n"}
    assert findings(tmp_path, files) == []
    assert "denied name" in findings(tmp_path, files, deny=r"example-site\.org")[0]


def test_fixtures_and_tool_dirs_are_skipped(tmp_path: Path) -> None:
    unsafe = (REPO / "tests/fixtures/unsafe.md").read_text()
    files = {"tests/fixtures/x.md": unsafe, ".venv/y.md": unsafe, "notes.bin": unsafe}
    assert findings(tmp_path, files) == []


def test_main_writes_an_sbom(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.delenv(cm.DENY_ENV, raising=False)
    root = make_repo(tmp_path / "repo", {"apps/a.yaml": app(CHART.format(rev="1.2.3"))})
    out = tmp_path / "sbom.json"
    assert cm.main([str(root), "--sbom", str(out)]) == 0
    bom = json.loads(out.read_text())
    assert bom["components"][0]["purl"] == "pkg:helm/demo@1.2.3?repository_url=https://charts.example.com/"
    assert "OK: 1 Application(s)" in capsys.readouterr().out


def test_main_fails_with_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setenv(cm.DENY_ENV, r"example-site\.org")
    root = make_repo(tmp_path, {"README.md": "example-site.org\n"})
    assert cm.main([str(root)]) == 1
    assert "denied name" in capsys.readouterr().out
