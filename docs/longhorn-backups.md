# Longhorn backups

Longhorn keeps two copies of every volume inside the cluster (on two agents). Backups add a copy outside it: every
volume is backed up nightly to an NFS share, keeping the last 14.

## What's in this repository

[`manifests/longhorn-backups/nightly.yaml`](../manifests/longhorn-backups/nightly.yaml), synced by the
`longhorn-backups` Application: a Longhorn `RecurringJob` that backs up every volume in the `default` group at
10:30 UTC, keeping 14 backups per volume, one volume at a time. Backups are incremental.

## What the cluster provides (set by hand)

The backup target, because its URL holds the NFS server's address. On a server, with the admin kubeconfig:

```sh
kubectl -n longhorn-system patch backuptargets.longhorn.io default --type merge \
  -p '{"spec":{"backupTargetURL":"nfs://<nfs-server>:/<export>","pollInterval":"5m0s"}}'
```

The export must allow the agents' addresses read-write, with root not squashed (Longhorn writes as root). Longhorn
mounts it from the agents. Neither the chart's values nor this repository set a backup target, so Argo CD leaves
it alone.

## Checking and restoring

- The Longhorn UI (`kubectl -n longhorn-system port-forward svc/longhorn-frontend 8000:80`) shows the target under
  **Settings → Backup Target** (it should be *Available*) and every backup under **Backup**.
- `kubectl -n longhorn-system get backupvolumes,backups` lists them from the command line.
- To restore, create a new volume from a backup in the UI (**Backup → ⋮ → Restore**), then point the app's claim at
  it. A restore never overwrites the running volume.
