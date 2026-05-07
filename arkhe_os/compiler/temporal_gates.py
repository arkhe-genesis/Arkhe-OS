import numpy as np

class TemporalOp:
    def __init__(self, op_type, ctc_ids, estimated_duration, metadata=None):
    def __init__(self, op_type: str, ctc_ids: list[int], estimated_duration: float, metadata: dict = None):
        self.op_type = op_type
        self.ctc_ids = ctc_ids
        self.estimated_duration = estimated_duration
        self.metadata = metadata or {}

    def compile_to_pulse_sequence(self, hardware_config: dict) -> list[dict]:
        raise NotImplementedError

class TemporalCircuit:
    def __init__(self):
        self.gates = []

    def add_gate(self, gate: TemporalOp):
        self.gates.append(gate)

    def compile_to_hardware(self, hardware_config: dict) -> list[dict]:
        all_pulses = []
        for gate in self.gates:
            if hasattr(gate, 'compile_to_pulse_sequence'):
                all_pulses.extend(gate.compile_to_pulse_sequence(hardware_config))
        return all_pulses
        sequence = []
        for gate in self.gates:
            sequence.extend(gate.compile_to_pulse_sequence(hardware_config))
        return sequence

class FloquetStabilizeGate(TemporalOp):
    """
    Porta que aplica driving periódico de Floquet para estabilizar
    qubits temporais durante operações sensíveis à decoerência.

    Uso típico: envolver operações de longa duração ou estados
    meta-estáveis que requerem proteção temporal.
    """
    def __init__(
        self,
        target_ctc: int,
        duration: float,
        driving_freq: float,
        rabi_freq: float,
        phase: float = 0.0,
        envelope_type: str = "constant"  # "constant", "gaussian", "square"
    ):
        super().__init__(
            op_type="FLOQUET_STABILIZE",
            ctc_ids=[target_ctc],
            estimated_duration=duration,
            metadata={
                "driving_frequency_Hz": driving_freq / (2 * np.pi),
                "rabi_frequency_Hz": rabi_freq / (2 * np.pi),
                "phase_offset_rad": phase,
                "envelope": envelope_type,
                "floquet_period_s": 2 * np.pi / driving_freq if driving_freq > 0 else float('inf'),
                "expected_coherence_gain": np.exp((rabi_freq/driving_freq)**2 / 2) if driving_freq > 0 else 1.0
                "floquet_period_s": 2 * np.pi / driving_freq,
                "expected_coherence_gain": np.exp((rabi_freq/driving_freq)**2 / 2)
            }
        )

    def compile_to_pulse_sequence(self, hardware_config: dict) -> list[dict]:
        """
        Compila a porta de Floquet para sequência de pulsos
        compatível com hardware de campo magnético.
        """
        pulses = []
        dt = hardware_config.get("time_resolution", 1e-9)  # 1 ns padrão
        n_steps = int(self.estimated_duration / dt)

        for step in range(n_steps):
            t = step * dt
            amplitude = self._envelope_function(t, self.metadata["envelope"])
            phase = self.metadata["phase_offset_rad"] + self.metadata["driving_frequency_Hz"] * 2*np.pi * t

            pulses.append({
                "channel": f"mag_field_ctc_{self.ctc_ids[0]}",
                "time_ns": t * 1e9,
                "amplitude_A": amplitude,
                "frequency_Hz": self.metadata["driving_frequency_Hz"],
                "phase_rad": phase,
                "purpose": "floquet_stabilization"
            })

        return pulses

    def _envelope_function(self, t: float, envelope_type: str) -> float:
        """Funções de envelope para shaping do driving."""
        if envelope_type == "constant":
            return 1.0
        elif envelope_type == "gaussian":
            sigma = self.estimated_duration / 6  # 99.7% em ±3σ
            return np.exp(-0.5 * ((t - self.estimated_duration/2) / sigma)**2)
        elif envelope_type == "square":
            return 1.0 if 0 <= t <= self.estimated_duration else 0.0
        return 1.0  # Fallback

class TemporalCircuit:
    def __init__(self):
        self.gates = []

    def add_gate(self, gate: TemporalOp):
        self.gates.append(gate)

    def compile_to_hardware(self, hardware_config: dict) -> list[dict]:
        all_pulses = []
        for gate in self.gates:
            if hasattr(gate, 'compile_to_pulse_sequence'):
                all_pulses.extend(gate.compile_to_pulse_sequence(hardware_config))
        return all_pulses
        return 1.0  # Fallback
