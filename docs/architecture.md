# Architecture

## The cluster

A small k3s cluster: three servers (control plane and embedded etcd, tainted so apps don't run there) and three
agents that run the apps. An API address that moves between servers (kube-vip) keeps `kubectl` and the agents
working when a server is down; the same tool hands out LoadBalancer addresses from a pool. Details of a particular
cluster (addresses, names, sizes) are kept by its owner, never in this repository.

## What runs from this repository

```
bootstrap/root.yaml ──► Application "root" ──► apps/*.yaml
                                                 ├─ headlamp         Helm chart (kubernetes-sigs/headlamp)
                                                 ├─ headlamp-access  manifests/headlamp-access/
                                                 ├─ longhorn         Helm chart (longhorn/longhorn)
                                                 └─ media-trial      manifests/media-trial/
```

| Application | Namespace | What | Reached at |
| --- | --- | --- | --- |
| root | argocd | syncs `apps/` | — |
| headlamp | headlamp | the web UI | LoadBalancer address, port 80 |
| headlamp-access | headlamp | the `headlamp-admin` login account | — |
| media-trial | media-trial | Sonarr and Radarr on copied configs, read-only media ([media-trial.md](media-trial.md)) | Traefik: `/sonarr-k8s`, `/radarr-k8s` |
| longhorn | longhorn-system | replicated block storage, StorageClass `longhorn` (default) | UI: ClusterIP only |

Argo CD itself is installed by Helm, outside this repository ([installing.md](installing.md#argo-cd)).

## Actors

- **The owner** merges pull requests, installs Argo CD, logs in to Argo CD and Headlamp.
- **Argo CD** reads this public repository over HTTPS (no credential) and applies it with its own cluster-admin
  ServiceAccount.
- **Headlamp** proxies the user's requests to the API with the token the user logged in with.
- **Dependabot and CI** propose and check changes; they never reach the cluster.

## How a change reaches the cluster

Pull request → CI (policy, schemas, lint, tests, secret scan) → squash-merge to `main` → Argo CD notices the new
commit (polling, about every three minutes) → sync, pruning removed objects → the Application reports
**Synced/Healthy**. A revert pull request rolls back the same way.

## Planned

- Argo CD managing its own Helm release from this repository.
