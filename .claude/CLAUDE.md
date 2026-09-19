# Arkhe OS repository guidance

Before editing, read [`../docs/architecture/AI_AGENT_OPERATING_MODEL.md`](../docs/architecture/AI_AGENT_OPERATING_MODEL.md)
and [`../AGENTS.md`](../AGENTS.md). This repository contains multiple
independent projects: find the nearest manifest and README, then run only the
component's relevant checks. Treat identity, cryptography, governance,
boot/kernel, hardware, and deployment changes as security-sensitive. Do not
touch generated artifacts, binaries, or unrelated local modifications.
