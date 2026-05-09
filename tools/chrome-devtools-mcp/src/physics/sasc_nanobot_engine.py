import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class NanoBot:
    id: str
    position: np.ndarray
    state: str  # 'LATENT', 'ACTIVE', 'DEPLOYED'
    payload: float # Drug concentration or binding strength
    phase: float = 0.0
    voltage: float = 0.0
    natural_frequency: float = 10.0 # Hz
    last_wake_time: float = 0.0
    is_waking: bool = False

class SwarmPMIC:
    """
    PMIC for the NanoBot Swarm.
    Derived from Sharpe Threshold and Graphene Supercapacitor properties.
    """
    def __init__(self, v_th: float = 0.48, i_leak: float = 10e-12, c_store: float = 1e-12):
        self.v_th = v_th      # V (Threshold Voltage)
        self.i_leak = i_leak  # A (Leakage Current)
        self.c_store = c_store # F (Storage Capacitance)

    def calculate_charge_time(self, p_in_watts: float) -> float:
        """
        t_charge = (C * V_th) / (I_in - I_leak)
        """
        i_in = p_in_watts / self.v_th
        if i_in <= self.i_leak:
            return float('inf')
        return (self.c_store * self.v_th) / (i_in - self.i_leak)

class DNAOrigamiCompiler:
    """
    Compiles geometry specs into DNA folding sequences.
    Simulates 'Structure is Computation' paradigm.
    """
    def compile_structure(self, target_shape: str) -> Dict[str, Any]:
        # Simple mapping for simulation
        shapes = {
            "CAGE": "ATGC...[folded_as_cage]",
            "SHELL": "GCAT...[folded_as_shell]",
            "GRIPPER": "TATA...[folded_as_gripper]"
        }
        return {
            "sequence": shapes.get(target_shape, "UNKNOWN"),
            "stability_score": 0.98,
            "resonance_freq_mhz": 40.0 # Acoustic resonance
        }

class NanoBotSwarm:
    """
    Simulates a swarm of Intracellular Phase Nodes (Layer 0 Actuators).
    Supports Exogenous (Magnetic/NIR) and Endogenous (pH) triggers.
    Implements Kuramoto Sync via RF (441 MHz).
    """
    def __init__(self, count: int = 1000):
        self.count = count
        self.bots = [
            NanoBot(
                id=f"bot_{i}",
                position=np.random.rand(3),
                state='LATENT',
                payload=0.0,
                phase=np.random.uniform(0, 2 * np.pi),
                natural_frequency=10.0 + np.random.normal(0, 0.1) # 10Hz +/- 1%
            ) for i in range(count)
        ]
        self.compiler = DNAOrigamiCompiler()
        self.pmic = SwarmPMIC()
        self.time = 0.0

    def apply_exogenous_trigger(self, trigger_type: str, intensity: float):
        """
        Activates bots via global Maestro signal (Magnetic/Acoustic/NIR).
        """
        for bot in self.bots:
            if trigger_type == "MAGNETIC":
                # Magnetic gradient pulls bots
                bot.position += np.random.normal(0, 0.01 * intensity, 3)
            elif trigger_type == "NIR":
                # Near-Infrared light triggers deployment
                bot.state = 'DEPLOYED' if intensity > 0.8 else 'ACTIVE'

    def check_endogenous_triggers(self, local_ph: float, presence_markers: List[str]):
        """
        Bots activate locally based on tissue dissonance (acidity) or logic gates.
        """
        activated_count = 0
        for bot in self.bots:
            # Dissonance detection: Acidic environment (pH < 6.8)
            if local_ph < 6.8:
                bot.state = 'ACTIVE'
                bot.payload = 1.0 # Release drug
                activated_count += 1
            # Logic gate: 'Marker_A' AND 'Marker_B'
            elif "MARKER_A" in presence_markers and "MARKER_B" in presence_markers:
                bot.state = 'ACTIVE'
                activated_count += 1
        return activated_count

    def update_iesr_dynamics(self, dt: float, p_in_watts: float):
        """
        Simulates the Charge-Wake cycle (IESR).
        """
        self.time += dt
        for bot in self.bots:
            # Charge capacitor
            i_in = p_in_watts / self.pmic.v_th
            dv = (i_in - self.pmic.i_leak) * dt / self.pmic.c_store
            bot.voltage = min(self.pmic.v_th, bot.voltage + dv)

            # Wake up if threshold reached
            if bot.voltage >= self.pmic.v_th:
                bot.is_waking = True
                bot.voltage = 0.0 # Discharge
                bot.last_wake_time = self.time
            else:
                bot.is_waking = False

    def distributed_kuramoto_sync(self, K: float, dt: float):
        """
        Implements Kuramoto phase coupling for waking bots.
        Theta_i_dot = omega_i + (K/N) * sum(sin(theta_j - theta_i))
        """
        waking_bots = [b for b in self.bots if b.is_waking]
        if not waking_bots:
            # Passive phase evolution
            for bot in self.bots:
                bot.phase = (bot.phase + 2 * np.pi * bot.natural_frequency * dt) % (2 * np.pi)
            return

        phases = np.array([b.phase for b in waking_bots])
        avg_phase = np.angle(np.mean(np.exp(1j * phases)))

        for bot in self.bots:
            # Natural evolution
            d_theta = 2 * np.pi * bot.natural_frequency * dt
            # Coupling term (only strong when waking)
            # Use mean field for all if at least some are waking
            d_theta += K * np.sin(avg_phase - bot.phase) * dt

            bot.phase = (bot.phase + d_theta) % (2 * np.pi)

    def get_order_parameter(self) -> float:
        """
        Calculates R(t) = |(1/N) * sum(exp(i*theta))|
        """
        phases = np.array([b.phase for b in self.bots])
        r = np.abs(np.mean(np.exp(1j * phases)))
        return float(r)

    def status(self) -> Dict[str, Any]:
        states = [b.state for b in self.bots]
        return {
            "total_bots": self.count,
            "active": states.count('ACTIVE'),
            "deployed": states.count('DEPLOYED'),
            "latent": states.count('LATENT'),
            "avg_payload": float(np.mean([b.payload for b in self.bots])),
            "order_parameter": self.get_order_parameter(),
            "avg_voltage": float(np.mean([b.voltage for b in self.bots]))
        }
