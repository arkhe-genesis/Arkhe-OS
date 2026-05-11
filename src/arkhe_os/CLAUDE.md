# Arkhe OS: CLAUDE.md - Build & Dev Instructions

## System Commands
- **Boot OS**: `cd src/arkhe_os && make && ./arkhe_os`
- **Run App**: `cd src/arkhe_os && ./arkhe-app <app_name> [args]`
- **Build Libraries**: `cd src/arkhe_os && make`

## Development Procedures
1. **Adding OpCodes**: Update `vm/phase_vm.h` and implement in `vm/phase_vm.c`.
2. **HAL Integration**: Ensure all hardware register calls are wrapped in `arkhe_hal.c`.
3. **Coherence Management**: The `arkhe_daemon` handles real-time λ₂ optimization.
4. **Memory**: Use `LD_PRELOAD=./libarkhe_alloc.so` for phase-aware allocations.

## Architecture
- Layered architecture: Hardware -> HAL -> Kernel -> PhaseVM -> Apps.
- Native integration with Arkhe-Chain for event logging.
