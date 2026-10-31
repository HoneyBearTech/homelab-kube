# Changelog

All notable changes to homelab-kube are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Nightly Longhorn backups (`apps/longhorn-backups.yaml`): every volume at 10:30 UTC, keeping 14, to a backup
  target set on the cluster by hand ([docs/longhorn-backups.md](docs/longhorn-backups.md)).

## [0.1.0] - 2026-10-30

The first release: a small k3s cluster driven from this repository by Argo CD.

### Added

- `bootstrap/root.yaml`: the root Argo CD Application ("app of apps") that syncs every Application in `apps/` from
  `main`, with automated sync, pruning and self-heal.
- `apps/argocd.yaml`: Argo CD manages its own Helm release (chart argo-cd 10.11.6, release `argocd`), so upgrades
  are pull requests; never pruned automatically; server-side apply.
- Headlamp 0.46.0 (Helm chart), the cluster's web UI, on a LoadBalancer address; its own ServiceAccount has no
  cluster role. The `headlamp-admin` ServiceAccount (cluster-admin) for logging in with short-lived tokens.
- Longhorn 1.13.0 (Helm chart): replicated block storage on the agents as the default StorageClass `longhorn`, two
  replicas, `Retain` reclaim, the UI ClusterIP only; pods stuck on a failed agent are deleted
  (`nodeDownPodDeletionPolicy`) so their volumes move with the replacement pods.
- The Argus agent (`apps/argus-agent.yaml`, `manifests/argus-agent/`): a DaemonSet that sends every node's metrics
  and logs to [Argus](https://github.com/HoneyBearTech/Argus) ([docs/argus-agent.md](docs/argus-agent.md)).
- The media trial (`apps/media-trial.yaml`, `manifests/media-trial/`, [docs/media-trial.md](docs/media-trial.md)):
  Sonarr 4.0.20 and Radarr 6.4.4 beside a Compose stack, on copied configs, each with a 10 GiB Longhorn config
  volume, the media read-only from a hand-applied volume, Traefik routes under `/sonarr-k8s` and `/radarr-k8s`
  (TCP health checks, since copied configs may restrict Allowed Hosts), `RuntimeDefault` seccomp, and a network
  policy that blocks every private network.
- `scripts/check_manifests.py`: the manifest policy (pinned charts, git sources and images; no Secrets; nothing
  privileged without a reason; no private addresses or internal names in any public file, apart from the
  well-known special-use ranges written as CIDRs), with unit tests and a CycloneDX SBOM of the Helm charts.
- `renovate.json`: Renovate proposes Helm chart and image bumps as pull requests, weekly, never auto-merged.
- CI (ruff, yamllint, actionlint, gitleaks, tests with coverage, the policy check, kubeconform), CodeQL, DCO,
  dependency review, OpenSSF Scorecard, Dependabot, and a release workflow that signs checksums keylessly and
  attaches SLSA provenance.
- Project documentation and policies, with the OpenSSF Best Practices and Baseline badges.

### Known issues

- On Ubuntu kernel 7.0.0-42, .NET applications (such as Sonarr and Radarr) abort every few seconds on CPUs without
  AVX2: the kernel logs a general protection fault in `abort()` of the C library. 7.0.0-38 is not affected. Run the
  agents that host .NET apps on an unaffected kernel until a fixed one is released.

[Unreleased]: https://github.com/HoneyBearTech/homelab-kube/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/HoneyBearTech/homelab-kube/releases/tag/v0.1.0
