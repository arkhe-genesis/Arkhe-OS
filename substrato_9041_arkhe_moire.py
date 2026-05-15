#!/usr/bin/env python3
"""Demonstração do Substrato 9041 — Mapeamento de Materiais 2D e Simulação Spin‑Valley."""

import asyncio
import numpy as np
from arkhe_moire.materials_2d_db import MATERIALS_2D_CATALOG
from arkhe_moire.spin_valley_simulator import MaterialsMapper
from arkhe_moire.spin_valley_simulator import SpinValleySimulator, SpinValleyState
from arkhe_moire.bridge import MoireArkheBridge

async def demo():
    print("═" * 70)
    print("ARKHE-MOIRÉ — Spin‑Valley Coherence Demo")
    print("═" * 70)

    # 1. Mapeamento de materiais existentes
    print("\n📊 MATERIAIS 2D CATALOGADOS:")
    mapper = MaterialsMapper()

    print("\n🔹 Melhores para spintrônica (Φ_C > 0.95):")
    spintronics = mapper.find_best_for_application("spintronics", min_phi_c=0.95)
    for name, phi_c in spintronics[:5]:
        mat_key = None
        for key, m in MATERIALS_2D_CATALOG.items():
            if m.name == name:
                mat_key = key
                break
        if mat_key:
            mat = MATERIALS_2D_CATALOG[mat_key]
            print(f"   • {name}: Φ_C={phi_c:.4f} | τ_spin={mat.spin_coherence_time_ps}ps")

    print("\n🔹 Materiais com Φ_C > 0.99:")
    high_phi = mapper.find_by_phi_c_range(0.99, 1.0)
    for name, phi_c in high_phi:
        print(f"   • {name}: Φ_C_peak={phi_c:.4f}")

    print("\n🔹 Melhores tempos de coerência spin (>100ps):")
    spin_coherent = mapper.find_by_coherence_time(100.0, "spin")
    for name, time_ps in spin_coherent:
        print(f"   • {name}: τ_spin={time_ps}ps")

    # 2. Simulação de canais spin‑valley para WSe₂
    print("\n🧬 SIMULAÇÃO SPIN‑VALLEY — WSe₂ @ 1.1°:")
    wse2 = MATERIALS_2D_CATALOG["WSe2"]
    sim = SpinValleySimulator(wse2, angle_degrees=1.1)

    # Encontrar ângulos críticos (base vs QNC)
    print(f"   • Ângulos críticos (Modelo Base): {sim.find_critical_angles()}")
    print(f"   • Ângulos críticos otimizados (QNC): {sim.optimize_critical_angles_qnc()}")

    # Calcular dispersão
    k_points = np.linspace(0, 1, 10).reshape(-1, 1) * np.ones((1, 2)) * 0.5
    dispersion = sim.compute_spin_valley_dispersion(k_points)
    print(f"   • Gap de energia (k=0): {dispersion[0, 1] - dispersion[0, 0]:.4f} eV")

    # Simular propagação
    initial = SpinValleyState(
        position=(0, 0),
        spin=complex(1, 0),
        valley=complex(1, 0),
        coherence=0.998,
        energy_ev=0.0,
    )
    states = sim.simulate_propagation(initial, time_steps=50)
    final_coherence = states[-1].coherence
    print(f"   • Coerência após 50fs: {final_coherence:.4f}")

    # 3. Gerar mapa de coerência
    coherence_map = sim.generate_coherence_map((1.0, 80.0))
    print(f"\n🗺️  MAPA DE COERÊNCIA GERADO:")
    print(f"   • Material: {coherence_map['material']}")
    print(f"   • Φ_C peak: {coherence_map['phi_c_peak']}")
    print(f"   • Critical angles: {coherence_map['critical_angles']}")
    print(f"   • Grid: {len(coherence_map['angles'])} angles × {len(coherence_map['temperatures'])} temps")

    # 4. Bridge com Arkhe (simulado)
    print(f"\n🔗 ANCORANDO NA TEMPORALCHAIN:")
    bridge = MoireArkheBridge()
    report = await bridge.run_and_anchor_simulation("WSe2", 1.1, use_qnc=True)
    print(f"   • Simulation ID: {report.simulation_id}")
    print(f"   • Φ_C peak achieved: {report.phi_c_peak_achieved:.4f}")
    print(f"   • Temporal seal: {report.temporal_seal or 'simulated'}")

    # 5. Dicalcogenetos Magnéticos & Perovskitas
    print(f"\n🔗 TESTANDO NOVOS MATERIAIS - CrI3:")
    cri3 = MATERIALS_2D_CATALOG["CrI3"]
    sim_cri3 = SpinValleySimulator(cri3, angle_degrees=1.5)
    print(f"   • Ângulos críticos (QNC) para CrI3: {sim_cri3.optimize_critical_angles_qnc()}")

    print("\n✅ Demo completed")

if __name__ == "__main__":
    asyncio.run(demo())
