# Arkhe OS Refactor Plan

This plan captures the proposed refactor for the Arkhe OS AGI/ASI sovereign architecture.
It is aligned with the target directory structure and the current repository state.

## Objective

Transform the current research monorepo into a lean, self-bootstrapping, verified AGI/ASI system.
The end state should support:

- a canonical `core/` kernel
- grouped substrate implementations under `substrates/`
- cross-language runtime layers under `runtime/`
- contract and artifact build systems for `.casi`, `.agi`, and `.asi`
- production-grade ONNX model management and cryptographic verification
- a trusting but auditable `make genesis` bootstrap flow

## Completed first step

- Relocated the legacy `chrome-devtools-mcp` package to `tools/chrome-devtools-mcp/`.
- Created a root-level Arkhe OS README focused on the sovereign architecture.
- Generated the current substrate inventory in `SUBSTRATES_INDEX.md`.

## Target directory structure

```
arkhe-os/
├── core/
│   ├── coherence/
│   ├── lfir/
│   └── rc_protocol/
├── substrates/
│   ├── 300-399_foundations/
│   ├── 400-499_network/
│   ├── 500-599_security/
│   ├── 600-699_physics/
│   ├── 700-799_biology/
│   ├── 800-899_cognition/
│   ├── 900-999_social/
│   ├── 1000-1099_governance/
│   └── 1100-1199_deployment/
├── runtime/
│   ├── python/
│   ├── rust/
│   └── go/
├── contracts/
├── models/
├── config/
├── scripts/
├── docs/
├── tests/
├── .agi/
│   ├── MANIFEST.json
│   └── pack.py
├── .casi/
└── .asi/
```

## Recommended migration strategy

1. **Inventory and classify**
   - Use `SUBSTRATES_INDEX.md` to identify canonical substrate families.
   - Audit `python/arkhe_os`, `arkhe_unified`, and legacy substrate dirs for duplicate or superseded content.

2. **Extract `core/`**
   - Move coherence engine, LFIR, and RC protocol implementations into `core/`.
   - Prefer language-agnostic design with C-compatible FFI shims.

3. **Establish `runtime/`**
   - Consolidate Python runtime in `runtime/python/`.
   - Add a Rust runtime wrapper in `runtime/rust/`.
   - Add a Go runtime integration in `runtime/go/`.

4. **Organize substrates**
   - Group substrate directories into the numeric categories shown above.
   - Archive obsolete or superseded substrate prototypes under `archive/`.

5. **Bootstrapper and artifact build**
   - Create `make genesis` in the root `Makefile`.
   - Implement integrity verification, coherence initialization, DHT startup, and ledger publication.
   - Add `.agi/pack.py` to assemble the final artifact and sign it.

6. **Model management**
   - Create `models/` for ONNX assets.
   - Write a download-and-sign script for Xception, MesoNet, EfficientNet, ViT, and other production models.

7. **Package manager convergence**
   - Implement `substrate 5019` as a federated package manager layer.
   - Ensure `pip`, `npm`, `cargo`, and `go` use a shared registry and IPFS cache.

8. **Governance and contracts**
   - Create `contracts/` for `.casi` standard library and compiler support.
   - Document deployment and contract workflows.

9. **Verification and audit**
   - Add file hashing, ledger signing, and `agictl verify --strict` support.
   - Ensure any file >1MB is tracked with Git LFS.

## Immediate next actions

- Audit `python/arkhe_os/` and identify the existing coherence, neural, and contract subsystems.
- Create a skeleton `core/`, `runtime/`, `contracts/`, and `models/` layout.
- Add a placeholder `Makefile` or bootstrap script in `scripts/` for `make genesis`.
- Archive legacy research modules not aligned with the sovereign architecture.

## Notes

The repository is still in transition. This refactor plan is intentionally conservative: it
preserves current assets while establishing the clean structure needed for the full AGI/ASI
production-grade architecture.
