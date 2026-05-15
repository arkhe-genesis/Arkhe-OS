#!/usr/bin/env python3
"""
Substrato 9041 — Ponte Arkhe-Moiré
Integra simulações de canais spin‑valley com TemporalChain e Φ_C Bus.
"""

import asyncio, hashlib, json, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .materials_2d_db import MATERIALS_2D_CATALOG, MoireMaterial
from .spin_valley_simulator import MaterialsMapper
from .spin_valley_simulator import SpinValleySimulator, SpinValleyState

@dataclass
class SimulationReport:
    """Relatório de simulação ancorado na TemporalChain."""
    simulation_id: str
    material: str
    angle_degrees: float
    critical_angles_found: List[float]
    phi_c_map: Dict
    temporal_seal: Optional[str] = None
    phi_c_peak_achieved: float = 0.0

class MoireArkheBridge:
    """
    Ponte entre as simulações moiré e o Safe Core da Arkhe.
    Ancora cada simulação na TemporalChain e publica métricas no Φ_C Bus.
    """

    def __init__(self, temporal_chain=None, phi_bus=None):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.simulation_history: List[SimulationReport] = []

    async def run_and_anchor_simulation(
        self,
        material_key: str,
        angle_degrees: float,
        temperature_k: float = 4.2,
        use_qnc: bool = False,
    ) -> SimulationReport:
        """Executa simulação e ancora resultados na TemporalChain."""
        material = MATERIALS_2D_CATALOG.get(material_key)
        if not material:
            raise ValueError(f"Material não encontrado: {material_key}")

        sim = SpinValleySimulator(material, angle_degrees)
        phi_c_map = sim.generate_coherence_map((1.0, temperature_k * 2))

        if use_qnc:
            critical_angles = sim.optimize_critical_angles_qnc()
        else:
            critical_angles = sim.find_critical_angles()

        simulation_id = hashlib.sha3_256(
            f"{material_key}:{angle_degrees}:{time.time()}".encode()
        ).hexdigest()[:16]

        report = SimulationReport(
            simulation_id=simulation_id,
            material=material.name,
            angle_degrees=angle_degrees,
            critical_angles_found=critical_angles,
            phi_c_map=phi_c_map,
            phi_c_peak_achieved=material.compute_phi_c_at_angle(angle_degrees, temperature_k),
        )

        # Ancorar na TemporalChain
        if self.temporal:
            report.temporal_seal = await self.temporal.anchor_event(
                "moire_simulation_completed", {
                    "material": material_key,
                    "angle": angle_degrees,
                    "phi_c_peak": report.phi_c_peak_achieved,
                    "critical_angles": critical_angles,
                    "timestamp": time.time(),
                }
            )

        # Publicar no Φ_C Bus
        if self.phi_bus:
            self.phi_bus.sync_phi_c(
                f"moire_{material_key}",
                report.phi_c_peak_achieved,
            )

        self.simulation_history.append(report)
        return report

    def get_best_materials_for_phi_c(self, min_phi_c: float = 0.99) -> List[Dict]:
        """Retorna os melhores materiais para alcançar determinado Φ_C."""
        mapper = MaterialsMapper()
        candidates = mapper.find_by_phi_c_range(min_phi_c, 1.0)
        results = []
        for name, phi_c in candidates:
            mat_key = next((k for k, v in MATERIALS_2D_CATALOG.items() if v.name == name), None)
            if mat_key:
                mat = MATERIALS_2D_CATALOG[mat_key]
                results.append({
                    "material": name,
                    "phi_c_peak": phi_c,
                    "critical_angles": mat.critical_angles,
                    "applications": mat.applications,
                })
        return results
