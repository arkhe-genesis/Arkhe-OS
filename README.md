# ARKHE OS Sovereign Intelligence

This repository is the Arkhe OS AGI/ASI sovereign intelligence monorepo.
It contains the architectural artifacts, substrate implementations, runtime engines,
contracts, models, and verification tooling for the Arkhe Cathedral.

## Repository structure

- `python/arkhe_os/` — canonical Python runtime and AGI/ASI packages.
- `arkhe_unified/` — unified orchestrator and multi-language integration layer.
- `arkhe-os-substrates-122-125/` — canonical substrate specifications for temporal
  compiler, cryogenic kernel, benchmark suite, and interface.
- `substrate-126/` through `substrate-129/` — temporal network, scheduler,
  memory hierarchy, and distributed CTC consensus subsystems.
- `substrates/` — curated substrate prototypes and early implementations.
- `tools/chrome-devtools-mcp/` — legacy Chrome DevTools MCP package relocated from
  the repo root.
- `docs/` — architecture diagrams, specification drafts, and operational manuals.
- `tests/` — verification and integration tests.
- `SUBSTRATES_INDEX.md` — current substrate inventory.
- `RESTRUCTURE_PLAN.md` — detailed refactor plan for the AGI/ASI production-ready
  architecture.

## Current status

This commit begins the repository reorganization by:
- moving the legacy `chrome-devtools-mcp` package into `tools/chrome-devtools-mcp/`
- separating Arkhe OS core and substrate assets from the browser tooling
- creating a substrate index and a refactor plan for the sovereign architecture

## Next steps

1. Consolidate `substrates/`, `arkhe-os-substrates-122-125/`, `arkhe-substrate-123/`,
   and `substrate-126..129/` into canonical substrate groups.
2. Establish `core/`, `runtime/`, `contracts/`, `models/`, `.agi/`, `.casi/`, and
   `.asi/` layers as defined in `RESTRUCTURE_PLAN.md`.
3. Implement `make genesis` and the genesis bootstrapper.
4. Add verification, package manager integration, and production-grade model
   management.

## Legacy tool location

The relocated Chrome DevTools MCP package now lives at:

- `tools/chrome-devtools-mcp/`

Use that package as a contained developer utility and do not mix it with the
Arkhe OS sovereign runtime.

---

> This repo is being refactored into a production-grade AGI/ASI stack.
> For architecture and migration details see `RESTRUCTURE_PLAN.md`.
