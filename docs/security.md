# Security requirements

What homelab-kube protects, what it doesn't, and where secrets live. The reasoning behind these is in the
[assurance case](assurance-case.md).

## What homelab-kube protects

- **The cluster only runs what was reviewed.** Every chart is pinned to an exact version and every image by
  digest; Argo CD applies only what is merged to `main`, after CI.
- **The repository leaks nothing.** No Secrets, tokens, kubeconfigs, private addresses or internal names are
  committed; CI enforces it.
- **Least privilege where it's ours to choose.** Headlamp's own pod gets no cluster role; Headlamp acts with the
  token the user logs in with. No manifest runs privileged or on the host network without a written reason.
- **Manual drift doesn't last.** Self-heal reverts changes made outside git; pruning removes what was deleted.

## Policy

`scripts/check_manifests.py` runs in CI on every change and in the release workflow:

| Rule | Requires | Waivable |
| --- | --- | --- |
| `pinned-chart` | an exact chart version | with a reason |
| `pinned-git` | this repository at `main`, any other at a full commit SHA | with a reason |
| `pinned-image` | `name:tag@sha256:<digest>` in plain manifests | with a reason |
| `no-privileged` | no privileged container, host network, PID or IPC | with a reason |
| `no-secret` | no `Secret` objects | never |
| `public-safe` | no private IPv4 addresses, `.lan` / `.internal` / `.home.arpa` names, or names matching the `PUBLIC_SAFE_DENY` secret, in any committed text file | never |

## What it doesn't protect

- **The cluster's admins.** Whoever has an admin kubeconfig, Argo CD's `admin` login or a `headlamp-admin`
  token controls the cluster.
- **A malicious merge.** Argo CD runs with cluster-admin and deploys what `main` says; protecting `main` (branch
  ruleset, required checks, review) is what stands in the way.
- **The apps themselves.** Vulnerabilities in k3s, Argo CD, Headlamp or other charts belong to those projects
  ([dependencies.md](dependencies.md)).
- **The network.** Nothing here adds TLS or authentication in front of the LoadBalancer addresses; keep them on a
  trusted network.
- **Images inside charts** are pinned by the chart version, not by a digest homelab-kube reviews.

## Where secrets live

| Secret | Where | Never |
| --- | --- | --- |
| k3s cluster join token | the owner's password manager; the nodes' `/etc/rancher/k3s/config.yaml` (0600) | in git, chat or logs |
| Admin kubeconfig | the owner's machine (0600) and the servers | in git |
| Argo CD `admin` password | Argo CD (bcrypt) and the owner's password manager | in git |
| Headlamp tokens | made on demand, short-lived | stored anywhere |
| Read-only monitoring token | its own kubeconfig (0600) | in git |
