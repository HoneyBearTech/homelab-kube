# Single sign-on

Argo CD and Headlamp sign users in with an OpenID Connect provider (written for Google; any OIDC provider works the
same way). The cluster's API trusts the same provider, so Headlamp acts with the signed-in user's own identity and
Kubernetes RBAC decides what they may do. Token logins and Argo CD's `admin` keep working as a fallback.

## What's in this repository

- `apps/argocd.yaml`: RBAC matches users by their `email` claim, and anyone not listed in `policy.csv` gets no
  access (`policy.default: ""`). The SSO fields set by hand (below) are listed in `ignoreDifferences`, so Argo CD
  neither reports them as drift nor reverts them.
- `apps/headlamp.yaml`: Headlamp reads its OIDC settings from the Secret `headlamp/headlamp-oidc`.

Nothing here holds a client ID, client secret, domain or email.

## What the cluster provides (set by hand)

Create one OAuth client of type *web application* at the provider, with these redirect URIs:

- `https://<argocd-host>/auth/callback`
- `https://<headlamp-host>/oidc-callback`

Then, in this order:

1. **The API server trusts the provider.** On every server, one at a time, add
   `/etc/rancher/k3s/config.yaml.d/50-oidc.yaml` and restart k3s; wait for the node to be `Ready` before the next:

   ```yaml
   kube-apiserver-arg:
     - "oidc-issuer-url=https://accounts.google.com"
     - "oidc-client-id=<client-id>"
     - "oidc-username-claim=email"
   ```

2. **Users get Kubernetes roles.** A ClusterRoleBinding (or RoleBindings) for each user, by email:

   ```sh
   kubectl create clusterrolebinding sso-<name> --clusterrole=cluster-admin --user=<email>
   ```

3. **Headlamp's Secret**, before Headlamp's pod restarts with these values (it won't start without it):

   ```sh
   kubectl -n headlamp create secret generic headlamp-oidc \
     --from-literal=OIDC_CLIENT_ID=<client-id> --from-literal=OIDC_CLIENT_SECRET=<client-secret> \
     --from-literal=OIDC_ISSUER_URL=https://accounts.google.com --from-literal=OIDC_SCOPES=openid,email,profile \
     --from-literal=OIDC_CALLBACK_URL=https://<headlamp-host>/oidc-callback
   ```

4. **Argo CD**, after these values have synced:

   ```sh
   kubectl -n argocd patch secret argocd-secret --type merge \
     -p '{"stringData":{"oidc.google.clientSecret":"<client-secret>"}}'
   kubectl -n argocd patch configmap argocd-cm --type merge -p '{"data":{
     "url":"https://<argocd-host>",
     "oidc.config":"name: Google\nissuer: https://accounts.google.com\nclientID: <client-id>\nclientSecret: $oidc.google.clientSecret\nrequestedScopes: [openid, profile, email]\n"}}'
   kubectl -n argocd patch configmap argocd-rbac-cm --type merge \
     -p '{"data":{"policy.csv":"g, <email>, role:admin\n"}}'
   ```

## Checking

- Argo CD's login page shows **Log in via Google**; after signing in, **User Info** shows the email.
- Headlamp's login page offers **Sign In**; after signing in, the cluster's resources are listed. A user with no
  role binding signs in but is refused everything.
- `kubectl auth can-i --list --as=<email>` shows what a user may do.

## Limits

- The provider's ID tokens last an hour; Headlamp asks you to sign in again when one expires.
- Removing a user means deleting their role bindings and their `policy.csv` line; the provider still lets them
  sign in, to nothing.
