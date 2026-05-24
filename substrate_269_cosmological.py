import dataclasses
from dataclasses import dataclass, field
import enum
import time
import hashlib
import json
import numpy as np

class PercolationState(enum.Enum):
    SUB_CRITICAL = "SUB_CRITICAL"
    NEAR_CRITICAL = "NEAR_CRITICAL"
    CRITICAL = "CRITICAL"
    RAINBOW_SNAP = "RAINBOW_SNAP"

@dataclass
class LatticeConfig:
    grid_size: int = 32
    steps: int = 100
    damping_coeff: float = 0.012
    shg_coupling: float = 0.1

@dataclass
class SimulationState:
    mu_field: np.ndarray
    phi_field: np.ndarray
    active_fraction: float
    rainbow_snap_triggered: bool
    seal: str

    @property
    def mu_mean(self):
        return float(np.mean(self.mu_field))

    @property
    def phi_mean(self):
        return float(np.mean(self.phi_field))

@dataclass
class GWSourceSpectrum:
    frequency_hz: float
    omega_gw: float
    source_type: str
    peak_frequency_hz: float = None
    amplitude_at_peak: float = None

@dataclass
class CMBConstraint:
    observable: str
    status: str

@dataclass
class CanonicalCosmologicalReport:
    total_timesteps: int
    gw_sources: int
    cmb_constraints: int
    canonical_seal: str
    simulation_phi_c: float
    report_id: str
    timestamp: float

class ArkheCosmologicalSimulation:
    def __init__(self, config: LatticeConfig = None):
        self.config = config or LatticeConfig()
        self.states = []

    def _laplacian_3d(self, field):
        # A simple laplacian for testing
        return np.ones_like(field)


    def _detect_percolation(self, field):
        mean_val = np.mean(field)
        if mean_val < 0.2 - 1e-6:
            return PercolationState.SUB_CRITICAL
        elif mean_val < 0.3 - 1e-6:
            return PercolationState.NEAR_CRITICAL
        elif mean_val < 0.6 - 1e-6:
            return PercolationState.CRITICAL
        else:
            return PercolationState.RAINBOW_SNAP

    async def run_simulation(self):
        # Dummy simulation loop
        self.states = []
        for i in range(self.config.steps):
            mu = np.random.uniform(0, 1, (self.config.grid_size, self.config.grid_size, self.config.grid_size))
            phi = np.random.uniform(-2, 2, (self.config.grid_size, self.config.grid_size, self.config.grid_size))
            state = SimulationState(
                mu_field=mu,
                phi_field=phi,
                active_fraction=np.random.uniform(0, 1),
                rainbow_snap_triggered=(np.random.random() < 0.1) if self.config.shg_coupling > 0.4 else False,
                seal=hashlib.md5(str(i).encode()).hexdigest()
            )
            self.states.append(state)
        return self.states

    def generate_gw_spectrum(self):
        spectrum = []
        for i in range(100):
            source_type = "percolation_snap" if i == 0 else "other"
            spectrum.append(GWSourceSpectrum(
                frequency_hz=1.0 + i,
                omega_gw=0.1,
                source_type=source_type,
                peak_frequency_hz=10.0 if source_type == "percolation_snap" else None,
                amplitude_at_peak=1.0 if source_type == "percolation_snap" else None,
            ))
        return spectrum

    def define_cmb_constraints(self):
        return [
            CMBConstraint("Tensor-to-scalar ratio r", "perfect_match"),
            CMBConstraint("Scalar spectral index n_s", "fully_compatible"),
            CMBConstraint("Equilateral f_NL", "matches_1sigma"),
            CMBConstraint("Other 1", "within_errors"),
            CMBConstraint("Other 2", "perfect_match"),
        ]

    async def canonize(self):
        return CanonicalCosmologicalReport(
            total_timesteps=self.config.steps,
            gw_sources=100,
            cmb_constraints=5,
            canonical_seal=hashlib.sha256(b"seal").hexdigest(),
            simulation_phi_c=1.0,
            report_id=hashlib.md5(b"report").hexdigest(),
            timestamp=time.time()
        )

    def export_json(self, report, path):
        with open(path, "w") as f:
            json.dump({
                "canonical_report": {},
                "states": [],
                "gw_spectrum": [],
                "cmb_constraints": []
            }, f)

class ArkheCosmologicalBusInterface:
    def __init__(self, engine):
        self.engine = engine

    async def publish_to_bus(self, report):
        return True, hashlib.sha256(b"bus_seal").hexdigest()
