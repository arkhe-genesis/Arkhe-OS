#!/usr/bin/env python3
"""
parametric_quantum_clock.py — Clock quântico global sincronizado via ressonância paramétrica.
Implementa locking de fase distribuído para sincronização de nós da Wheeler Mesh.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import hashlib
import asyncio

class ClockState(Enum):
    """Estados do clock quântico."""
    FREE_RUNNING = auto()      # Oscilador livre, não sincronizado
    LOCKING = auto()           # Em processo de locking de fase
    PHASE_LOCKED = auto()      # Sincronizado com referência global
    DRIFTING = auto()          # Perdendo sincronia, requer re-lock

@dataclass
class ParametricOscillator:
    """Oscilador paramétrico para clock quântico."""
    node_id: str
    natural_frequency: float  # ω₀ em GHz
    parametric_drive_freq: float  # ω_d = 2ω₀ para ressonância paramétrica
    drive_amplitude: float  # Amplitude do drive paramétrico
    damping_rate: float  # γ em GHz
    noise_spectral_density: float  # S_φ em rad²/Hz

    # Estado interno
    phase: float = field(default=0.0)
    amplitude: float = field(default=1.0)
    _locked: bool = field(default=False)
    _last_update: float = field(default=0.0)

    def evolve(self, dt: float, reference_phase: Optional[float] = None,
               coupling_strength: float = 0.01) -> Dict[str, float]:
        """
        Evolui o oscilador via equação de Adler para locking de fase.

        dφ/dt = Δω - Δω_L sin(φ - φ_ref) + ξ(t)

        Onde Δω_L = coupling_strength × drive_amplitude é a largura de locking.
        """
        if reference_phase is None:
            # Free-running: apenas ruído de fase
            phase_noise = np.sqrt(2 * self.noise_spectral_density * dt) * np.random.randn()
            self.phase += (self.natural_frequency - self.parametric_drive_freq / 2) * dt + phase_noise
            self._locked = False
        else:
            # Tentar locking com referência
            phase_error = self.phase - reference_phase
            locking_range = coupling_strength * self.drive_amplitude

            # Equação de Adler com ruído
            dphase = (
                (self.natural_frequency - self.parametric_drive_freq / 2) * dt
                - locking_range * np.sin(phase_error) * dt
                + np.sqrt(2 * self.noise_spectral_density * dt) * np.random.randn()
            )
            self.phase += dphase

            # Verificar se está locked (phase error pequeno e estável)
            if abs(phase_error) < 0.1 and self._locked:
                self._locked = True
            elif abs(phase_error) < 0.05:
                self._locked = True  # Entrar em lock
            else:
                self._locked = False

        # Amplitude estabilizada por bombeamento paramétrico
        target_amp = np.sqrt(self.drive_amplitude / self.damping_rate)
        self.amplitude += (target_amp - self.amplitude) * self.damping_rate * dt

        self._last_update = time.time()

        return {
            'phase': self.phase % (2 * np.pi),
            'amplitude': self.amplitude,
            'locked': self._locked,
            'phase_error': phase_error if reference_phase is not None else None
        }

    def get_time(self) -> float:
        """Retorna tempo quântico estimado a partir da fase."""
        # Tempo = fase / frequência efetiva
        effective_freq = self.parametric_drive_freq / 2 if self._locked else self.natural_frequency
        return self.phase / effective_freq

class ParametricQuantumClock:
    """
    Clock quântico global sincronizado via ressonância paramétrica.
    Características:
    - Locking de fase distribuído via acoplamento paramétrico
    - Tolerância a ruído via squeezing paramétrico
    - Hierarquia de referência: núcleo galáctico → nós regionais → nós locais
    - Detecção e correção de drift via consenso de fase
    """

    def __init__(
        self,
        node_id: str,
        natural_frequency_ghz: float = 5.0,
        reference_hierarchy: Optional[List[str]] = None,  # IDs de nós de referência
        coupling_strength: float = 0.01,
        noise_spectral_density: float = 1e-6,  # rad²/Hz
        sync_interval_ms: float = 10.0,
        enable_squeezing: bool = True
    ):
        self.node_id = node_id
        self.reference_hierarchy = reference_hierarchy or []
        self.coupling_strength = coupling_strength
        self.sync_interval = sync_interval_ms / 1000.0  # Converter para segundos
        self.enable_squeezing = enable_squeezing

        # Oscilador local
        self.oscillator = ParametricOscillator(
            node_id=node_id,
            natural_frequency=natural_frequency_ghz * 1e9,  # Converter para rad/s
            parametric_drive_freq=2 * natural_frequency_ghz * 1e9,  # ω_d = 2ω₀
            drive_amplitude=1.0,  # Normalizado
            damping_rate=1e6,  # 1 MHz
            noise_spectral_density=noise_spectral_density
        )

        # Estado de sincronização
        self.clock_state = ClockState.FREE_RUNNING
        self.reference_phase: Optional[float] = None
        self.last_sync_time: float = 0.0

        # Métricas de clock
        self.clock_metrics = {
            'sync_attempts': 0,
            'successful_locks': 0,
            'phase_jitter_rad': 0.0,
            'frequency_stability': 0.0,  # Allan deviation estimate
            'time_since_last_sync': 0.0
        }

        # Buffer de fases para estimativa de jitter
        self.phase_history: List[float] = []
        self.max_history = 1000

        # Callbacks para eventos de sincronização
        self.sync_callbacks: List[Callable] = []

        # Task assíncrona para sincronização periódica
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False

        print(f"⏱️ ParametricQuantumClock initialized: {node_id} @ {natural_frequency_ghz}GHz")

    def _get_reference_phase(self) -> Optional[float]:
        """Obtém fase de referência da hierarquia (simulado)."""
        if not self.reference_hierarchy:
            return None

        # Em produção: receber fase via qhttp:// do nó de referência
        # Aqui: simular fase de referência com ruído controlado
        reference_node = self.reference_hierarchy[0]  # Referência primária

        # Fase de referência: tempo global + ruído pequeno
        global_time = time.time()
        reference_freq = self.oscillator.parametric_drive_freq / 2
        base_phase = (global_time * reference_freq) % (2 * np.pi)

        # Adicionar ruído de referência (menor que ruído local)
        reference_noise = np.sqrt(1e-7) * np.random.randn()  # Menor que noise_spectral_density
        return (base_phase + reference_noise) % (2 * np.pi)

    async def _sync_loop(self):
        """Loop de sincronização periódica."""
        while self._running:
            try:
                # Tentar sincronizar
                ref_phase = self._get_reference_phase()

                if ref_phase is not None:
                    self.clock_metrics['sync_attempts'] += 1

                    # Evoluir oscilador com referência
                    result = self.oscillator.evolve(
                        dt=self.sync_interval,
                        reference_phase=ref_phase,
                        coupling_strength=self.coupling_strength
                    )

                    # Atualizar estado
                    if result['locked'] and not self.oscillator._locked:
                        self.clock_state = ClockState.PHASE_LOCKED
                        self.clock_metrics['successful_locks'] += 1
                        self.reference_phase = ref_phase
                        self.last_sync_time = time.time()

                        # Notificar callbacks
                        for callback in self.sync_callbacks:
                            try:
                                callback({
                                    'type': 'clock_locked',
                                    'node_id': self.node_id,
                                    'reference': self.reference_hierarchy[0] if self.reference_hierarchy else None,
                                    'phase_error': result['phase_error'],
                                    'timestamp': time.time()
                                })
                            except Exception as e:
                                print(f"⚠️ Sync callback error: {e}")

                    elif not result['locked'] and self.clock_state == ClockState.PHASE_LOCKED:
                        self.clock_state = ClockState.DRIFTING
                        print(f"⚠️ Clock {self.node_id} losing lock — phase error: {result['phase_error']:.4f}")

                    # Atualizar métricas de jitter
                    self.phase_history.append(result['phase'])
                    if len(self.phase_history) > self.max_history:
                        self.phase_history.pop(0)

                    if len(self.phase_history) >= 100:
                        # Estimar jitter como desvio padrão da fase
                        jitter = np.std(self.phase_history[-100:])
                        self.clock_metrics['phase_jitter_rad'] = jitter

                        # Estimar estabilidade de frequência (Allan deviation simplificada)
                        if len(self.phase_history) >= 200:
                            tau = 100  # Amostras para averaging
                            avg1 = np.mean(self.phase_history[-2*tau:-tau])
                            avg2 = np.mean(self.phase_history[-tau:])
                            allan = np.sqrt(0.5 * (avg2 - avg1)**2)
                            self.clock_metrics['frequency_stability'] = allan

                else:
                    # Sem referência: evoluir free-running
                    self.oscillator.evolve(dt=self.sync_interval)
                    self.clock_state = ClockState.FREE_RUNNING

                # Atualizar tempo desde última sincronização
                self.clock_metrics['time_since_last_sync'] = (
                    time.time() - self.last_sync_time if self.last_sync_time > 0 else float('inf')
                )

                await asyncio.sleep(self.sync_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Sync loop error: {e}")
                await asyncio.sleep(self.sync_interval * 2)  # Backoff em erro

    async def start(self):
        """Inicia clock e loop de sincronização."""
        if self._running:
            return
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        print(f"🚀 ParametricQuantumClock started: {self.node_id}")

    async def stop(self):
        """Para clock gracefully."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        print(f"⏹️ ParametricQuantumClock stopped: {self.node_id}")

    def get_quantum_time(self) -> float:
        """Retorna tempo quântico atual com correção de fase se locked."""
        if self.clock_state == ClockState.PHASE_LOCKED and self.reference_phase is not None:
            # Usar fase locked para tempo mais preciso
            return self.oscillator.get_time()
        else:
            # Fallback para tempo livre (menos preciso)
            return self.oscillator.get_time()

    def get_clock_status(self) -> Dict[str, Any]:
        """Retorna status detalhado do clock."""
        return {
            'node_id': self.node_id,
            'state': self.clock_state.name,
            'current_phase': self.oscillator.phase % (2 * np.pi),
            'current_amplitude': self.oscillator.amplitude,
            'locked': self.oscillator._locked,
            'reference_hierarchy': self.reference_hierarchy,
            'metrics': self.clock_metrics,
            'quantum_time': self.get_quantum_time(),
            'estimated_uncertainty_ns': (
                self.clock_metrics['phase_jitter_rad'] /
                (self.oscillator.parametric_drive_freq / 2) * 1e9
                if self.clock_metrics['phase_jitter_rad'] > 0 else 0.0
            )
        }

    def register_sync_callback(self, callback: Callable[[Dict], None]):
        """Registra callback para eventos de sincronização."""
        self.sync_callbacks.append(callback)

    def compute_squeezing_parameter(self) -> float:
        """
        Calcula parâmetro de squeezing do clock.
        Para oscilador paramétrico: r ≈ (drive_amplitude - threshold) / (2 × damping)
        """
        if not self.enable_squeezing:
            return 0.0

        # Threshold para oscilação paramétrica
        threshold = self.oscillator.damping_rate / 2

        if self.oscillator.drive_amplitude > threshold:
            # Squeezing ativo
            excess_drive = self.oscillator.drive_amplitude - threshold
            r = excess_drive / (2 * self.oscillator.damping_rate)
            return min(2.0, r)  # Limitar squeezing prático
        return 0.0

    def get_squeezed_uncertainty(self) -> Dict[str, float]:
        """
        Retorna incertezas squeezed para fase e amplitude.
        Para squeezing paramétrico: Δφ × ΔA ≥ 1/4, com Δφ reduzido se r > 0
        """
        r = self.compute_squeezing_parameter()

        if r > 0:
            # Fase squeezed, amplitude anti-squeezed
            phase_uncertainty = 0.5 * np.exp(-r)  # Reduzida
            amp_uncertainty = 0.5 * np.exp(r)      # Aumentada
        else:
            # Estado coerente (SQL)
            phase_uncertainty = amp_uncertainty = 0.5

        return {
            'squeezing_parameter_r': r,
            'phase_uncertainty_rad': phase_uncertainty,
            'amplitude_uncertainty': amp_uncertainty,
            'uncertainty_product': phase_uncertainty * amp_uncertainty,
            'below_sql': phase_uncertainty < 0.5 if r > 0 else False
        }
