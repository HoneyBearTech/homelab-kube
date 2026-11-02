# The *arr apps

Radarr, Radarr 4K, Sonarr, Sonarr 4K, Lidarr, Bazarr and Bazarr 4K run on the cluster beside the Docker Compose
host that runs them today. Each starts as a read-only **shadow**, then moves **live** one app at a time while the
Compose host's copy is stopped. The download client stays on the Compose host until the last move.

## The rule

An app is live in exactly one place. Two instances never share one app's databases, and never both grab, import or
rename in the media library: they would download the same releases twice and fight over the same files.

## Modes

Each Deployment's pod template carries the label `homelab-kube/mode`.

| | `shadow` | `live` |
| --- | --- | --- |
| Database | its own copy of the app's databases | the production databases |
| Media | read-only (`media-ro`) | read-write (`media-rw`, added with the first live app) |
| Network | DNS, the internet, its database server | also the download clients, the indexer proxy and the media servers |
| Downloads, RSS, searches, connections, import lists | off | on |
| The Compose host's copy | live | stopped |

## The media volumes

The library is one NFS export, mounted at `/media` as on the Compose host, so root folders in the databases match
and imports still hardlink. The PersistentVolumes hold the NFS server's address, so the cluster's owner applies them
by hand, each with `persistentVolumeReclaimPolicy: Retain`, `storageClassName: ""` and a `claimRef`:

- `arr-media-ro`: `ReadOnlyMany`, read-only mount, for `arr/media-ro`
- `arr-media-rw`: `ReadWriteMany`, for `arr/media-rw` (from the first live app on); the export must allow the
  agents read-write, with the same user mapping as the Compose host's mount

## Network

`network-policy.yaml` allows DNS and the internet and refuses every private range. Policies applied by hand add
the addresses, selected by the mode label:

- every pod in `arr`: the database server's PostgreSQL port
- `homelab-kube/mode: live`: the download clients, the indexer proxy and the media servers

## Databases

The apps' databases are on a PostgreSQL server, not in the config volume; only `config.xml` (Bazarr:
`config/config.yaml`) is there, holding the connection. A shadow points at its own copy, named
`<app>_k8s_main` and `<app>_k8s_log`, (Bazarr: one, `<app>_k8s`) made from the production databases with `pg_dump` and `pg_restore` (the
production app keeps running). A live app points at the production databases.

The image digests here match the Compose host's. While an app could still move back, update it there first: a newer
version may migrate the shared database, and an older copy can't open it again.

## Loading a config

With the Deployment at 0 replicas (as committed), copy the app's config folder from the Compose host without
`logs`, `Backups`, the old SQLite files and, if you like, `MediaCover`. Edit the copy:

1. Database: for a shadow, `<app>_k8s_main` / `<app>_k8s_log` (`PostgresMainDb`, `PostgresLogDb`); Bazarr has one,
   `<app>_k8s` (`postgresql.database`).
2. URL base: `/<app>-k8s` is set from the environment for Radarr, Sonarr and Lidarr. Bazarr: set
   `general.base_url` to `/bazarr-k8s` (or `/bazarr4k-k8s`) in `config.yaml`.

Then load it into `<app>-config` through a throwaway pod and start the app by pull request (`replicas: 1`), as in
[media-trial.md](media-trial.md#copying-a-config-in), with namespace `arr`. The archive holds the app's API key and
database password: delete it from every machine once it's loaded.

## A shadow's checklist

Before using it, in its web UI: disable every download client; untick RSS, automatic and interactive search on
every indexer; disable every connection and import list. Bazarr: disable every subtitle provider and point its
Sonarr and Radarr at the shadow copies in this namespace (`sonarr:8989`, `radarr:7878`, with their URL bases). The
network policy and the read-only media already make a missed step fail rather than act.

## Going live (one app)

1. Stop the Compose host's copy by pull request in that stack's repository (so nothing restarts it).
2. Scale the app here to 0; point `config.xml` at the production databases; set `homelab-kube/mode: live` and the
   `media-rw` claim by pull request; scale to 1.
3. Re-enable its download clients, indexers, connections and lists; point its clients (indexer proxy, reverse proxy,
   monitoring, Bazarr) at the cluster.
4. Check: a search grabs, the download client downloads, the app imports with a hardlink, the media server sees it.

**Rolling back:** scale the app here to 0, revert the pull request that stopped the Compose host's copy, and point
its clients back. Both copies use the same databases, so nothing is lost.
