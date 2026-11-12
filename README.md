# homelab-kube

[![CI](https://github.com/HoneyBearTech/homelab-kube/actions/workflows/ci.yml/badge.svg)](https://github.com/HoneyBearTech/homelab-kube/actions/workflows/ci.yml)
[![CodeQL](https://github.com/HoneyBearTech/homelab-kube/actions/workflows/codeql.yml/badge.svg)](https://github.com/HoneyBearTech/homelab-kube/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/HoneyBearTech/homelab-kube/badge)](https://scorecard.dev/viewer/?uri=github.com/HoneyBearTech/homelab-kube)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/16098/badge)](https://www.bestpractices.dev/projects/16098)
[![OpenSSF Baseline](https://www.bestpractices.dev/projects/16098/baseline)](https://www.bestpractices.dev/projects/16098)

`homelab-kube` manages a small homelab Kubernetes cluster with Argo CD. The root Application watches `apps/`,
which in turn applies the Helm charts and manifests in this repository. Chart and image versions are pinned; a
merge to `main` is deployed automatically, and reverting a change rolls it back.

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
- [The *arr apps](docs/arr.md): shadows beside the Compose stack, then moved live one at a time
- [Architecture](docs/architecture.md): the cluster, the Applications, and how a change reaches the cluster
- [Interfaces](docs/interfaces.md): every Application, setting, annotation and command
- [Verifying releases](docs/verifying-releases.md): checking signatures, checksums, provenance and the SBOM
- [Security requirements](docs/security.md): what the manifests protect, what they don't, where secrets live
- [Assurance case](docs/assurance-case.md): threat model, trust boundaries, secure design, common weaknesses
- [Dependencies](docs/dependencies.md): how charts, images and tools are chosen, pinned, tracked and patched
- [Roadmap](docs/roadmap.md): the next year, and what homelab-kube will not do
- Project policies: [CONTRIBUTING](CONTRIBUTING.md) · [SECURITY](SECURITY.md) · [GOVERNANCE](GOVERNANCE.md) ·
  [SUPPORT](SUPPORT.md) · [CODE OF CONDUCT](CODE_OF_CONDUCT.md) · [CHANGELOG](CHANGELOG.md)

For first-time setup, begin with [Installing](docs/installing.md) for cluster prerequisites, then follow the
[Quick start](docs/quick-start.md). The [documentation index](docs/README.md) groups setup, operations, and
reference material.

## What's in it

- [`bootstrap/root.yaml`](bootstrap/root.yaml): the one manifest applied by hand. An Argo CD Application that syncs
  every Application in `apps/` ("app of apps").
- [`apps/`](apps/): one Argo CD Application per component:
  - **argocd**: the Argo CD controller, installed from its pinned Helm chart.
  - **argus-agent**: node metrics and pod logs sent to Argus ([docs/argus-agent.md](docs/argus-agent.md)).
  - **arr**: the *arr apps beside a Compose stack, as read-only shadows first, then moved live one at a time
    ([docs/arr.md](docs/arr.md)).
  - **headlamp**: [Headlamp](https://headlamp.dev), the cluster's web UI, from its Helm chart, on a LoadBalancer
    address. Its own ServiceAccount gets no cluster role; it acts with the token you log in with.
  - **headlamp-access**: the `headlamp-admin` ServiceAccount you log in to Headlamp with.
  - **longhorn-backups**: nightly backups of every Longhorn volume, retaining 14 ([docs/longhorn-backups.md](docs/longhorn-backups.md)).
  - **longhorn**: [Longhorn](https://longhorn.io) replicated block storage on the agents' dedicated disks, as the
    default StorageClass `longhorn` (two replicas, volumes kept when a claim is deleted).
  - **sealed-secrets**: the controller for encrypted SealedSecret manifests ([docs/sealed-secrets.md](docs/sealed-secrets.md)).
- [`manifests/`](manifests/): plain manifests the Applications point at.
- [`bootstrap/`](bootstrap/): the root Application applied by hand.
- [`docs/`](docs/): setup, operations, security, and reference guides.
- [`scripts/`](scripts/) and [`tests/`](tests/): manifest policy checker and its tests.
- Root project files include the `Makefile`, dependency pins, and contribution/security policies.
- [`scripts/check_manifests.py`](scripts/check_manifests.py): the policy check CI runs on every change.

Planned: see the [roadmap](docs/roadmap.md).

## Getting started

You need a running k3s (or other Kubernetes) cluster with a LoadBalancer implementation, `kubectl` with an admin
kubeconfig, and `helm`. Install Argo CD using the version tracked by `apps/argocd.yaml`, then apply the root
Application:

```sh
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd --version 10.17.1 --namespace argocd --create-namespace \
  --set server.service.type=LoadBalancer --set dex.enabled=false
kubectl apply -f bootstrap/root.yaml
```

Argo CD then installs the Applications in `apps/`. Follow the [quick start](docs/quick-start.md) and
[installing guide](docs/installing.md) for the full process, including first login and changing the initial
password.

## Service access

- Argo CD is exposed by a `LoadBalancer` Service; discover its address from the `argocd-server` Service.
- Headlamp is exposed on port 80 by a `LoadBalancer` Service; discover its address from the `headlamp` Service.
- The *arr applications use Traefik Ingress paths without committed hostnames; see [Interfaces](docs/interfaces.md).
- Longhorn's UI remains `ClusterIP`; use port-forwarding or Headlamp to reach it.

The cluster supplies LoadBalancer addresses, DNS, identity-provider values, NFS backup targets, and other
site-specific settings during setup. They are intentionally not stored here; see [Installing](docs/installing.md)
and the relevant focused runbooks.

## Configuration

Chart values are inline in each Application. Site-specific values such as addresses, DNS names, identity-provider
configuration, and NFS targets are supplied by cluster setup and are not committed. See
[what the cluster provides](docs/installing.md#what-the-cluster-provides).

## Routine operations

- Check application sync and health in the Argo CD UI; the [Architecture](docs/architecture.md) guide explains
  the GitOps flow.
- Use [Upgrading](docs/upgrading.md) for updates and rollback.
- Follow [Security requirements](docs/security.md) for access and secret handling.
- Use [Longhorn backups](docs/longhorn-backups.md) to check and restore backups.
- Follow [The *arr apps](docs/arr.md) for shadow testing and cutover.

## Running it securely

- Reach the API, Argo CD and Headlamp only from a trusted network or VPN; nothing here is meant for the internet.
- Change Argo CD's initial admin password and delete `argocd-initial-admin-secret`.
- Make Headlamp tokens short-lived (`kubectl -n headlamp create token headlamp-admin --duration=8h`).
- Protect `main`: Argo CD deploys whatever is merged there.

More in [docs/security.md](docs/security.md).

## License

[MIT](LICENSE).
