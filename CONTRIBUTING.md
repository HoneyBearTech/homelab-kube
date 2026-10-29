# Contributing to homelab-kube

Thanks for your interest. homelab-kube is the maintainer's Kubernetes manifests for a small k3s homelab cluster,
applied by Argo CD; it is published so others can read and reuse it, and contributions are welcome. It has one
maintainer (see [GOVERNANCE.md](GOVERNANCE.md)), and changes deploy to a real cluster when they merge.
There is no service-level agreement, and review may take a while. Releases are tagged
([CHANGELOG.md](CHANGELOG.md)).

## Reporting bugs and suggesting changes

- **Bugs and ideas**: [GitHub Issues](https://github.com/HoneyBearTech/homelab-kube/issues), using the templates.
  Say which version you run, which Application is involved and what you did, and leave out passwords, tokens,
  hostnames, domains, IP addresses and paths.
- A bug in k3s, Argo CD, Headlamp or another chart itself belongs with that project.
- **Security vulnerabilities**: never in a public issue; see [SECURITY.md](SECURITY.md).

## Development setup

You need git and Python 3.14. Everything else is pinned in `requirements-dev.txt` and installed into `.venv/`:

```sh
make lint       # ruff, ruff format, yamllint
make test       # the policy checker's unit tests, with the coverage floor
make check      # the manifest policy over the repository (scripts/check_manifests.py)
make validate   # every manifest against the Kubernetes and Argo CD schemas (needs kubeconform and network)
```

No cluster is needed for any of them.

## When and how tests run

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs on every pull request and every push to `main`.
"Checks + tests", the required check, runs ruff, yamllint, actionlint (with shellcheck on every `run:` script),
gitleaks over the whole history, the checker's unit tests with a coverage floor, the manifest policy
([`scripts/check_manifests.py`](scripts/check_manifests.py)) and kubeconform. CodeQL, dependency review, the DCO
check and OpenSSF Scorecard run too. The unit tests need no cluster and no network.

## Before you open a pull request

```sh
make lint && make test && make check
```

and `make validate` if you changed a manifest.

## Coding standards

- **Argo CD Applications** (`apps/`): every Helm chart pinned to an exact version (`targetRevision: 1.2.3`);
  this repository followed at `main`; any other git repository at a full commit SHA. Values go inline
  (`helm.valuesObject`) so a pull request shows every change.
- **Manifests** (`manifests/`): every image pinned as `name:tag@sha256:<digest>`; no privileged containers, host
  network, PID or IPC unless the object has a `homelab-kube/allow-<rule>` annotation giving the reason; no `Secret`
  objects at all (secrets are created in the cluster, never committed). `scripts/check_manifests.py` enforces this.
- **Public files**: no private IP addresses, internal domains or host names anywhere. Site-specific values are
  given to the cluster outside this repository (docs/installing.md). The checker refuses private addresses and
  `.lan` / `.internal` / `.home.arpa` names, and CI adds the maintainer's own names from a secret.
- **Python** (`scripts/`, `tests/`): [ruff](https://docs.astral.sh/ruff/) with every rule family
  (`pyproject.toml`), formatted with `ruff format`.
- **YAML** (manifests, workflows, templates): [yamllint](https://yamllint.readthedocs.io/) with
  [`.yamllint.yml`](.yamllint.yml), in strict mode.
- **Workflows**: [actionlint](https://github.com/rhysd/actionlint) with
  [shellcheck](https://www.shellcheck.net/) on every `run:` script. Actions are pinned by commit SHA, jobs
  get the least permissions they need, and untrusted event data reaches scripts only through `env:`.

## Test policy

- A change to `scripts/check_manifests.py` comes with tests for what it adds or fixes, and keeps coverage above the
  floor in `pyproject.toml`.
- A change to a manifest or Application passes the policy check and kubeconform in CI, and is watched in Argo CD
  after it merges (it deploys); the pull request says what to look for.

## Developer Certificate of Origin

Every commit must be signed off to certify the [Developer Certificate of Origin](https://developercertificate.org/):
that you wrote the change or otherwise have the right to submit it under the project's license. Add the
sign-off with `git commit -s`, which appends:

```
Signed-off-by: Your Name <you@example.com>
```

using your git `user.name` and `user.email`. The DCO check
([`.github/workflows/dco.yml`](.github/workflows/dco.yml)) fails a pull request with an unsigned commit; fix
it with `git rebase --signoff main` and force-push your branch.

## Pull requests

- `main` is protected: changes land only through a pull request, and the required CI check must pass. Pull
  requests are squash-merged.
- Keep each pull request focused on one change, and describe what it does and why. A chart or image bump links its
  release notes and says whether it migrates data or changes CRDs.
- Update `README.md`, the docs and `CHANGELOG.md` (under "Unreleased") when you change Applications, settings
  or user-visible behaviour.
- **This repository is public.** Never commit passwords, tokens, certificates, kubeconfigs, hostnames, domains, IP
  addresses or host paths. Secret scanning with push protection is on, and CI runs gitleaks over the
  history.

## Releases

The maintainer adds a `## [x.y.z] - date` section to `CHANGELOG.md`, then pushes a signed tag
(`git tag -s vX.Y.Z -m vX.Y.Z && git push origin vX.Y.Z`). The release workflow checks the policy, signs
the checksums and creates the GitHub Release from that changelog section
([docs/verifying-releases.md](docs/verifying-releases.md)).

## License

By contributing, you agree that your contribution is licensed under the project's [MIT License](LICENSE).
