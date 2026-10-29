# Interfaces

## Applications

| File | Application | Source | Version | Destination namespace |
| --- | --- | --- | --- | --- |
| `bootstrap/root.yaml` | root | this repository, `apps/` | `main` | argocd |
| `apps/headlamp.yaml` | headlamp | Helm `https://kubernetes-sigs.github.io/headlamp/`, chart `headlamp` | 0.46.0 | headlamp |
| `apps/headlamp-access.yaml` | headlamp-access | this repository, `manifests/headlamp-access/` | `main` | headlamp |

Every Application uses the `default` project, automated sync with `prune` and `selfHeal`, and `CreateNamespace=true`.

## Headlamp values

| Value | Setting | Why |
| --- | --- | --- |
| `clusterRoleBinding.create` | `false` | the pod's ServiceAccount gets no cluster role; Headlamp acts with the login token |
| `service.type` / `service.port` | `LoadBalancer` / `80` | its own address from the cluster's pool |
| `resources` | requests 50m CPU, 128 MiB; limit 512 MiB | small, predictable footprint |

## Objects

| Object | Purpose |
| --- | --- |
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
