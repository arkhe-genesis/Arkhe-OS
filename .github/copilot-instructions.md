# Arkhe OS contribution context

Read [`../docs/architecture/AI_AGENT_OPERATING_MODEL.md`](../docs/architecture/AI_AGENT_OPERATING_MODEL.md)
and [`../AGENTS.md`](../AGENTS.md) before proposing a change. This repository
contains many independently built components. Determine the local build and
test contract from the closest manifest and README; do not assume that a root
package configuration applies to every directory.

Keep pull requests focused on one component or interface. Preserve unrelated
worktree changes, avoid generated and binary artifacts, and report the narrow
validation actually run. Handle cryptography, identity, governance, boot/kernel,
firmware, hardware, deployment, and infrastructure changes as security-sensitive.
