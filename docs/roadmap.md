# Roadmap

What's planned for about the next year, and what homelab-kube will not do. Dates aren't promised.

## Now: the cluster's base

- [x] The root Application ("app of apps") and Headlamp, with a login account that holds no stored token
- [x] The policy check: pinned versions, no Secrets, nothing privileged, nothing site-specific
- [ ] First release (0.1.0)

## Next: storage and a first workload

- [x] Longhorn on the agents (replicated block storage) as the default StorageClass
- [x] A media volume over NFS, read-only for trial apps (applied by hand: it holds an address)
- [ ] A trial of media-management apps with copied settings and no downloads, to compare with the Compose stacks
- Encrypted secrets in git (Sealed Secrets or SOPS), so apps that need a secret can be declared here

## Later

- [x] Argo CD managing its own Helm release from this repository
- [x] Renovate, to propose Helm chart and image bumps (pull requests only)
- Single sign-on for Argo CD and Headlamp
- [x] Backups of Longhorn volumes off the cluster (nightly, keep 14)

## Security and project health

- Register with the OpenSSF Best Practices programme and reach Passing, then Silver; meet OpenSSF Baseline levels 1
  and 2
- Keep CI's policy check, schema validation, CodeQL and Scorecard green on every change
- Signed releases with SLSA provenance from the first release on

## What homelab-kube will not do

- Hold secrets in plain form, or any site-specific address, domain or host name
- Expose anything to the internet
- Become a general-purpose Kubernetes distribution or a Helm chart of its own
- Follow moving versions (`latest`, ranges, branches of other repositories)
