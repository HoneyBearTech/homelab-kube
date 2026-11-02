# Argus agent

[Argus](https://github.com/HoneyBearTech/Argus) (Grafana dashboards, Prometheus and Loki) monitors the homelab's
Docker hosts with one agent container each. On this cluster the same image runs as a DaemonSet
(`manifests/argus-agent/`) with its Kubernetes configuration, so every node, servers included, appears on Argus'
Host Health, Docker Containers and Logs dashboards under its node name. What it collects and why it needs each
permission is in Argus' [docs/kubernetes.md](https://github.com/HoneyBearTech/Argus/blob/main/docs/kubernetes.md).

## The Secret

The Argus server's addresses and the push password are committed encrypted, as the SealedSecret
`manifests/argus-agent/argus-agent.sealed.yaml` ([sealed-secrets.md](sealed-secrets.md)); the controller turns it into
the Secret `argus/argus-agent` the pods read. To change a value, seal it again with the same three keys
(`ARGUS_PROMETHEUS_URL`, `ARGUS_LOKI_URL`, `ARGUS_PROMETHEUS_PASSWORD`), merge, and restart the pods:
`kubectl -n argus rollout restart daemonset argus-agent`.

## What it may do

- **API**: `get` on `nodes/metrics` (each node's kubelet, for container metrics) and `get`, `list`, `watch` on
  pods (to name log files). Nothing it can change.
- **Node**: host network and PID, `/` and `/sys` mounted read-only, root with only `DAC_OVERRIDE`, read-only root
  filesystem, RuntimeDefault seccomp, not privileged, no container runtime socket. The DaemonSet waives
  `no-privileged` for this, with its reason in the annotation.
- **Network**: outbound only, to Prometheus and Loki. Alloy's own UI listens on the node's loopback.

## Checking it

`kubectl -n argus get pods -o wide` shows one Running pod per node. In Argus, each node has a row on Host Health,
its pods' containers show on Docker Containers as `<namespace>/<container>`, and Logs lists the node as a host.
The image is pinned by digest; a new Argus release is a digest bump here.
