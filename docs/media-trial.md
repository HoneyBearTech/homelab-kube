# The media trial

Sonarr and Radarr run on the cluster beside the Compose stack that stays live, with copies of its configs, to see
how the apps behave on Kubernetes: storage, restarts, a node going away. The trial must never grab, download,
import or notify anything, and never write to the library.

## What keeps it harmless

| Guard | Where |
| --- | --- |
| The media is read-only: the NFS export, the mount options, the volume and the container mount | the `media-nfs` volume (applied by hand) and `manifests/media-trial/*.yaml` |
| No traffic to any private network: download clients, indexer proxies and media servers are unreachable | [`network-policy.yaml`](../manifests/media-trial/network-policy.yaml) |
| Downloads, RSS sync, automatic search and connections are switched off in each app before it's used | the checklist below |
| The apps start at 0 replicas, so nothing runs until its config is in place | `replicas: 0` in each Deployment |

## The media volume

The claim `media-trial/media` binds to the PersistentVolume `media-nfs`, which isn't in this repository because it
holds the NFS server's address. The cluster's owner applies it once with an admin kubeconfig: a read-only NFS
volume with `persistentVolumeReclaimPolicy: Retain`, `storageClassName: ""`, access mode `ReadOnlyMany` and a
`claimRef` to `media-trial/media`. Every app in the namespace mounts that one claim at `/media`, the same path
as in the Compose stack, so the root folders in the copied databases match.

## Copying a config in

For each app (`sonarr`, `radarr`), with its Deployment still at 0 replicas.

**1. On the Compose host**, after that night's backup, stop the app so its SQLite database is consistent, archive
its config without logs and backups, and start it again:

```sh
cd ~/homelab-<stack> && docker compose stop sonarr
sudo du -sh "$CONFIG_ROOT/sonarr/config"            # must fit the 10 GiB claim
sudo tar -C "$CONFIG_ROOT/sonarr" --exclude=config/logs --exclude=config/Backups --exclude='config/*.pid' \
  -czf ~/sonarr-config.tgz config && sudo chown "$USER" ~/sonarr-config.tgz
docker compose start sonarr
```

**2. On your workstation**, copy the archive over, then load it into the app's Longhorn volume through a
throwaway pod (the app's own image, so nothing new is pulled; it only sleeps):

```sh
scp <compose-host>:sonarr-config.tgz ~/
IMAGE=$(kubectl -n media-trial get deploy sonarr -o jsonpath='{.spec.template.spec.containers[0].image}')
kubectl -n media-trial run sonarr-loader --image="$IMAGE" --restart=Never --overrides="$(printf '{"spec":{"containers":[{"name":"loader","image":"%s","command":["sleep","3600"],"volumeMounts":[{"name":"config","mountPath":"/config"}]}],"volumes":[{"name":"config","persistentVolumeClaim":{"claimName":"sonarr-config"}}]}}' "$IMAGE")"
kubectl -n media-trial wait --for=condition=Ready pod/sonarr-loader --timeout=180s
kubectl -n media-trial cp ~/sonarr-config.tgz sonarr-loader:/tmp/config.tgz
kubectl -n media-trial exec sonarr-loader -- sh -c \
  'tar -xzf /tmp/config.tgz -C /config --strip-components=1 && chown -R 1000:1000 /config && ls -la /config'
kubectl -n media-trial delete pod sonarr-loader
rm ~/sonarr-config.tgz
```

The archive holds the app's API key and sign-in settings: delete it from both machines when it's loaded.

**3. Start it** by pull request: `replicas: 1` in `manifests/media-trial/<app>.yaml`. Argo CD starts the pod; the
first start can take a few minutes while the app checks its database.

## Before using it: the checklist

Open `http://<Traefik's address>/sonarr-k8s` (or `/radarr-k8s`) and sign in with the copied login. Then, in this
order:

1. **Settings → Download Clients**: disable every client (untick *Enable*).
2. **Settings → Indexers**: untick *Enable RSS*, *Enable Automatic Search* and *Enable Interactive Search* on each.
3. **Settings → Connect**: disable every connection (media servers, notifications, scripts).
4. **Settings → Import Lists**: disable every list, so nothing new is added and searched.
5. **Settings → General**: check that *URL Base* shows `/sonarr-k8s` (it comes from the environment).

The network policy already blocks the private network, so a step missed here fails rather than acts; the
checklist makes sure it never tries. The app will warn that its root folders aren't writable: that's expected.

## Ending the trial

Remove `apps/media-trial.yaml` by pull request. Argo CD removes the apps; the three claims stay (they're never
deleted by a sync) and their Longhorn volumes are kept (`Retain`), until they're deleted on purpose.
