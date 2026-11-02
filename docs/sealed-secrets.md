# Sealed Secrets

[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) lets a Secret be committed to this public
repository encrypted, as a `SealedSecret`. Anyone can encrypt ("seal") with the controller's public certificate;
only the controller in this cluster holds the private key that decrypts. It then creates, and keeps up to date, the
ordinary Secret the app reads.

`apps/sealed-secrets.yaml` installs the controller as `sealed-secrets-controller` in `kube-system`, the name and
namespace `kubeseal` uses by default.

## After the first sync: back up the key

The sealing key is made by the controller on its first start, in the cluster only. If the cluster is rebuilt without
it, every SealedSecret in git becomes unreadable. With the admin kubeconfig, save it once to the password manager,
then delete the file:

```sh
kubectl -n kube-system get secret -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > sealing-key.yaml
```

The key is never renewed (`keyrenewperiod: "0"`), so this one copy stays enough.

The public certificate isn't secret: it's committed as [`sealed-secrets.pem`](../sealed-secrets.pem) at the top of
the repository (valid until 2036-10-30), so sealing needs no cluster access. The controller prints it in its log on
start; after a new key, replace the file with it.

## Sealing a Secret

Write the Secret locally (never committed), seal it, and commit only the output:

```sh
kubectl -n <namespace> create secret generic <name> --dry-run=client -o yaml \
  --from-literal=KEY=<value> > secret.yaml
kubeseal --cert sealed-secrets.pem --format yaml < secret.yaml > manifests/<app>/<name>.sealed.yaml
rm secret.yaml
```

CI's secret scan (gitleaks) skips only lines shaped like kubeseal's output (`.gitleaks.toml`); a plain value is
still reported.

A SealedSecret only works under the name and namespace it was sealed for. To change one value, seal again with
`kubeseal --merge-into`.

A Secret made by hand before is left alone: to let a SealedSecret take it over, annotate it first with
`sealedsecrets.bitnami.com/managed=true`.

## Restoring after a rebuild

Before Argo CD syncs this Application on a new cluster, apply the saved key file
(`kubectl apply -f sealing-key.yaml`), then let the controller start: it picks the key up and decrypts every
SealedSecret.

## Rotating the key

Only when the key may have leaked: delete the key Secret and restart the controller, which makes a new one; then
commit the new certificate, re-seal every SealedSecret and back the new key up. Values sealed with a leaked key
must be changed at their source as well, since old commits keep the old ciphertext.
