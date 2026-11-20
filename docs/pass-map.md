# Pass map

A short record of each piece of work on homelab-kube: what shipped, or what a
review found, and where to look. Newest first. The reasons behind the choices
are in the [decisions log](decisions-log.md).

## 2026-11-20: `renovate-automerge`

Renovate merges its pull requests itself once every check passes, majors
included; new versions wait 3 days, security fixes and image rebuilds don't.
Longhorn and Argo CD stay manual (their own pull requests). `platformAutomerge`
is true. (#50)
