# Interfaces

## Applications

| File | Application | Source | Version | Destination namespace |
| --- | --- | --- | --- | --- |
| `bootstrap/root.yaml` | root | this repository, `apps/` | `main` | argocd |
| `apps/headlamp.yaml` | headlamp | Helm `https://kubernetes-sigs.github.io/headlamp/`, chart `headlamp` | 0.46.0 | headlamp |
| `apps/headlamp-access.yaml` | headlamp-access | this repository, `manifests/headlamp-access/` | `main` | headlamp |
| `apps/argocd.yaml` | argocd | Helm `https://argoproj.github.io/argo-helm`, chart `argo-cd` (release `argocd`) | 10.17.1 | argocd |
| `apps/arr.yaml` | arr | this repository, `manifests/arr/` | `main` | arr |
| `apps/longhorn-backups.yaml` | longhorn-backups | this repository, `manifests/longhorn-backups/` | `main` | longhorn-system |
| `apps/sealed-secrets.yaml` | sealed-secrets | Helm `https://bitnami.github.io/sealed-secrets`, chart `sealed-secrets` (release `sealed-secrets-controller`) | 2.22.0 | kube-system |
| `apps/longhorn.yaml` | longhorn | Helm `https://charts.longhorn.io`, chart `longhorn` | 1.13.0 | longhorn-system |

Every Application uses the `default` project, automated sync with `prune` and `selfHeal`, and `CreateNamespace=true`.

## Headlamp values

| Value | Setting | Why |
| --- | --- | --- |
| `clusterRoleBinding.create` | `false` | the pod's ServiceAccount gets no cluster role; Headlamp acts with the login token |
| `service.type` / `service.port` | `LoadBalancer` / `80` | its own address from the cluster's pool |
| `resources` | requests 50m CPU, 128 MiB; limit 512 MiB | small, predictable footprint |
| `config.oidc.externalSecret` | `headlamp-oidc`, with scopes | single sign-on settings from a sealed Secret ([sso.md](sso.md)) |
| `config.oidc.callbackURL` | `$(OIDC_CALLBACK_URL)` | turns the callback flag on; the value comes from that Secret |

## Argo CD values

| Value | Setting | Why |
| --- | --- | --- |
| `server.service.type` | `LoadBalancer` | its own address from the cluster's pool |
| `dex.enabled` | `false` | sign-on goes straight to the OIDC provider |
| `configs.rbac.scopes` / `policy.default` | `[email]` / `""` | SSO users are matched by email; anyone unlisted gets nothing |
| `ignoreDifferences` | `argocd-cm` `url`, `oidc.config`; `argocd-rbac-cm` `policy.csv` | set by hand ([sso.md](sso.md)); not reverted |

## Sealed Secrets values

| Value | Setting | Why |
| --- | --- | --- |
| `fullnameOverride` / namespace | `sealed-secrets-controller` / `kube-system` | `kubeseal`'s defaults: no flags needed |
| `keyrenewperiod` | `"0"` | one key, never renewed: one backup restores every SealedSecret ([sealed-secrets.md](sealed-secrets.md)) |
| `resources` | requests 10m CPU, 32 MiB; limit 128 MiB | small, predictable footprint |

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
| `defaultSettings.nodeDownPodDeletionPolicy` | `delete-both-statefulset-and-deployment-pod` | a pod stuck on a failed agent is deleted, so its volume moves with the replacement pod |
| `longhornUI.replicas` / `service.ui.type` | `1` / `ClusterIP` | the UI has no login: not given an address |

The Application syncs with `ServerSideApply=true` (Longhorn's CRDs are too large for client-side apply).

## Objects

| Object | Purpose |
| --- | --- |
| Deployments `sonarr`, `radarr`, `lidarr`, `bazarr`, `sonarr4k`, `radarr4k`, `bazarr4k` (0 replicas until loaded) | *arr apps; see [arr.md](arr.md) for configuration and cutover |
| Ingresses for those apps (class `traefik`, no host) | `/sonarr-k8s`, `/radarr-k8s`, `/lidarr-k8s`, `/bazarr-k8s`, `/sonarr4k-k8s`, `/radarr4k-k8s`, `/bazarr4k-k8s` on Traefik |
| NetworkPolicy `arr-egress` | egress controls for *arr workloads; see [arr.md](arr.md#modes) |
| ServiceAccount `headlamp/headlamp-admin` | Headlamp login; no token is mounted or stored |
| ClusterRoleBinding `headlamp-admin` → `cluster-admin` | what that login may do |

## Environment variable names

The Argus agent's DaemonSet uses `ARGUS_HOST` and `ARGUS_NODE_IP`; its Secret supplies
`ARGUS_PROMETHEUS_URL`, `ARGUS_LOKI_URL`, and `ARGUS_PROMETHEUS_PASSWORD`. These values are cluster-specific and
secret-backed. See [Argus agent](argus-agent.md) for setup and semantics.

The *arr manifests use `PUID`, `PGID`, `TZ`, and `UMASK`, plus app-specific URL-base variables where configured:
`SONARR__SERVER__URLBASE`, `RADARR__SERVER__URLBASE`, and `LIDARR__SERVER__URLBASE`. See [The *arr apps](arr.md)
for their meaning and how app configuration is loaded. Headlamp's OIDC callback is supplied through the
Secret-backed `OIDC_CALLBACK_URL`; see [Single sign-on](sso.md).

## Labels

| Label | On | Values |
| --- | --- | --- |
| `homelab-kube/mode` | the pods in `arr` | `shadow` or `live`; selects the network policies applied by hand ([arr.md](arr.md#modes)) |

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
