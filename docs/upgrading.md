# Upgrading

Every change reaches the cluster the same way: a pull request to `main`, CI, a merge, then Argo CD syncs it
(automatically, within about three minutes, or at once with **Refresh** in the UI).

## Bumping a chart

Renovate opens a pull request for each new chart version (and image digest); nothing merges by itself. For each:

1. Read the chart's release notes and the app's: look for changed values, CRD changes and data migrations.
2. Check the PR's change to `targetRevision`, and adjust `valuesObject` in the same PR if the chart needs it.
3. Open a pull request linking the release notes; CI checks the pin and the schemas.
4. After the merge, watch the Application turn **Synced** and **Healthy** in Argo CD.

## Upgrading Argo CD

Argo CD is installed with Helm (installing.md#argo-cd). Read the chart's upgrade notes first, then:

```sh
helm repo update argo
helm upgrade argocd argo/argo-cd --version <new> --namespace argocd --reuse-values
```

## Upgrading k3s

Upgrade one node at a time, servers first, to the same version everywhere; keep at least two servers up so etcd
keeps its quorum. k3s' own upgrade guide applies; the version is recorded with the cluster's notes, not here.

## Rolling back

Revert the pull request. Argo CD syncs `main` back to the previous state. A chart that migrated data one way
may need its own restore; its release notes say so.
