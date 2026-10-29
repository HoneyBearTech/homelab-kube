# Quick start

From a running k3s cluster to Argo CD and Headlamp. The cluster and what it needs first are described in
[installing.md](installing.md#what-the-cluster-provides); this page assumes they're in place.

## 1. Install Argo CD

With an admin kubeconfig and `helm`:

```sh
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update argo
helm install argocd argo/argo-cd --version 10.11.6 --namespace argocd --create-namespace \
  --set server.service.type=LoadBalancer --set dex.enabled=false
kubectl -n argocd rollout status deploy/argocd-server
kubectl -n argocd get svc argocd-server   # EXTERNAL-IP is Argo CD's address
```

## 2. Log in and change the password

```sh
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
```

Open `https://<EXTERNAL-IP>` (the certificate is self-signed until you put a proxy in front), log in as `admin`
with that password, and change it under **User Info → Update Password**. Then delete the initial secret:

```sh
kubectl -n argocd delete secret argocd-initial-admin-secret
```

## 3. Apply the root Application

```sh
kubectl apply -f bootstrap/root.yaml
```

In the Argo CD UI, `root` appears, then `headlamp` and `headlamp-access`. All three should turn **Synced** and
**Healthy** within a few minutes.

## 4. Open Headlamp

```sh
kubectl -n headlamp get svc headlamp                                   # EXTERNAL-IP is Headlamp's address
kubectl -n headlamp create token headlamp-admin --duration=8h          # the login token
```

Open `http://<EXTERNAL-IP>` and paste the token. When it expires, make a new one.

From now on, change the cluster by pull request: a merge to `main` is synced by Argo CD.
