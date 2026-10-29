# homelab-kube documentation

Start with the [README](../README.md) for what homelab-kube is and how to run it.

| Document | For |
| --- | --- |
| [Quick start](quick-start.md) | From a running k3s cluster to Argo CD and Headlamp |
| [Installing](installing.md) | What the cluster needs first, Argo CD, the root Application, running it securely, uninstalling |
| [Argus agent](argus-agent.md) | Metrics and logs of every node to Argus: the Secret to create first, what the agent may do |
| [Media trial](media-trial.md) | Sonarr and Radarr on copied configs: the guards, copying a config in, the checklist |
| [Upgrading](upgrading.md) | Bumping a chart, upgrading Argo CD and k3s, and rolling back |
| [Architecture](architecture.md) | The cluster, the Applications, and how a change reaches the cluster |
| [Interfaces](interfaces.md) | Every Application, setting, annotation and command |
| [Verifying releases](verifying-releases.md) | Checking that release files came from this repository, unchanged |
| [Security requirements](security.md) | What the manifests protect, what they don't, and where secrets live |
| [Assurance case](assurance-case.md) | The threat model, trust boundaries and why the security requirements are met |
| [Dependencies](dependencies.md) | How charts, images and tools are chosen, pinned, tracked and patched |
| [Roadmap](roadmap.md) | What's planned for the next year, and what homelab-kube will not do |

Project policies live at the top of the repository: [CONTRIBUTING.md](../CONTRIBUTING.md),
[GOVERNANCE.md](../GOVERNANCE.md), [SECURITY.md](../SECURITY.md), [SUPPORT.md](../SUPPORT.md),
[CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) and [CHANGELOG.md](../CHANGELOG.md).

These documents change in the same pull request as the behaviour they describe. Anything not built yet is
marked **Planned**. If you find a document that's wrong, please
[open an issue](https://github.com/HoneyBearTech/homelab-kube/issues): it's treated as a bug.
