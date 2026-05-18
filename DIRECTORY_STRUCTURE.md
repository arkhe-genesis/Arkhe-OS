# ARKHE Ω-TEMP Directory Structure Guide

This document maps out the top-level directories in the Arkhe OS monorepo to help developers and agents navigate the project hierarchy effectively.

```text
/
├── .github/                  # CI/CD workflows and actions
├── .agents/                  # Configurations and prompts for autonomous subagents
├── agents/                   # Agent implementation code and logic
├── agi/                      # Core Artificial General Intelligence models and scripts
├── api/                      # External and internal API definitions and routing
├── Arkhe/                    # Primary Arkhe namespace components
├── arkhe-*/                  # Broad namespace for core libraries, platforms, and services
│   ├── arkhe-os/             # Core OS level logic
│   ├── arkhe-polyglot-parser/# Rust-based universal syntax tree parser
│   ├── arkhe-sdk-python/     # Python bindings for ecosystem integration
│   └── ...                   # Other specific integrations (e.g., arkhe-webrtc, arkhe-cpp)
├── arkp-*/                   # Arkhe Plugins and specific application protocols
│   ├── arkp_qnc/             # Quantum Neural Coding
│   ├── arkp_quantum/         # Quantum hardware interfaces
│   └── ...
├── benchmarks/               # Performance measurement tools and outputs
├── bindings/                 # FFI bindings for cross-language integration
├── build/                    # Build artifacts and intermediate files
├── cmd/                      # Command-line interface entry points
├── components/               # Shared reusable UI or logical components
├── config/                   # Global configuration files and schemas
├── contracts/                # Smart contracts (Solidity, LFIR, EVM bridges)
├── core/                     # Fundamental low-level shared logic
├── data/                     # Local data storage, datasets, and databases (e.g. timechain.db)
├── deploy/                   # Deployment scripts and configurations
├── docs/                     # Extensive markdown documentation, schemas, and architecture notes
├── edge/                     # Code targeted for edge computing and IoT
├── execution/                # Execution environments and VM sandboxes
├── firmware/                 # Code for hardware execution (e.g., ESP32)
├── hardware/                 # Hardware integration layer and specs
├── infrastructure/           # Infrastructure as code (e.g., Terraform)
├── integration/              # Scripts connecting multiple systems
├── jails/                    # FreeBSD Jail configurations and orchestration
├── kernel/                   # Loadable Kernel Modules (LKMs) for Linux/FreeBSD (e.g., arkhe_bus)
├── ml/                       # Machine Learning models and training scripts
├── mock_app_dir/             # Mock applications for testing interactions
├── models/                   # Data structures and domain models
├── packages/                 # Internal monolithic packages
├── packaging/                # Scripts to build installers (DEB, EXE, etc.)
├── paper91/                  # Academic manuscripts and research papers
├── pipeline/                 # Data and CI/CD pipeline definitions
├── protocols/                # Specifications for communication and interaction
├── python/                   # General Python utility scripts and core
├── runtime/                  # Edge and local runtime executors
├── scripts/                  # Utility and maintenance bash/python scripts
├── security/                 # Cryptography, HSM integration, and Zero-Trust policies
├── server/                   # Backend server applications
├── services/                 # Microservices (e.g., parser service, analytics)
├── src/                      # Primary source code directory (often for Rust/C++ projects)
├── store/                    # Database interfaces (SQLite Canonical Store)
├── substrate-*/              # Implementation of specific enumerated "Substratos"
├── substrates/               # Collection of various substrate modules
├── system32/                 # Windows-specific driver and integration code
├── templates/                # Document and code templates
├── temporal/                 # TemporalChain networking and custody logic
├── terraform/                # Cloud infrastructure provisioning
├── test/ & tests/            # Comprehensive test suites (unit, integration, chaos)
├── third_party/              # External dependencies and submodules
├── tools/                    # Developer and operational tools
├── transparency/             # Scripts for generating transparency and audit reports
├── tutorials/                # Educational content and Jupyter notebooks
├── ui/                       # User interfaces (Desktop, Web)
├── validation/               # Lab and production validation routines
├── wetlab/                   # Integration scripts for biological systems
├── windows/                  # Windows native integration scripts
├── wix/                      # Windows Installer XML (WiX) files
└── zig/                      # Zig language integrations
```

## Finding Your Way

- **If you're debugging a test failure:** Start in the `tests/` directory and trace back to the relevant `substrate-*` or `arkhe-*` module.
- **If you're working on the core logic:** Look into `core/`, `kernel/`, or the specific `substrate-*` directory.
- **If you need to understand the philosophy or design:** Read the files in `docs/` and `wiki/`.
- **If you're deploying:** Check `scripts/`, `deploy/`, and `terraform/`.
