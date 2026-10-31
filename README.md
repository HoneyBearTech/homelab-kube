# homelab-kube

[![CI](https://github.com/HoneyBearTech/homelab-kube/actions/workflows/ci.yml/badge.svg)](https://github.com/HoneyBearTech/homelab-kube/actions/workflows/ci.yml)
[![CodeQL](https://github.com/HoneyBearTech/homelab-kube/actions/workflows/codeql.yml/badge.svg)](https://github.com/HoneyBearTech/homelab-kube/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/HoneyBearTech/homelab-kube/badge)](https://scorecard.dev/viewer/?uri=github.com/HoneyBearTech/homelab-kube)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/16098/badge)](https://www.bestpractices.dev/projects/16098)
[![OpenSSF Baseline](https://www.bestpractices.dev/projects/16098/baseline)](https://www.bestpractices.dev/projects/16098)

Kubernetes manifests for a small homelab k3s cluster, applied by Argo CD from this repository: every Helm chart
and image version-pinned, kept as code so a merge to `main` is a deploy and a revert is a rollback.

> [!WARNING]
> A merge to `main` changes the cluster within minutes: Argo CD syncs every Application automatically, prunes what
> was removed, and reverts manual changes. The Headlamp login account in
> [`manifests/headlamp-access/`](manifests/headlamp-access/admin.yaml) is cluster-admin; anyone who can make a
> token for it controls the cluster. Keep the cluster's API, Argo CD and Headlamp on a trusted network
> ([docs/security.md](docs/security.md)).

## Documentation

- [Quick start](docs/quick-start.md): from a running k3s cluster to Argo CD and Headlamp
- [Installing](docs/installing.md): what the cluster needs first, installing Argo CD, the root Application,
  running it securely, uninstalling
- [Upgrading](docs/upgrading.md): bumping a chart, upgrading Argo CD and k3s, rolling back
- [Media trial](docs/media-trial.md): Sonarr and Radarr on copied configs, what keeps them harmless, copying a config in
- [Architecture](docs/architecture.md): the cluster, the Applications, and how a change reaches the cluster
- [Interfaces](docs/interfaces.md): every Application, setting, annotation and command
- [Verifying releases](docs/verifying-releases.md): checking signatures, checksums, provenance and the SBOM
- [Security requirements](docs/security.md): what the manifests protect, what they don't, where secrets live
- [Assurance case](docs/assurance-case.md): threat model, trust boundaries, secure design, common weaknesses
- [Dependencies](docs/dependencies.md): how charts, images and tools are chosen, pinned, tracked and patched
- [Roadmap](docs/roadmap.md): the next year, and what homelab-kube will not do
- Project policies: [CONTRIBUTING](CONTRIBUTING.md) · [SECURITY](SECURITY.md) · [GOVERNANCE](GOVERNANCE.md) ·
  [SUPPORT](SUPPORT.md) · [CODE OF CONDUCT](CODE_OF_CONDUCT.md) · [CHANGELOG](CHANGELOG.md)

## What's in it

- [`bootstrap/root.yaml`](bootstrap/root.yaml): the one manifest applied by hand. An Argo CD Application that syncs
  every Application in `apps/` ("app of apps").
- [`apps/`](apps/): one Argo CD Application per component:
  - **headlamp**: [Headlamp](https://headlamp.dev), the cluster's web UI, from its Helm chart, on a LoadBalancer
    address. Its own ServiceAccount gets no cluster role; it acts with the token you log in with.
  - **headlamp-access**: the `headlamp-admin` ServiceAccount you log in to Headlamp with.
  - **longhorn**: [Longhorn](https://longhorn.io) replicated block storage on the agents' dedicated disks, as the
    default StorageClass `longhorn` (two replicas, volumes kept when a claim is deleted).
  - **media-trial**: Sonarr and Radarr beside a Compose stack, on copied configs, with read-only media and no
    access to the private network ([docs/media-trial.md](docs/media-trial.md)).
- [`manifests/`](manifests/): plain manifests the Applications point at.
- [`scripts/check_manifests.py`](scripts/check_manifests.py): the policy check CI runs on every change.

  - **longhorn-backups**: nightly backups of every Longhorn volume, keeping 14 ([docs/longhorn-backups.md](docs/longhorn-backups.md)).

Planned: see the [roadmap](docs/roadmap.md).

## Getting started

You need a k3s (or other Kubernetes) cluster with a LoadBalancer implementation, `kubectl` with an admin
kubeconfig, and `helm`. Then:

```sh
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd --version 10.11.6 --namespace argocd --create-namespace \
  --set server.service.type=LoadBalancer --set dex.enabled=false
kubectl apply -f bootstrap/root.yaml
```

Argo CD then installs everything in `apps/`. The full steps, including the first login and changing the initial
password, are in the [quick start](docs/quick-start.md).

## Configuration

There is nothing to configure in this repository for one cluster: chart values are inline in each Application,
and nothing site-specific (addresses, domains, host names) is committed. What a cluster provides itself is listed
in [docs/installing.md](docs/installing.md#what-the-cluster-provides): the LoadBalancer address pool, DNS names
and any reverse proxy in front.

## Running it securely

- Reach the API, Argo CD and Headlamp only from a trusted network or VPN; nothing here is meant for the internet.
- Change Argo CD's initial admin password and delete `argocd-initial-admin-secret`.
- Make Headlamp tokens short-lived (`kubectl -n headlamp create token headlamp-admin --duration=8h`).
- Protect `main`: Argo CD deploys whatever is merged there.

More in [docs/security.md](docs/security.md).

## License

[MIT](LICENSE).
