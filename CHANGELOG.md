# Changelog

All notable changes to homelab-kube are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Longhorn 1.13.0 (Helm chart): replicated block storage on the agents, as the default StorageClass `longhorn`
  with two replicas and `Retain` reclaim; the UI stays ClusterIP; synced with server-side apply.
- `bootstrap/root.yaml`: the root Argo CD Application ("app of apps") that syncs every Application in `apps/` from
  `main`, with automated sync, pruning and self-heal.
- Headlamp 0.46.0 (Helm chart), the cluster's web UI, on a LoadBalancer address; its own ServiceAccount has no
  cluster role.
- The `headlamp-admin` ServiceAccount (cluster-admin) for logging in to Headlamp with short-lived tokens.
- `scripts/check_manifests.py`: the manifest policy (pinned charts, git sources and images; no Secrets; nothing
  privileged; no private addresses or internal names in any public file), with unit tests and a CycloneDX SBOM of
  the Helm charts for releases.
- CI (ruff, yamllint, actionlint, gitleaks, tests with coverage, the policy check, kubeconform), CodeQL, DCO,
  dependency review, OpenSSF Scorecard, Dependabot, and a release workflow that signs checksums keylessly and
  attaches SLSA provenance.
- Project documentation and policies.
