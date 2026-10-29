# Changelog

All notable changes to homelab-kube are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- The media trial's apps run with `DOTNET_EnableWriteXorExecute=0`: both crashed with SIGSEGV every few seconds
  on the cluster's nodes.
- The media trial's health checks are TCP port checks: the copied configs' Allowed Hosts answered 400 to the
  kubelet's HTTP checks.
- The media trial's Sonarr and Radarr run (1 replica each) now that their configs are copied in.

### Added

- The media trial (`apps/media-trial.yaml`, `manifests/media-trial/`): Sonarr 4.0.20 and Radarr 6.4.4 (the same
  images as the Compose stack) at 0 replicas, each with a 10 GiB Longhorn config volume, the shared read-only media
  claim bound to a hand-applied volume, Traefik routes under `/sonarr-k8s` and `/radarr-k8s`, and a network policy
  that blocks every private network. `docs/media-trial.md` covers copying a config in and the checklist.
- The policy check accepts the well-known special-use ranges written as CIDRs (`10.0.0.0/8`, `0.0.0.0/0`, ...);
  any other private address is still refused.
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
