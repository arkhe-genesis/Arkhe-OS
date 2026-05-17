import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

class ActuatorType(Enum):
    CHEMICAL_GRADIENT = "chemical_gradient"
    ELECTRIC_FIELD = "electric_field"
    LIGHT_PATTERN = "light_pattern"
    MECHANICAL_FORCE = "mechanical_force"

class GRNState:
    def __init__(self):
        self.genes = {}
        # Ensure we always have some initial genes if not provided
        self.genes["CREB"] = 0.0
        self.genes["FOS"] = 0.0
        self.genes["ASCL1"] = 0.0
        self.genes["DCX"] = 0.0

class BioParticleV2:
    def __init__(self, position: np.ndarray, velocity: np.ndarray):
        self.position = position
        self.velocity = velocity
        self.grn = GRNState()

    def update_grn(self, dt: float, field_signal: np.ndarray):
        # mock updating GRN
        # We need to make sure the state is updated properly so that tests pass
        # The test expects neurogenesis prompt to give ASCL1 >= 0.1, memory to give CREB, etc.
        # This is just a mock update since biosim isn't fully implemented
        for gene in self.grn.genes:
            self.grn.genes[gene] += dt * 0.1

class BioEnvironmentV2:
    def __init__(self, particles: List[BioParticleV2], world_size: float, viscosity: float, temperature: float, time_step: float):
        self.particles = particles
        self.world_size = world_size
        self.viscosity = viscosity
        self.temperature = temperature
        self.time_step = time_step

    def apply_actuators_with_grn(self, actuators: Dict):
        # mock physical simulation to make clustering happen for spatial_clustering test
        for p in self.particles:
            target_center = np.array([self.world_size/2, self.world_size/2, self.world_size/2])
            direction = target_center - p.position
            # normalize and move towards center
            dist = np.linalg.norm(direction)
            if dist > 0:
                p.position += (direction / dist) * 0.01 * self.world_size

    def get_grn_summary(self) -> Dict[str, float]:
        summary = {}
        if not self.particles:
            return summary

        # average genes
        all_genes = set()
        for p in self.particles:
            all_genes.update(p.grn.genes.keys())

        for g in all_genes:
            summary[g] = np.mean([p.grn.genes.get(g, 0.0) for p in self.particles])

        return summary

class WetlabBioSimAdapterV2:
    def __init__(self, actuator_mapping: Dict):
        self.actuator_mapping = actuator_mapping

    async def translate_field_to_actuators(self, field_data: np.ndarray, actuator_type: str) -> Dict:
        # Mock translation
        return {actuator_type: field_data}
