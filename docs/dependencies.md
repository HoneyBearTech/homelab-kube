# Dependencies and vulnerability management

How homelab-kube chooses, obtains, tracks and updates what it's built from, and what happens when one of those
dependencies has a vulnerability.

homelab-kube's dependencies are almost entirely the **Helm charts and images** the cluster runs (today Headlamp).
The rest are the tools its checks and tests use and the GitHub Actions in its workflows. Its own code, the policy
checker, uses the Python standard library and PyYAML.

## Choosing a dependency

A new chart, image or tool must:

- be open source under an OSI-approved license (the apps' own licenses apply to them: homelab-kube pins and
  configures them, it doesn't redistribute them);
- be actively maintained: releases in the last year, security issues answered, and published for `linux/amd64`;
- come from the project itself: its official chart repository and registry; and
- be worth it: a new Application needs a reason in the pull request that adds it.

## Obtaining dependencies

| Dependency | Declared in | Pinned by | Fetched by |
| --- | --- | --- | --- |
| Helm charts | `apps/*.yaml` (`targetRevision`) | exact chart version (Renovate proposes bumps) | Argo CD |
| Images in plain manifests | `manifests/` | version tag and digest | the cluster's nodes |
| Images inside charts | the chart version | the chart's own pins | the cluster's nodes |
| Check and test tools (pytest, coverage, PyYAML, ruff, yamllint) | [`requirements-dev.in`](../requirements-dev.in) → [`requirements-dev.txt`](../requirements-dev.txt) | exact version and SHA-256 hashes | `pip install --require-hashes --no-deps` |
| kubeconform and the Argo CD schemas (CI only) | [`ci.yml`](../.github/workflows/ci.yml), [`Makefile`](../Makefile) | release version and SHA-256; catalog commit SHA | `curl` |
| Linters and scanners used only by CI (actionlint, gitleaks) | [`ci.yml`](../.github/workflows/ci.yml) | version tag and digest | Docker |
| GitHub Actions | [`.github/workflows/`](../.github/workflows/) | full commit SHA (version in a comment) | GitHub Actions |

Each release carries a CycloneDX SBOM listing every Helm chart and version ([verifying-releases.md](verifying-releases.md)).
To update the Python tools: `uv pip compile --generate-hashes --universal requirements-dev.in -o requirements-dev.txt`.

## Tracking dependencies

- **Renovate** ([`renovate.json`](../renovate.json), run by the Mend Renovate GitHub App) proposes updates for Argo CD
  charts in `apps/` and `bootstrap/`, Kubernetes images in `manifests/`, Python requirements, and GitHub Actions.
  It checks before 6am on Monday in America/Chicago, groups minor and patch updates, and keeps major updates separate.
  Renovate opens pull requests and a dependency dashboard issue. **Nothing is merged automatically**: a merge deploys,
  so the maintainer reads release notes and merges by hand ([upgrading.md](upgrading.md#bumping-a-chart)).
- **Dependabot alerts** remain enabled for vulnerability findings and are triaged below. Disable Dependabot security
  updates after migrating version updates to Renovate. Renovate also raises OSV vulnerability alerts labeled `security`.
- **A merge deploys.** Argo CD syncs `main` automatically, so every merge reaches the maintainer's cluster within
  minutes.
- **Dependency review** blocks a pull request that adds a Python or Actions dependency with a known vulnerability
  of moderate severity or higher, or a license outside the allowlist.
- The CI-only tools pinned in `run:` steps (actionlint, gitleaks, kubeconform) aren't seen by dependency managers;
  they're bumped by hand at least every quarter.
- **Nothing in the cluster updates itself from a registry.** Argo CD applies only what is merged.

## Policy for vulnerabilities in dependencies

Known vulnerabilities are found through Dependabot alerts and the charts' and images' own advisories. Each finding
is triaged within 14 days:

1. **If a fixed version exists**, bump to it by pull request; the merge deploys it. A fix for an exploitable critical
   or high-severity vulnerability goes out in a patch release within 30 days; others with the next release.
2. **If upstream hasn't released a fix**, assess whether it's reachable here (everything is on a trusted network,
   behind a login). If it is, mitigate where possible and say so in the release notes; otherwise record the reason.
3. **If a chart or image is abandoned**, replace it.

### Current findings

None known.

## Licenses

homelab-kube's own files are MIT-licensed. The Python tools must be under an OSI-approved license that dependency
review allows; yamllint (GPL-3.0) is allowed as a development tool. Charts and images keep their own licenses.

## Policy for findings from static analysis (SAST)

CodeQL analyses the checker and the workflows on every pull request and weekly, and ruff runs the bandit security
rules in CI. A CodeQL finding of medium severity or higher is fixed before the next release, or, if it is a false
positive, dismissed in code scanning with a written reason. A ruff finding fails CI; a deliberate exception is a
per-line `noqa` with the reason next to it.
