.PHONY: test lint check validate

PYTHON ?= python3
VENV := .venv
# kubeconform for `make validate` (https://github.com/yannh/kubeconform); CI downloads the same version and
# checks its SHA-256. The Argo CD schemas come from the CRDs catalog at a pinned commit.
CRDS_CATALOG := https://raw.githubusercontent.com/datreeio/CRDs-catalog/3eb90d47aba8d61919d4419dd38301536e32a94b

# Check and test tools, pinned with hashes; the venv is rebuilt when the requirements change
$(VENV)/.installed: requirements-dev.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes --no-deps -r requirements-dev.txt
	touch $@

# Unit tests for the policy checker, with the coverage floor from pyproject.toml (offline)
test: $(VENV)/.installed
	$(VENV)/bin/coverage run -m pytest -q
	$(VENV)/bin/coverage report

# The Python and YAML linters CI runs (the workflow and secret scanners run in containers; see ci.yml)
lint: $(VENV)/.installed
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/yamllint --strict .

# The manifest policy: pinned charts, images and git sources, no Secrets, nothing privileged, nothing internal
check: $(VENV)/.installed
	$(VENV)/bin/python scripts/check_manifests.py

# Every manifest against the Kubernetes and Argo CD schemas (needs kubeconform on PATH and network)
validate:
	kubeconform -strict -summary -schema-location default \
	  -schema-location '$(CRDS_CATALOG)/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
	  bootstrap apps manifests
