# ARKHE OS Substrate Inventory

This inventory documents the current substrate directories and their high-level purpose.
It is a working index for the larger Arkhe OS refactor.

## Root substrate directories

- `arkhe-os-substrates-122-125/`
  - Substrate 122: Temporal Compiler
  - Substrate 123: Cryogenic Kernel
  - Substrate 124: Benchmark Suite
  - Substrate 125: Interface

- `arkhe-substrate-123/`
  - Implementation of Substrate 123 logic and related temporal kernel experiments.

- `substrate-126/`
  - Temporal Network Stack (qHTTP protocol, distributed state transfer).

- `substrate-127/`
  - Quantum OS Scheduler.

- `substrate-128/`
  - Temporal Memory Hierarchy.

- `substrate-129/`
  - Distributed CTC Consensus.

- `substrates/`
  - Prototype and exploratory substrate modules:
    - `substrato_134_sistema_exterior/`
    - `substrato_175_autopoiese_galactica/`
    - `v168_noma/`
    - `v170_living_crystal/`
    - `v172_distributed_quantum/`
    - `v174_hodge_duality/`

## Notes

- This is a partial inventory; the repository also contains substrate-related
  implementations in `python/arkhe_os/`, `arkhe_unified/`, and other packages.
- The next phase is to merge these directories into the canonical layer tree
  described in `RESTRUCTURE_PLAN.md`.
