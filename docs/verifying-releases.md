# Verifying releases

Every homelab-kube release is published by the [`release.yml`](../.github/workflows/release.yml) workflow
when a version tag is pushed. homelab-kube builds no images or charts: a release is a version of the manifests,
with every Helm chart pinned to an exact version and every image by digest. You can check that what you run came from that workflow, unchanged:

- the GitHub Release has a source archive (with the license), a **CycloneDX SBOM** listing every Helm
  chart, its version and repository (`homelab-kube-<version>.cdx.json`) and `SHA256SUMS` for both;
- `SHA256SUMS` is signed with [cosign](https://docs.sigstore.dev/) "keylessly": the signature
  (`SHA256SUMS.sigstore.json`) is tied to the workflow's GitHub identity through
  [Sigstore](https://www.sigstore.dev/), so there is no long-lived signing key to steal, and every
  signature is recorded in the public Rekor transparency log;
- **SLSA build provenance** covers every file in `SHA256SUMS`
  (`homelab-kube-<version>.provenance.sigstore.json`, also stored by GitHub, and as in-toto JSON Lines in
  `homelab-kube-<version>.intoto.jsonl`);
- the **version tag** in git is signed with the maintainer's SSH key.

You need [cosign](https://docs.sigstore.dev/cosign/system_config/installation/) 3.0 or later. The examples
use version 0.1.0; substitute the one you run. There is no release yet: the first is **Planned**.

## The release files

Download `SHA256SUMS`, `SHA256SUMS.sigstore.json`, the SBOM and the source archive from the
[release page](https://github.com/HoneyBearTech/homelab-kube/releases), then:

```sh
cosign verify-blob SHA256SUMS --bundle SHA256SUMS.sigstore.json \
  --certificate-identity-regexp '^https://github\.com/HoneyBearTech/homelab-kube/\.github/workflows/release\.yml@refs/tags/v' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
sha256sum -c SHA256SUMS
```

The first command proves `SHA256SUMS` came from the release workflow; the second, that the archive and
SBOM match it.

## Build provenance

With the [GitHub CLI](https://cli.github.com/):

```sh
gh attestation verify homelab-kube-0.1.0.tar.gz --repo HoneyBearTech/homelab-kube \
  --signer-workflow HoneyBearTech/homelab-kube/.github/workflows/release.yml
```

To verify offline, add `--bundle homelab-kube-0.1.0.provenance.sigstore.json`.

## The git tag

The maintainer signs version tags with an SSH key whose public half is in
[`.github/allowed_signers`](../.github/allowed_signers):

```sh
git clone https://github.com/HoneyBearTech/homelab-kube.git && cd homelab-kube
git -c gpg.ssh.allowedSignersFile=.github/allowed_signers tag -v v0.1.0
```

It should print `Good "git" signature for 31805425+HoneyBearTech@users.noreply.github.com`. Check
`.github/allowed_signers` against the key published at <https://github.com/HoneyBearTech.keys> rather than
trusting the copy in the repository alone.

## The charts and images

The charts and images are signed (or not) by their own publishers. What homelab-kube guarantees is that the versions
in the verified SBOM and in `apps/` are the ones that were reviewed: Argo CD fetches exactly those chart versions,
and every image in `manifests/` is pinned by digest. To compare what a cluster runs with a release:

```sh
kubectl -n argocd get applications -o custom-columns=NAME:.metadata.name,REVISION:.status.sync.revision
jq -r '.components[] | "\(.name) \(.version)"' homelab-kube-<version>.cdx.json
```
