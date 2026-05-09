import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict
from arkhe_os.temporal.floquet_driven_qubit import FloquetParameters, FloquetStabilizedQubit

@dataclass
class CTCNode:
    ctc_id: int
    natural_frequency: float
    gamma_0: float
    phase_offset: float = 0.0

class CrossCTCSynchronizer:
    """
    Substrate 284: Cross-CTC Floquet Synchronization
    Synchronizes multiple Time Crystals (CTCs) via a shared Floquet driving mechanism,
    enabling distributed quantum operations with global coherence.
    """
    def __init__(self, nodes: List[CTCNode], shared_driving_params: FloquetParameters):
        self.nodes = nodes
        self.shared_driving_params = shared_driving_params
        self.stabilized_nodes: Dict[int, FloquetStabilizedQubit] = {}

        self._initialize_nodes()

    def _initialize_nodes(self):
        for node in self.nodes:
            # Each node experiences the shared driving field but might have local phase variations
            local_params = FloquetParameters(
                omega_d=self.shared_driving_params.omega_d,
                omega_R=self.shared_driving_params.omega_R,
                phase_offset=self.shared_driving_params.phase_offset + node.phase_offset,
                envelope=self.shared_driving_params.envelope
            )
            self.stabilized_nodes[node.ctc_id] = FloquetStabilizedQubit(
                params=local_params,
                gamma_0=node.gamma_0
            )

    def global_coherence_metric(self, operation_time: float) -> float:
        """
        Calculates the global coherence metric across all synchronized CTCs.
        The global coherence is bounded by the most decoherent node in the synchronized state.
        """
        if not self.stabilized_nodes:
            return 0.0

        individual_t2s = []
        for ctc_id, qubit in self.stabilized_nodes.items():
            t2 = qubit.coherence_time()
            individual_t2s.append(t2)

        # The effective global T2 is dominated by the shortest T2 in the network
        min_t2 = min(individual_t2s)

        if min_t2 == float('inf'):
            return 1.0

        # Simple exponential decay model for global coherence based on the bottleneck
        global_phi = np.exp(-operation_time / min_t2)
        return float(global_phi)

    def synchronization_fidelity(self) -> float:
        """
        Calculates the phase synchronization fidelity among the CTC network.
        Perfect synchronization = 1.0.
        """
        if len(self.nodes) < 2:
            return 1.0

        phases = [node.phase_offset for node in self.nodes]
        # Calculate the phase order parameter (Kuramoto model style)
        order_parameter = np.abs(np.mean(np.exp(1j * np.array(phases))))
        return float(order_parameter)

    def generate_shared_pulse_sequence(self, duration: float, dt: float = 1e-9) -> List[Dict]:
        """
        Generates the shared magnetic pulse sequence broadcast to all CTCs.
        """
        pulses = []
        n_steps = int(duration / dt)

        for step in range(n_steps):
            t = step * dt
            # Use base instantaneous coupling logic but broadcast
            amplitude = 1.0 # Envelope function would go here
            if self.shared_driving_params.envelope:
                amplitude = self.shared_driving_params.envelope(t)

            phase = self.shared_driving_params.phase_offset + self.shared_driving_params.omega_d * t

            pulses.append({
                "time_ns": t * 1e9,
                "amplitude": amplitude,
                "frequency_Hz": self.shared_driving_params.omega_d / (2 * np.pi),
                "phase_rad": phase,
                "purpose": "shared_floquet_driving"
            })

        return pulses
