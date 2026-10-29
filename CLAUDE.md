# homelab-kube Guidelines

Kubernetes manifests for the homelab k3s cluster, applied by Argo CD from `main` (app of apps: `bootstrap/root.yaml` → `apps/`). Public repository. Default branch: `main`.

> **STRICT**: AI anonymity required. No AI attribution or mention of AI assistance in committed files, PRs, git history, or docs.

## Public Safety & Architectural Hard Rules
- **Public Repo Invariants**: Zero internal hostnames, domains, IPs, LAN paths, secrets, kubeconfigs or personal emails in code, docs, tests, or commits. Cluster facts belong in Chronos notes. `scripts/check_manifests.py` refuses private addresses and internal names; CI adds the owner's names from the `PUBLIC_SAFE_DENY` secret.
- **Pinning**: Helm charts at an exact version; this repo at `main`; other git sources at a full commit SHA; images as `name:tag@sha256:<digest>`.
- **No Secrets in git**: no `Secret` objects, ever (not waivable). Secrets are created in the cluster.
- **Hardening**: no privileged containers, host network, PID or IPC without a `homelab-kube/allow-<rule>` annotation with a reason and owner approval.

## Notes & State Tracking
- Read `~/Chronos/Projects/homelab-kube/` before structural changes: `homelab-kube-roadmap.md`, `homelab-kube-Pass-Map.md`, `homelab-kube-Architecture.md`, `homelab-kube-Security-Considerations.md`, `homelab-kube-Decisions-Log.md`. The cluster build itself is in `~/Chronos/Projects/homelab-ops/homelab-ops-Kubernetes-Plan.md`.
- Update Chronos files as work lands. Notes **never** enter this code repo; `.obsidian-docs/` stays gitignored.

## Deploys & Merging
- **Auto-deploy on merge**: Argo CD syncs `main` automatically (prune + self-heal). Rollback via revert PR.
- **Cluster access**: read-only only, with `~/.kube/homelab-readonly` (`view` + nodes/storage). No writes to the cluster outside a merged PR; the owner runs anything that needs the admin kubeconfig.
- **Commits & PRs**: DCO signed-off (`git commit -s`), email `31805425+HoneyBearTech@users.noreply.github.com`.
- Required CI check names: `CI / Checks + tests`, `DCO / DCO sign-off`.

## Stack
- Manifests: Argo CD `Application` objects (Helm charts with inline `valuesObject`) and plain YAML.
- Tooling: Python 3.14 (`scripts/check_manifests.py`, PyYAML), pytest + coverage, ruff, yamllint, kubeconform (CI).

## Core Commands

```sh
make lint       # ruff check, ruff format --check, yamllint --strict
make test       # checker unit tests + coverage floor (offline)
make check      # manifest policy over the repo (PUBLIC_SAFE_DENY=<regex> to add names)
make validate   # kubeconform against Kubernetes + Argo CD schemas (needs kubeconform, network)
```
