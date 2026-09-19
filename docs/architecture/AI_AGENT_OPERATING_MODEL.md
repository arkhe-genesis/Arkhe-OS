# Arkhe OS: operating model for coding agents

## Purpose and scope

Arkhe OS is a **polyglot repository of multiple projects**, not a single
application. This document gives coding assistants a common map before they
modify code. It covers the repository root and does not replace a component's
own `README`, manifest, or nested `AGENTS.md`.

## Repository map

| Area | Role | How to identify the contract |
| --- | --- | --- |
| `crates/` | Rust services and libraries for Cathedral, Arkhe, Safe-Core, identity, inference, observability, and zero-knowledge functions. | The root `Cargo.toml` declares the maintained workspace members. |
| `cathedral-arkhe/` and `timechain/` | Workspace Rust components for safety, UEP, temporal and related runtime work. | Their `Cargo.toml` files and the root workspace manifest. |
| `arkhe-os/`, `kernel/`, `bootloader/` | Operating-system, kernel, boot, and platform-specific work. | Each component's manifest and README; do not assume root-workspace membership. |
| `src/`, `core/`, `arkhe_core/`, and Python packages | Python services, research, APIs, orchestration, and simulations. | Their local `pyproject.toml`, `requirements*.txt`, and tests. |
| `arkhe-android/`, `arkhe-ios/`, `arkp-mobile/`, `arkhe-webrtc/` | Mobile and client integrations. | Their platform build files and READMEs. |
| `contracts/`, `quantum/contracts/`, `arkhe_evm_bridge/` | Smart-contract and chain integrations. | Contract tool configuration and contract-local tests. |
| `terraform/`, `k8s/`, `helm/`, `deploy/`, `.github/` | Infrastructure, delivery, and automation. | IaC module boundaries and workflow-local triggers. |
| `substrate-*`, `substrato-*`, `substrates/` | Independently versioned substrate experiments and implementations. | The individual substrate's manifest, specification, and tests. |
| `docs/`, `specs/`, `runbooks/` | Architectural, operational, and protocol documentation. | Treat normative specifications as contracts when code cites them. |

## Boundaries and safety rules

1. **Workspace is explicit.** Only crates listed in root `Cargo.toml` belong
   to the root Rust workspace. Run Cargo commands with `-p <member>` when the
   target is known; enter a standalone project before using its manifest.
2. **Manifests are local contracts.** Root `pyproject.toml` and `package.json`
   describe projects at the root, not every Python or JavaScript subtree.
   Locate the nearest manifest before installing dependencies or running tests.
3. **Security-sensitive code needs narrow changes.** Treat `crypto/`,
   `security/`, `safe-core/`, `crates/*identity*`, `crates/*zk*`, boot/kernel,
   firmware, hardware, deployment, and governance paths as sensitive. Keep
   serialization, cryptographic parameters, authorization behavior, and
   deployment defaults stable unless a reviewed migration is requested.
4. **Generated and binary material is not source.** Do not casually modify
   `node_modules/`, `.gradle/`, build outputs, firmware blobs, model/data
   artifacts, lock files, or generated bindings. Regenerate from the owning
   component only when the task requires it.
5. **Documentation must be truthful.** The root README is not a complete
   repository guide. Prefer component documentation and this map when deciding
   what a change affects.

## Change procedure

1. Start with `git status --short` and preserve pre-existing modifications.
2. Identify the component from the table above; read its nearest manifest,
   README, tests, and nested agent instructions.
3. Search for callers, protocol types, and configuration references before
   changing public behavior.
4. Make the smallest coherent change. Avoid broad formatting or dependency
   upgrades in an unrelated fix.
5. Validate at the component boundary. Examples include `cargo test -p NAME`,
   a local Python test command, a package script in the nearest `package.json`,
   or `terraform validate` in the changed IaC module.
6. Review `git diff --check` and `git diff -- <paths>` before committing.

## Tool-neutral output requirements

State the component changed, the command(s) actually run, and any validation
that was skipped. Separate observations from assumptions. Do not expose hidden
reasoning, secrets, access tokens, private keys, or unredacted production data.

## Maintaining this document

Update this map when a new maintained workspace, top-level subsystem, or
cross-component interface is added. Keep tool-specific configuration concise:
it should point here and contain only tool behavior that cannot be expressed in
this shared guide.
