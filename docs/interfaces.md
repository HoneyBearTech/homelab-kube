# Interfaces

## Applications

| File | Application | Source | Version | Destination namespace |
| --- | --- | --- | --- | --- |
| `bootstrap/root.yaml` | root | this repository, `apps/` | `main` | argocd |
| `apps/headlamp.yaml` | headlamp | Helm `https://kubernetes-sigs.github.io/headlamp/`, chart `headlamp` | 0.46.0 | headlamp |
| `apps/headlamp-access.yaml` | headlamp-access | this repository, `manifests/headlamp-access/` | `main` | headlamp |
| `apps/media-trial.yaml` | media-trial | this repository, `manifests/media-trial/` | `main` | media-trial |
| `apps/longhorn.yaml` | longhorn | Helm `https://charts.longhorn.io`, chart `longhorn` | 1.13.0 | longhorn-system |

Every Application uses the `default` project, automated sync with `prune` and `selfHeal`, and `CreateNamespace=true`.

## Headlamp values

| Value | Setting | Why |
| --- | --- | --- |
| `clusterRoleBinding.create` | `false` | the pod's ServiceAccount gets no cluster role; Headlamp acts with the login token |
| `service.type` / `service.port` | `LoadBalancer` / `80` | its own address from the cluster's pool |
| `resources` | requests 50m CPU, 128 MiB; limit 512 MiB | small, predictable footprint |

## Longhorn values

| Value | Setting | Why |
| --- | --- | --- |
| `preUpgradeChecker.jobEnabled` | `false` | Longhorn's documented setting for Argo CD |
| `persistence.defaultClass` / `defaultClassReplicaCount` | `true` / `2` | the default StorageClass `longhorn`, two copies on different agents |
| `persistence.reclaimPolicy` | `Retain` | a pruned or deleted claim keeps its volume |
| `defaultSettings.defaultDataPath` | `/var/lib/longhorn` | each agent's dedicated disk |
| `defaultSettings.defaultReplicaCount` | `2` | the same for volumes made outside the StorageClass |
| `defaultSettings.replicaAutoBalance` | `best-effort` | spread replicas when an agent comes back |
| `defaultSettings.storageMinimalAvailablePercentage` | `25` | stop scheduling replicas on a disk under 25 % free |
| `longhornUI.replicas` / `service.ui.type` | `1` / `ClusterIP` | the UI has no login: not given an address |

The Application syncs with `ServerSideApply=true` (Longhorn's CRDs are too large for client-side apply).

## Objects

| Object | Purpose |
| --- | --- |
| PVC `media-trial/media` (ReadOnlyMany, `volumeName: media-nfs`) | the media library, read-only, for every trial app |
| PVC `media-trial/sonarr-config`, `radarr-config` (Longhorn, 10 GiB) | each app's `/config` |
| Deployments `sonarr`, `radarr` (0 replicas until loaded) | the apps; URL base from `SONARR__SERVER__URLBASE` / `RADARR__SERVER__URLBASE` |
| Ingress `sonarr`, `radarr` (class `traefik`, no host) | `/sonarr-k8s`, `/radarr-k8s` on Traefik's address |
| NetworkPolicy `trial-egress` | DNS in the cluster and the internet only; no private networks |
| ServiceAccount `headlamp/headlamp-admin` | Headlamp login; no token is mounted or stored |
| ClusterRoleBinding `headlamp-admin` → `cluster-admin` | what that login may do |

## Policy annotations

A manifest may waive one rule of `scripts/check_manifests.py` with `homelab-kube/allow-<rule>: "<reason>"` in its
`metadata.annotations`. Waivable: `pinned-chart`, `pinned-git`, `pinned-image`, `no-privileged`. Never waivable:
`no-secret`, `public-safe`.

## Commands

| Command | Does |
| --- | --- |
| `make lint` | ruff, ruff format, yamllint |
| `make test` | the checker's unit tests with the coverage floor |
| `make check` | the manifest policy; `PUBLIC_SAFE_DENY=<regex>` adds names to refuse |
| `make validate` | kubeconform against the Kubernetes and Argo CD schemas |
| `python scripts/check_manifests.py [dir] --sbom FILE` | the policy, writing a CycloneDX SBOM of the charts |
| `kubectl -n headlamp create token headlamp-admin --duration=8h` | a Headlamp login token |
