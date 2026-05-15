#!/usr/bin/env python3
"""
Substrato 9041 — Banco de Dados de Materiais 2D
Mapeia materiais bidimensionais conhecidos com ângulos críticos
e previsões de coerência Φ_C para aplicações quânticas.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

class MaterialClass(Enum):
    """Classes de materiais 2D."""
    TMD = "transition_metal_dichalcogenide"  # WSe₂, MoS₂, etc.
    GRAPHENE = "graphene_family"             # Graphene, hBN
    XENE = "xene"                            # Silicene, Germanene, Stanene
    PEROVSKITE = "perovskite_2d"             # BaTiO₃, etc.
    TOPOLOGICAL = "topological_insulator"    # Bi₂Se₃, Bi₂Te₃
    MAGNETIC_2D = "magnetic_2d"              # CrI3, Cr2Ge2Te6, etc.

@dataclass
class MoireMaterial:
    """Definição de um material 2D com propriedades de coerência moiré."""
    name: str
    formula: str                    # Fórmula química (ex: "WSe₂")
    material_class: MaterialClass
    lattice_constant_a: float      # Parâmetro de rede (Å)
    monolayer_bandgap_ev: float    # Bandgap da monocamada (eV)
    spin_orbit_coupling_ev: float  # Acoplamento spin-órbita (eV)

    # Propriedades moiré
    critical_angles: List[float]   # Ângulos de torção para coerência máxima (graus)
    phi_c_peak: float              # Φ_C máximo previsto para o ângulo ótimo
    valley_coherence_time_ps: float  # Tempo de coerência valley típico (ps)
    spin_coherence_time_ps: float    # Tempo de coerência spin típico (ps)

    # Aplicações
    applications: List[str] = field(default_factory=list)

    def compute_phi_c_at_angle(self, angle_degrees: float, temperature_k: float = 4.2) -> float:
        """
        Estima Φ_C para um ângulo de torção específico.

        Modelo simplificado:
        Φ_C(θ) = Φ_C_peak * exp(-(θ - θ_critical)² / (2 * σ²)) * f(T)
        onde f(T) = 1 - (T / T_decoherence)²
        """
        # Encontrar ângulo crítico mais próximo
        if not self.critical_angles:
            return 0.0

        closest_critical = min(self.critical_angles, key=lambda a: abs(a - angle_degrees))
        sigma = 0.5  # Largura gaussiana típica

        # Fator gaussiano
        gaussian = np.exp(-((angle_degrees - closest_critical) ** 2) / (2 * sigma**2))

        # Fator de temperatura (T_decoherence ~ 80K para TMDs)
        t_decoherence = 80.0  # K
        if temperature_k < t_decoherence:
            thermal_factor = 1.0 - (temperature_k / t_decoherence) ** 2
        else:
            thermal_factor = 0.0

        return self.phi_c_peak * gaussian * thermal_factor

    def compute_valley_conductance(self, angle_degrees: float, bias_mv: float = 10.0) -> float:
        """
        Estima condutância valley (em μS) para dada torção e bias.
        """
        phi_c = self.compute_phi_c_at_angle(angle_degrees)
        base_conductance = 10.0  # μS base
        # Condutância escala com Φ_C e inversamente com o bandgap
        return base_conductance * phi_c * (1.0 / (self.monolayer_bandgap_ev + 0.1))


# ============================================================================
# CATÁLOGO DE MATERIAIS 2D MAPEADOS
# ============================================================================

MATERIALS_2D_CATALOG: Dict[str, MoireMaterial] = {
    # ── TMDs (Dicalcogenetos de Metais de Transição) ──────────────
    "WSe2": MoireMaterial(
        name="Tungsten Diselenide",
        formula="WSe₂",
        material_class=MaterialClass.TMD,
        lattice_constant_a=3.28,
        monolayer_bandgap_ev=1.66,
        spin_orbit_coupling_ev=0.46,
        critical_angles=[0.0, 1.1, 3.5, 5.2, 60.0],
        phi_c_peak=0.998,
        valley_coherence_time_ps=15.0,
        spin_coherence_time_ps=120.0,
        applications=["valleytronics", "quantum_emitters", "moiré_excitons"],
    ),
    "MoS2": MoireMaterial(
        name="Molybdenum Disulfide",
        formula="MoS₂",
        material_class=MaterialClass.TMD,
        lattice_constant_a=3.16,
        monolayer_bandgap_ev=1.88,
        spin_orbit_coupling_ev=0.15,
        critical_angles=[0.0, 1.3, 4.2, 58.0],
        phi_c_peak=0.985,
        valley_coherence_time_ps=8.0,
        spin_coherence_time_ps=60.0,
        applications=["transistors", "photodetectors", "valley_hall_effect"],
    ),
    "WS2": MoireMaterial(
        name="Tungsten Disulfide",
        formula="WS₂",
        material_class=MaterialClass.TMD,
        lattice_constant_a=3.15,
        monolayer_bandgap_ev=2.05,
        spin_orbit_coupling_ev=0.43,
        critical_angles=[0.0, 1.2, 4.0, 59.0],
        phi_c_peak=0.990,
        valley_coherence_time_ps=12.0,
        spin_coherence_time_ps=100.0,
        applications=["quantum_emitters", "spin_valley_coupling"],
    ),
    "MoSe2": MoireMaterial(
        name="Molybdenum Diselenide",
        formula="MoSe₂",
        material_class=MaterialClass.TMD,
        lattice_constant_a=3.29,
        monolayer_bandgap_ev=1.55,
        spin_orbit_coupling_ev=0.18,
        critical_angles=[0.0, 1.4, 4.5, 57.0],
        phi_c_peak=0.978,
        valley_coherence_time_ps=7.0,
        spin_coherence_time_ps=50.0,
        applications=["photovoltaics", "leds", "valley_polarization"],
    ),

    # ── Grafeno e derivados ──────────────────────────────────────
    "graphene_hBN": MoireMaterial(
        name="Graphene on hBN (G/hBN)",
        formula="C (graphene) on BN (hexagonal boron nitride)",
        material_class=MaterialClass.GRAPHENE,
        lattice_constant_a=2.46,
        monolayer_bandgap_ev=0.0,  # Semimetal
        spin_orbit_coupling_ev=0.001,  # Muito fraco
        critical_angles=[0.0, 1.1, 30.0],
        phi_c_peak=0.992,
        valley_coherence_time_ps=3.0,
        spin_coherence_time_ps=200.0,  # Grafeno tem excelente coerência de spin
        applications=["spintronics", "superlattice_transport", "quantum_dots"],
    ),
    "twisted_bilayer_graphene": MoireMaterial(
        name="Twisted Bilayer Graphene (TBG)",
        formula="C (bilayer graphene)",
        material_class=MaterialClass.GRAPHENE,
        lattice_constant_a=2.46,
        monolayer_bandgap_ev=0.0,
        spin_orbit_coupling_ev=0.001,
        critical_angles=[1.08, 1.16],  # "Magic angles"
        phi_c_peak=0.999,
        valley_coherence_time_ps=5.0,
        spin_coherence_time_ps=250.0,
        applications=["superconductivity", "correlated_insulators", "magic_angle_physics"],
    ),

    # ── Xenes (monocamadas de elementos do grupo IV) ──────────────
    "silicene": MoireMaterial(
        name="Silicene",
        formula="Si (silicene)",
        material_class=MaterialClass.XENE,
        lattice_constant_a=3.86,
        monolayer_bandgap_ev=0.0,  # Semimetal com gap induzido por campo
        spin_orbit_coupling_ev=0.003,
        critical_angles=[0.0, 2.0, 5.0],
        phi_c_peak=0.950,
        valley_coherence_time_ps=2.0,
        spin_coherence_time_ps=50.0,
        applications=["topological_insulator", "field_effect_transistors"],
    ),
    "germanene": MoireMaterial(
        name="Germanene",
        formula="Ge (germanene)",
        material_class=MaterialClass.XENE,
        lattice_constant_a=4.06,
        monolayer_bandgap_ev=0.0,
        spin_orbit_coupling_ev=0.043,
        critical_angles=[0.0, 2.5, 5.5],
        phi_c_peak=0.960,
        valley_coherence_time_ps=3.0,
        spin_coherence_time_ps=80.0,
        applications=["quantum_spin_hall", "spintronics"],
    ),

    # ── Isolantes Topológicos ────────────────────────────────────
    "Bi2Se3": MoireMaterial(
        name="Bismuth Selenide",
        formula="Bi₂Se₃",
        material_class=MaterialClass.TOPOLOGICAL,
        lattice_constant_a=4.14,
        monolayer_bandgap_ev=0.30,  # Bulk gap
        spin_orbit_coupling_ev=0.40,  # Muito forte
        critical_angles=[0.0, 1.5, 3.0],
        phi_c_peak=0.970,
        valley_coherence_time_ps=20.0,
        spin_coherence_time_ps=500.0,  # Protegido topologicamente
        applications=["topological_quantum_computing", "spintronics", "majorana_fermions"],
    ),
    "Bi2Te3": MoireMaterial(
        name="Bismuth Telluride",
        formula="Bi₂Te₃",
        material_class=MaterialClass.TOPOLOGICAL,
        lattice_constant_a=4.38,
        monolayer_bandgap_ev=0.15,
        spin_orbit_coupling_ev=0.45,
        critical_angles=[0.0, 1.8, 3.2],
        phi_c_peak=0.975,
        valley_coherence_time_ps=18.0,
        spin_coherence_time_ps=450.0,
        applications=["thermoelectrics", "topological_insulators"],
    ),

    # ── Perovskitas 2D ───────────────────────────────────────────
    "BaTiO3_2D": MoireMaterial(
        name="Barium Titanate 2D",
        formula="BaTiO₃",
        material_class=MaterialClass.PEROVSKITE,
        lattice_constant_a=3.99,
        monolayer_bandgap_ev=3.20,
        spin_orbit_coupling_ev=0.10,
        critical_angles=[0.0, 2.2, 4.8],
        phi_c_peak=0.965,
        valley_coherence_time_ps=4.0,
        spin_coherence_time_ps=40.0,
        applications=["ferroelectrics", "nonlinear_optics", "piezoelectrics"],
    ),
    "CsPbBr3_2D": MoireMaterial(
        name="Cesium Lead Bromide 2D",
        formula="CsPbBr₃",
        material_class=MaterialClass.PEROVSKITE,
        lattice_constant_a=5.87,
        monolayer_bandgap_ev=2.36,
        spin_orbit_coupling_ev=1.20, # Forte acoplamento spin-órbita devido ao Pb
        critical_angles=[0.0, 1.7, 3.8],
        phi_c_peak=0.980,
        valley_coherence_time_ps=6.0,
        spin_coherence_time_ps=70.0,
        applications=["light_emission", "photovoltaics", "quantum_emitters"],
    ),

    # ── Dicalcogenetos Magnéticos 2D ──────────────────────────────
    "CrI3": MoireMaterial(
        name="Chromium Triiodide",
        formula="CrI₃",
        material_class=MaterialClass.MAGNETIC_2D,
        lattice_constant_a=6.86,
        monolayer_bandgap_ev=1.20,
        spin_orbit_coupling_ev=0.30,
        critical_angles=[0.0, 1.5, 4.2],
        phi_c_peak=0.988,
        valley_coherence_time_ps=10.0,
        spin_coherence_time_ps=300.0, # Excelentes propriedades de spin devido ao magnetismo
        applications=["magneto_optics", "spintronics", "magnonics"],
    ),
    "Cr2Ge2Te6": MoireMaterial(
        name="Chromium Germanium Telluride",
        formula="Cr₂Ge₂Te₆",
        material_class=MaterialClass.MAGNETIC_2D,
        lattice_constant_a=6.83,
        monolayer_bandgap_ev=0.74,
        spin_orbit_coupling_ev=0.25,
        critical_angles=[0.0, 2.1, 5.0],
        phi_c_peak=0.972,
        valley_coherence_time_ps=8.0,
        spin_coherence_time_ps=250.0,
        applications=["magnetic_memory", "spintronics"],
    ),
}
