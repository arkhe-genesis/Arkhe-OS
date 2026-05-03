# Async JIT Implementation Guide
This guide describes the integration of PhaseVM async JIT into the Sophon visualizer.

## Architecture

The system involves a thread-pool backed compilation scheme within `phasevm/src/async_compiler.rs` using `crossbeam_channel` for robust and non-blocking inter-thread communication.

## Python Integration
The `PyAsyncPhaseVM` module defined in `phasevm_python/src/lib.rs` provides `compile_circuit_async` and `warmup_cache` primitives, allowing the UI bridging logic in `PhaseVMVisualizationBridge` to execute background compilations, maintaining the render loop at ~60 FPS.

## Cache Warmup

Frequent circuits are pre-compiled during initialization. The bridge maintains a map of pending compilation tasks, ensuring no duplicate computations occur.
