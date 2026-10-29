# Assurance case

Why the [security requirements](security.md) are met: the threat model, the trust boundaries, the design
principles applied, and how common weaknesses are countered.

## Threat model

| Threat | Example | Countered by |
| --- | --- | --- |
| An unreviewed version reaches the cluster | a chart range resolves to a new major; a moving image tag | exact chart versions and image digests, enforced by the policy check; Argo CD applies only `main` |
| A malicious or careless change is merged | a manifest that runs privileged or grants cluster-admin | required CI checks, the policy's `no-privileged` rule, review of every pull request, the `main` ruleset |
| A secret or private detail is published | a token, kubeconfig or the LAN's addresses in a public file | `no-secret` and `public-safe` rules, gitleaks over the history, secret scanning with push protection, `.gitignore` |
| A compromised Action or tool in CI | a re-tagged Action exfiltrates the token | Actions pinned by commit SHA, tools by digest or hash, read-only default token, no secrets for forks |
| Someone on the network reaches the UIs | Headlamp or Argo CD on a LoadBalancer address | Argo CD's login; Headlamp needs a token; both on a trusted network only |
| A stolen Headlamp token | copied from a browser | tokens are short-lived and made on demand; none is stored |
| Drift made by hand | `kubectl edit` on a live object | Argo CD self-heal reverts it |

## Trust boundaries

1. **GitHub → the cluster.** Argo CD pulls this public repository over HTTPS; the cluster trusts whatever is on
   `main`. The boundary is held by the branch ruleset and CI.
2. **The network → the cluster's addresses.** The API, Argo CD and Headlamp trust their own logins; the network
   in front is trusted to be the owner's.
3. **The Headlamp pod → the API.** The pod's own ServiceAccount has no cluster role; requests carry the user's token.
4. **CI → the repository.** Workflows get a read-only token by default; only release and auto-merge jobs get more,
   and only for what they do.

## Secure design principles

- **Least privilege**: Headlamp's pod has no cluster role; CI jobs ask for permissions per job; the monitoring
  account is `view`-only.
- **Fail-safe defaults**: the policy refuses unpinned versions, Secrets and private details unless waived with a
  reason (and the last two can't be).
- **Economy of mechanism**: one root Application, plain manifests and inline chart values; no templating layer.
- **Complete mediation**: every change goes through a pull request and CI; nothing is applied by hand after the
  bootstrap.
- **Open design**: everything is public except the site's own details, which aren't needed to review it.
- **Separation of privilege**: merging needs the maintainer's account and passing checks; using the cluster needs
  separate credentials kept outside the repository.

## Common weaknesses

| Weakness (CWE) | How it's countered |
| --- | --- |
| CWE-798 hard-coded credentials | no Secrets allowed; gitleaks; push protection |
| CWE-200 exposure of sensitive information | `public-safe` rule; site details kept outside the repository |
| CWE-250 execution with unnecessary privileges | `no-privileged` rule; no cluster role for Headlamp's pod |
| CWE-494 download of code without integrity check | pinned charts, digests, hashed Python tools, SHA-pinned Actions, checksum-verified kubeconform |
| CWE-1104 use of unmaintained third-party components | dependency choice and review policy ([dependencies.md](dependencies.md)) |
| CWE-78 / script injection in workflows | untrusted event data only through `env:`; actionlint |

## Evidence

CI results on every pull request; CodeQL and Scorecard results in the repository's Security tab; the policy check's
unit tests (`tests/`); signed release checksums with SLSA provenance ([verifying-releases.md](verifying-releases.md)).
