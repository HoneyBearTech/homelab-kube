## What and why

<!-- What does this change, and why? Link the issue it closes, if any. For a chart or image bump, link the
release notes and say whether it migrates data or changes CRDs. -->

## Checklist

- [ ] Every commit is signed off (`git commit -s`), certifying the [DCO](https://developercertificate.org/); see [CONTRIBUTING.md](../CONTRIBUTING.md#developer-certificate-of-origin).
- [ ] `make lint` and `make test` pass locally (CI runs the same, plus the manifest policy check, schema validation, and the workflow and secret scanners).
- [ ] Every Helm chart is pinned to an exact version and every image as `name:tag@sha256:<digest>`; any policy exception has a `homelab-kube/allow-<rule>` annotation with a reason.
- [ ] User-visible changes are in `CHANGELOG.md` under "Unreleased", and the README / `docs/` are updated.
- [ ] No secrets, tokens, certificates, hostnames, domains, IP addresses or host paths are committed.
