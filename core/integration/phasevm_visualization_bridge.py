#!/usr/bin/env python3
"""
PhaseVM → Visualization Bridge — Complete Bytecode to Shader Pipeline
Connects Rust JIT compilation to Pygfx/WGPU shader rendering via Jones invariants.

Pipeline:
  Network Metrics → Topological Bytecode → PhaseVM JIT → Jones Invariant
  → Shader Parameter Mapping → GPU Uniform Update → Real-time Visualization
"""
import numpy as np
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import logging
from concurrent.futures import ThreadPoolExecutor

from phasevm import PhaseVM  # Rust binding via PyO3
from core.visualization.sophon_hexagon_v2 import SophonHexagonEngine
from core.visualization.bidirectional_ui import BidirectionalUI, UIParameter

logger = logging.getLogger(__name__)

@dataclass
class WarmupConfig:
    """Configuration for JIT cache warm-up during initialization."""
    # Predefined profiles: 'minimal', 'standard', 'comprehensive'
    profile: str = 'standard'
    # Custom circuits to add (list of gate name lists)
    custom_circuits: List[List[str]] = field(default_factory=list)
    # Maximum time to spend on warm-up (seconds)
    timeout_seconds: float = 5.0
    # Prioritize shorter circuits (higher coherence) first
    prioritize_by_coherence: bool = True
    # Log warm-up progress
    verbose: bool = False

class CompilationMode(Enum):
    """Mode for bytecode compilation and parameter mapping."""
    AMPLITUDE = auto()      # |J| → wave amplitude
    PHASE = auto()          # arg(J) → wave phase offset
    FREQUENCY = auto()      # Re(J) → frequency modulation
    COUPLING = auto()       # Im(J) → nonlinear coupling strength
    MIXED = auto()          # Adaptive mapping based on circuit complexity

@dataclass
class BytecodeToShaderConfig:
    """Configuration for bytecode→shader parameter mapping."""
    # Compilation
    compilation_mode: CompilationMode = CompilationMode.MIXED
    cache_enabled: bool = True
    max_cache_size: int = 1024

    # Mapping parameters
    amplitude_scale: float = 0.5      # Scale factor for |J| → amplitude
    phase_scale: float = np.pi / 4    # Scale for arg(J) → phase offset
    frequency_base: float = 2.0       # Base frequency for Re(J) modulation
    coupling_max: float = 0.3         # Max coupling strength from Im(J)

    # Performance
    compilation_timeout_ms: float = 50.0  # Max time for JIT compilation
    fallback_to_cached: bool = True       # Use cached result if compilation times out

    # Visualization sync
    uniform_update_threshold: float = 0.01  # Min change to trigger GPU update
    frame_sync: bool = True                  # Sync updates to render loop

