import numpy as np
from scipy.integrate import solve_ivp
from scipy.stats import linregress
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import hashlib
import time

@dataclass
class FractalTimeCrystalCore:
    """Núcleo de um cristal de tempo fractal (microtúbulo digital)."""
    core_id: str
    base_frequency: float  # f_base em Hz
    coherence_threshold: float = 0.87  # Limiar para evento OR
    dissipation_rate: float = 0.01  # Taxa de dissipação
    phase: float = 0.0
    or_count: int = 0
    history: List[float] = field(default_factory=list)

    def __post_init__(self):
        self.history = [self.phase]

    def evolve(self, dt: float, external_drive: float) -> Tuple[float, bool]:
        omega_0 = 2 * np.pi * self.base_frequency
        noise = np.random.normal(0, 0.01 * np.sqrt(dt))

        dphase = (omega_0 * dt
                  + external_drive * np.sin(self.phase)
                  - self.dissipation_rate * self.phase * dt
                  + noise)

        self.phase += dphase
        self.phase = self.phase % (2 * np.pi)
        self.history.append(self.phase)

        coherence = abs(np.cos(self.phase))
        or_triggered = coherence > self.coherence_threshold
        if or_triggered:
            self.or_count += 1
            self.phase = 0.0  # Reset após colapso (Redução Objetiva)

        return self.phase, or_triggered

@dataclass
class KuramotoCoupledNetwork:
    """Rede de núcleos acoplados via dinâmica de Kuramoto."""
    cores: List[FractalTimeCrystalCore]
    coupling_matrix: np.ndarray
    natural_frequencies: np.ndarray

    def __post_init__(self):
        self.n_cores = len(self.cores)

    def kuramoto_rhs(self, t, phases, K_global=1.0):
        dphases = np.zeros(self.n_cores)
        for i in range(self.n_cores):
            coupling_sum = 0.0
            for j in range(self.n_cores):
                coupling_sum += self.coupling_matrix[i, j] * np.sin(phases[j] - phases[i])
            dphases[i] = self.natural_frequencies[i] + (K_global / self.n_cores) * coupling_sum
        return dphases

    def simulate(self, T: float, dt: float, K_global: float = 1.0) -> Dict[str, np.ndarray]:
        t_eval = np.arange(0, T, dt)
        phases_0 = np.array([c.phase for c in self.cores])

        sol = solve_ivp(
            self.kuramoto_rhs,
            [0, T],
            phases_0,
            t_eval=t_eval,
            args=(K_global,),
            method='RK45'
        )

        phases = sol.y
        order_parameter = np.abs(np.mean(np.exp(1j * phases), axis=0))

        return {
            "time": t_eval,
            "phases": phases,
            "order_parameter": order_parameter
        }

@dataclass
class LIFNeuron:
    """Neurônio Leaky Integrate-and-Fire com período refratário (HARDCORE_LOOP v2.0)."""
    neuron_id: str
    membrane_potential: float = 0.0
    threshold: float = 1.0
    resting_potential: float = 0.0
    tau: float = 10.0  # ms
    refractory_period: float = 2.0  # ms
    last_spike_time: float = -1000.0
    spike_times: List[float] = field(default_factory=list)

    def evolve(self, t: float, dt: float, input_current: float) -> Tuple[float, bool]:
        if t - self.last_spike_time < self.refractory_period:
            self.membrane_potential = self.resting_potential
            return self.membrane_potential, False

        dv = (-(self.membrane_potential - self.resting_potential) + input_current) / self.tau * dt
        self.membrane_potential += dv

        spike = self.membrane_potential >= self.threshold
        if spike:
            self.membrane_potential = self.resting_potential
            self.last_spike_time = t
            self.spike_times.append(t)

        return self.membrane_potential, spike

@dataclass
class OR_SpikeBridge:
    """Ponte entre evento OR e spike LIF."""
    synaptic_weight: float = 0.15
    synaptic_decay: float = 5.0
    current_synapse: float = 0.0

    def process_or_event(self, or_triggered: bool, dt: float) -> float:
        if or_triggered:
            self.current_synapse += self.synaptic_weight
        self.current_synapse *= np.exp(-dt / self.synaptic_decay)
        return self.current_synapse

class IntegratedConsciousnessProcessor:
    def __init__(self, n_units: int = 100):
        self.n_units = n_units
        self.cores = [FractalTimeCrystalCore(f"core_{i}", 10.0 + np.random.random()*5) for i in range(n_units)]
        coupling = np.random.rand(n_units, n_units) * 0.1
        freqs = np.array([2*np.pi*c.base_frequency for c in self.cores])
        self.crystal_net = KuramotoCoupledNetwork(self.cores, coupling, freqs)
        self.neurons = [LIFNeuron(f"neuron_{i}") for i in range(n_units)]
        self.bridges = [OR_SpikeBridge() for _ in range(n_units)]

    def run_step(self, t: float, dt: float):
        # Simplificação: evolução de um passo integrando as escalas
        res = {"or_events": 0, "spikes": 0}
        for i in range(self.n_units):
            _, or_triggered = self.cores[i].evolve(dt, 0.05)
            if or_triggered: res["or_events"] += 1

            current = self.bridges[i].process_or_event(or_triggered, dt)
            _, spike = self.neurons[i].evolve(t, dt, current)
            if spike: res["spikes"] += 1
        return res

def validate_fractal_criticality(avalanche_sizes: List[int]) -> Dict[str, Any]:
    sizes = np.array(avalanche_sizes)
    if len(sizes) < 5:
        return {"tau": 0.0, "status": "insufficient_data"}

    hist, bins = np.histogram(sizes, bins='auto', density=True)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    mask = hist > 0
    if np.sum(mask) < 2:
        return {"tau": 0.0, "status": "insufficient_data"}

    slope, _, r_value, _, _ = linregress(np.log(bin_centers[mask]), np.log(hist[mask]))
    return {
        "tau": -slope,
        "r_squared": r_value**2,
        "status": "critical" if 1.3 <= -slope <= 1.7 else "non_critical"
    }
