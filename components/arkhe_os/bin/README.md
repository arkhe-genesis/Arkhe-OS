# AGI Userspace Binaries (Substrate 314)

This directory contains the userspace binaries for interacting with the AGI kernel subsystem.

## Components

- `agictl`: SovereignCLI — Interface principal
- `agimon`: CoherenceObserver — Monitoramento em tempo real
- `agifed`: FederatedBridge — Cliente para consenso federado
- `agikey`: GenesisKeyManager — Gerenciamento de chaves quânticas gênese
- `agilog`: IntentAuditor — Auditoria e query de logs
- `agieval`: CoherenceValidator — Validação e benchmark
- `agiboot`: GenesisBootstrapper — Inicialização de estado gênese
- `agidebug`: TemporalDebugger — Debugging de inferência retrocausal