class PhaseVMVisualizationBridge:
    """
    Bridges PhaseVM Rust JIT compiler to Sophon visualization pipeline.

    Real-time cycle:
    1. Fetch network state → generate topological bytecode
    2. Compile bytecode via PhaseVM JIT → Jones invariant (complex)
    3. Map Jones invariant to shader parameters (amplitude, phase, frequency, coupling)
    4. Update GPU uniform buffer → trigger re-render
    5. (Optional) Feed back visual state to network thresholds via bidirectional UI
    """

    def __init__(
        self,
        visualization_engine: SophonHexagonEngine,
        bidirectional_ui: Optional[BidirectionalUI] = None,
        config: BytecodeToShaderConfig = None,
        sophon_api_url: Optional[str] = None,
        async_compilation: bool = True,
        num_compiler_threads: int = 2,
        warmup_config: Optional[WarmupConfig] = None,
    ):
        self.viz = visualization_engine
        self.ui = bidirectional_ui
        self.config = config or BytecodeToShaderConfig()
        self.sophon_api = sophon_api_url

        # Initialize PhaseVM JIT compiler
        self.phasevm = PhaseVM()

        # Thread pool for async compilation to prevent render loop blocking
        self.executor = ThreadPoolExecutor(max_workers=num_compiler_threads) if async_compilation else None

        # State tracking
        self.last_jones: Optional[complex] = None
        self.last_shader_params: Optional[np.ndarray] = None
        self.compilation_times: List[float] = []

        # Register UI callbacks if available
        if self.ui:
            self._register_ui_callbacks()

        # Execute warm-up cache if configured
        if warmup_config is not None:
            self._execute_warmup(warmup_config)

    def _execute_warmup(self, config: WarmupConfig):
        """Execute JIT cache warm-up during initialization."""
        if not hasattr(self.phasevm, 'warmup_cache'):
            logger.warning("PhaseVM version does not support warm-up; skipping")
            return

        try:
            # Build warm-up config for Rust
            try:
                from phasevm_rs import PyWarmupConfig
            except ImportError:
                # If using the pure-python wrapper module instead of direct bindings
                from phasevm import PyWarmupConfig

            rust_config = PyWarmupConfig()
            rust_config.timeout_seconds = int(config.timeout_seconds)
            rust_config.prioritize_by_coherence = config.prioritize_by_coherence

            # Load predefined profile
            profile_config = PyWarmupConfig.from_profile(config.profile)
            rust_config.circuits = profile_config.circuits

            # Add custom circuits
            for circuit in config.custom_circuits:
                rust_config.add_circuit(circuit)

            # Execute warm-up
            if config.verbose:
                logger.info(f"Starting JIT warm-up: profile={config.profile}, "
                           f"timeout={config.timeout_seconds}s, "
                           f"circuits={len(rust_config.circuits)}")

            start = time.perf_counter()
            stats = self.phasevm.warmup_cache(rust_config)
            elapsed = time.perf_counter() - start

            if config.verbose:
                logger.info(f"Warm-up complete: {stats.successfully_compiled}/{stats.total_requested} "
                           f"compiled, {stats.new_cache_entries} new entries, "
                           f"{stats.elapsed_ms}ms (Python: {elapsed*1000:.1f}ms)")

            # Store stats for monitoring
            self._warmup_stats = stats.to_dict() if hasattr(stats, 'to_dict') else {
                'successfully_compiled': stats.successfully_compiled,
                'new_cache_entries': stats.new_cache_entries,
                'elapsed_ms': stats.elapsed_ms,
            }

        except Exception as e:
            logger.warning(f"Warm-up failed (non-fatal): {e}")
            self._warmup_stats = {'error': str(e)}

    def get_warmup_stats(self) -> Dict[str, any]:
        """Return warm-up execution statistics."""
        return getattr(self, '_warmup_stats', {})

    def _register_ui_callbacks(self):
        """Connect UI controls to bytecode generation parameters."""
        def on_circuit_complexity_change(value: float):
            # UI slider → bytecode length/complexity
            self.circuit_complexity = np.clip(value, 1, 20)
            logger.debug(f"Circuit complexity updated: {self.circuit_complexity}")

        self.ui.add_parameter(UIParameter(
            name="circuit_complexity",
            label="Bytecode Complexity",
            value=5.0, min_val=1.0, max_val=20.0, step=1.0,
            shader_uniform_index=None,  # Not a direct shader param
            network_metric=None
        ))
        self.ui.on_parameter_change("circuit_complexity", on_circuit_complexity_change)

    def network_state_to_bytecode(self, metrics: Dict[str, float]) -> List[str]:
        """
        Convert network coherence metrics to topological bytecode (cbytes).

        Mapping strategy:
        - High coherence → simple circuits (identity, H)
        - Low coherence → complex circuits (multi-gate braids)
        - High BER → gates with imaginary components (Z, phase gates)
        """
        coh_dist = metrics.get('coherence_distance', 0.3)
        delivery = metrics.get('delivery_rate', 0.97)
        ber = metrics.get('ber', 1e-4)

        # Determine circuit complexity based on coherence
        complexity = int(np.clip(1 + (1 - coh_dist) * 10, 1, 15))
        if hasattr(self, 'circuit_complexity'):
            complexity = int(np.clip(self.circuit_complexity, 1, 20))

        # Generate gate sequence
        gates = []
        gate_pool = ['H', 'X', 'Z', 'I']  # Available gates in PhaseVM

        for i in range(complexity):
            # Bias gate selection based on metrics
            if ber > 1e-4 and i % 3 == 0:
                # High BER → more Z gates (phase errors)
                gates.append('Z')
            elif delivery < 0.90 and i % 2 == 0:
                # Low delivery → more X gates (bit flips)
                gates.append('X')
            else:
                # Default: Hadamard for superposition
                gates.append(np.random.choice(gate_pool))

        return gates

    def compile_bytecode_to_jones_sync(self, gates: List[str]) -> Optional[complex]:
        """Synchronous part of compilation"""
        try:
            return self.phasevm.compile_circuit(gates)
        except Exception as e:
            logger.warning(f"JIT compilation failed: {e}")
            raise e

    async def compile_bytecode_to_jones(self, gates: List[str]) -> Optional[complex]:
        """
        Compile bytecode via PhaseVM JIT and return Jones invariant.
        Uses ThreadPoolExecutor to run compilation asynchronously,
        preventing render loop blocking.
        Includes timeout handling and fallback to cached results.
        """
        start = time.perf_counter()

        try:
            # Attempt async compilation with timeout
            loop = asyncio.get_event_loop()
            task = loop.run_in_executor(self.executor, self.compile_bytecode_to_jones_sync, gates)

            # Wait for compilation with timeout
            result = await asyncio.wait_for(task, timeout=self.config.compilation_timeout_ms / 1000.0)

            elapsed_ms = (time.perf_counter() - start) * 1000
            self.compilation_times.append(elapsed_ms)

            # Keep compilation time history bounded
            if len(self.compilation_times) > 100:
                self.compilation_times.pop(0)

            logger.debug(f"JIT compilation: {len(gates)} gates → {elapsed_ms:.2f}ms")
            return result

        except asyncio.TimeoutError:
            logger.warning(f"JIT compilation timed out after {self.config.compilation_timeout_ms}ms")
            if self.config.fallback_to_cached and self.last_jones is not None:
                logger.info("Falling back to cached Jones invariant")
                return self.last_jones
            return None
        except Exception as e:
            if self.config.fallback_to_cached and self.last_jones is not None:
                logger.info("Falling back to cached Jones invariant")
                return self.last_jones
            return None

    def jones_to_shader_params(self, jones: complex) -> Dict[str, float]:
        """
        Map Jones invariant to shader uniform parameters.

        Mapping depends on CompilationMode:
        - AMPLITUDE: |J| → wave_amplitude
        - PHASE: arg(J) → wave_phase offset
        - FREQUENCY: Re(J) → frequency modulation
        - COUPLING: Im(J) → coupling_strength
        - MIXED: Adaptive combination based on circuit complexity
        """
        magnitude = abs(jones)
        phase = np.angle(jones)
        real, imag = jones.real, jones.imag

        params = {}

        if self.config.compilation_mode == CompilationMode.AMPLITUDE:
            params['amplitude_factor'] = np.clip(
                self.config.amplitude_scale * magnitude, 0.0, 1.0
            )
        elif self.config.compilation_mode == CompilationMode.PHASE:
            params['phase_offset'] = np.clip(
                phase * self.config.phase_scale, -np.pi, np.pi
            )
        elif self.config.compilation_mode == CompilationMode.FREQUENCY:
            params['frequency_mod'] = self.config.frequency_base * (1.0 + 0.5 * real)
        elif self.config.compilation_mode == CompilationMode.COUPLING:
            params['coupling_strength'] = np.clip(
                self.config.coupling_max * abs(imag), 0.0, self.config.coupling_max
            )
        else:  # MIXED mode
            # Adaptive mapping based on Jones properties
            params['amplitude_factor'] = np.clip(0.3 + 0.4 * magnitude, 0.3, 1.0)
            params['phase_offset'] = phase * 0.25  # Subtle phase modulation
            params['frequency_mod'] = self.config.frequency_base * (1.0 + 0.3 * real)
            params['coupling_strength'] = np.clip(0.1 * abs(imag), 0.0, 0.15)

        return params

    def update_shader_uniforms(self, params: Dict[str, float]) -> bool:
        """
        Update visualization engine shader uniforms with new parameters.

        Returns True if update was significant enough to trigger re-render.
        """
        if self.viz.ui is None:
            return False

        updated = False

        # Map params to UI parameters (which bind to shader uniforms)
        if 'amplitude_factor' in params:
            new_val = params['amplitude_factor']
            if self._significant_change('wave_amplitude_balance', new_val):
                self.viz.ui.update_parameter('wave_amplitude_balance', new_val)
                updated = True

        if 'coupling_strength' in params:
            new_val = params['coupling_strength']
            if self._significant_change('coupling_strength', new_val):
                self.viz.ui.update_parameter('coupling_strength', new_val)
                updated = True

        # Store for change detection
        self.last_shader_params = params.copy()
        return updated

    def _significant_change(self, param_name: str, new_value: float) -> bool:
        """Check if parameter change exceeds update threshold."""
        if self.last_shader_params is None:
            return True
        old_value = self.last_shader_params.get(param_name)
        if old_value is None:
            return True
        return abs(new_value - old_value) > self.config.uniform_update_threshold

    async def update_cycle(self, metrics: Dict[str, float]) -> Dict[str, any]:
        """
        Execute one complete update cycle: metrics → bytecode → JIT → shader.

        Returns timing and status information for monitoring.
        """
        cycle_start = time.perf_counter()
        result = {'success': False, 'stages': {}}

        try:
            # Stage 1: Bytecode generation
            t0 = time.perf_counter()
            gates = self.network_state_to_bytecode(metrics)
            result['stages']['bytecode_ms'] = (time.perf_counter() - t0) * 1000

            # Stage 2: JIT compilation (Now Async)
            t1 = time.perf_counter()
            jones = await self.compile_bytecode_to_jones(gates)
            if jones is None:
                logger.warning("JIT compilation failed, skipping update")
                result['stages']['compilation_ms'] = (time.perf_counter() - t1) * 1000
                return result
            result['stages']['compilation_ms'] = (time.perf_counter() - t1) * 1000
            self.last_jones = jones

            # Stage 3: Parameter mapping
            t2 = time.perf_counter()
            shader_params = self.jones_to_shader_params(jones)
            result['stages']['mapping_ms'] = (time.perf_counter() - t2) * 1000

            # Stage 4: Shader update
            t3 = time.perf_counter()
            updated = self.update_shader_uniforms(shader_params)
            result['stages']['shader_update_ms'] = (time.perf_counter() - t3) * 1000
            result['shader_updated'] = updated

            result['success'] = True
            result['jones_invariant'] = {'real': jones.real, 'imag': jones.imag}
            result['shader_params'] = shader_params

        except Exception as e:
            logger.error(f"Update cycle failed: {e}", exc_info=True)
            result['error'] = str(e)

        result['total_ms'] = (time.perf_counter() - cycle_start) * 1000
        return result

    def get_performance_stats(self) -> Dict[str, float]:
        """Return compilation and update performance statistics."""
        if not self.compilation_times:
            return {'avg_compilation_ms': 0, 'p99_compilation_ms': 0}

        times = sorted(self.compilation_times)
        return {
            'avg_compilation_ms': np.mean(times),
            'p50_compilation_ms': np.percentile(times, 50),
            'p99_compilation_ms': np.percentile(times, 99),
            'max_compilation_ms': np.max(times),
            'cache_size': self.phasevm.cache_size[0] if hasattr(self.phasevm, 'cache_size') else 0,
        }
