# Installing

## What the cluster provides

homelab-kube commits nothing site-specific, so a cluster provides these itself, outside this repository:

| What | Why | How the maintainer's cluster does it |
| --- | --- | --- |
| Kubernetes | runs everything | k3s, three servers on embedded etcd and three agents |
| A highly available API address | `kubectl` and nodes keep working when a server is down | kube-vip (ARP), as a DaemonSet on the servers |
| A LoadBalancer implementation and an address pool | Argo CD, Headlamp and Traefik get addresses | kube-vip's cloud provider, with the pool in the `kube-system/kubevip` ConfigMap |
| An ingress controller | (Planned) routes to apps | k3s' bundled Traefik |
| A dedicated disk on every agent, mounted at `/var/lib/longhorn`, plus `open-iscsi` (with `iscsid` running) and `nfs-common` | Longhorn's volumes | a 100 GB ext4 disk labelled `longhorn`; multipathd told to ignore `sd*` devices |
| DNS names, a reverse proxy, TLS | friendly names and certificates | outside the cluster |

The servers are tainted `CriticalAddonsOnly=true:NoExecute`, so apps (and Longhorn's replicas) run on the agents only.

k3s also installs its `local-path` StorageClass and marks it default. With two defaults, Kubernetes uses the newest
(`longhorn`) for a claim that names none; the apps here always name `storageClassName: longhorn`. To have one
default only, add `local-storage` to `disable:` in each server's k3s config.

Keep these settings with the cluster's own notes, never in this repository: the policy check and CI refuse
private addresses and internal names (`scripts/check_manifests.py`).

## Argo CD

Argo CD itself is installed with Helm, once, by the cluster's owner ([quick start](quick-start.md#1-install-argo-cd)).
It isn't (yet) managed from this repository, so it can't remove itself with a bad merge. Settings used:

| Value | Setting | Why |
| --- | --- | --- |
| `server.service.type` | `LoadBalancer` | the UI and API on their own address |
| `dex.enabled` | `false` | no single sign-on yet: the local `admin` account only |

## The root Application

`kubectl apply -f bootstrap/root.yaml` creates `root`, which syncs every Application in `apps/` from `main`, with
automated sync, pruning and self-heal. It's the only manifest applied by hand.

A private fork needs Argo CD to have read access: add the repository under **Settings → Repositories** with a
read-only deploy key, and point `repoURL` in `bootstrap/root.yaml` and `apps/` at the fork.

## Running it securely

- Keep the API, Argo CD and Headlamp reachable only from a trusted network or VPN.
- Change Argo CD's initial admin password and delete `argocd-initial-admin-secret` (quick start, step 2).
- Use short-lived Headlamp tokens; never create a long-lived token Secret for `headlamp-admin`.
- Give monitoring and automation their own ServiceAccount bound to the built-in `view` role, not an admin
  kubeconfig.
- Protect `main` with a branch ruleset (pull request, required checks, no force-push): Argo CD deploys what's there.

More in [security.md](security.md).

## Uninstalling

```sh
kubectl -n argocd delete application root   # with pruning, Argo CD removes the Applications it created
helm uninstall argocd --namespace argocd
kubectl delete namespace argocd headlamp
```

If an Application hangs on deletion, its finalizer is waiting for resources to go; check
`kubectl -n argocd describe application <name>`.
