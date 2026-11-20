# Plan: renovate-automerge

## What Sean asked for

"Ensure that all my repos that have renovate allow the renovate PRs to auto
merge", on the homelab-atlas model: every update, majors included, merges once
all checks pass, after a 3-day wait.

## What we found

- Renovate's config sets `automerge: false`.
- No check exercises the cluster itself: CI checks the manifests, not a running
  cluster.
- Does a merge deploy? Yes, at once: Argo CD syncs `main` within minutes.

## What we'll change

1. `renovate.json`: turn on auto-merge for every update, majors included, the
   way homelab-atlas does it: `automerge: true`, squash merges,
   `platformAutomerge: true` (GitHub merges as soon as the required checks
   pass); new versions wait 3 days before they are proposed
   (`minimumReleaseAge`, with `timestamp-optional` so a registry without release
   dates doesn't hold an update forever); security fixes and image rebuilds
   (digest updates) skip the wait. Check: Renovate's config validator passes,
   and a local Renovate dry run shows auto-merge on for ordinary updates and off
   for the exceptions below.
2. Docs that say updates are merged by hand, or by Dependabot: GOVERNANCE.md,
   docs/dependencies.md, docs/upgrading.md. Say instead that Renovate merges
   updates once every check passes, and name the exceptions.
3. Record the job in `docs/` (pass map, decisions log, roadmap; created if
   missing).

## Kept manual

- Longhorn stays manual (it must move one minor version at a time).
- Argo CD stays manual (its upgrade notes need reading first).

Each exception is an earlier decision by the owner; to drop one, say so on this
pull request.

## Who's on it

Engineer, Security Officer, Auditor.

## Risks

- The riskiest repo for this: a merged update reaches the cluster within
  minutes, and CI can't run it first. Keeping Longhorn and Argo CD manual covers
  the two with known upgrade traps.
- Renovate's schedule is unchanged, so updates still arrive once a week.

## Out of scope

Repository settings and branch rules (only the owner changes those), and the
workflows under `.github/workflows` (a leftover Dependabot auto-merge workflow
stays as it is).

