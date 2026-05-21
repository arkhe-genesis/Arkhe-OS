#!/usr/bin/env python3
# =========================================================
# Executar Experimento Primakoff Gold
# =========================================================
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from primakoff.experiment import PrimakoffExperiment
from agi.agents import AGIAgent, AGIConsensus
from detectors.optical.fiber_sensor import FiberCherenkovSensor
from detectors.wifi.ruview_rf import RuViewRF

def main():
    print("=" * 70)
    print("ARKHE OS - EXPERIMENTO PRIMAKOFF GOLD")
    print("Substratos 387 -> 396")
    print("=" * 70)

    # Configuracao do experimento
    exp = PrimakoffExperiment(
        coil_length_m=3.0,
        coil_field_t=0.57,
        beam_energy_gev=50.0,
        days=100
    )

    result = exp.run_simulation()

    print("\n--- PARAMETROS DO EXPERIMENTO ---")
    print(f"Bobina: {result['coil_length_m']} m, {result['coil_field_t']} T")
    print(f"Feixe: {result['beam_energy_gev']} GeV, {result['days']} dias")
    print(f"Total de eletroes: {result['total_electrons']:.2e}")
    print(f"Probabilidade Primakoff: {result['primakoff_probability']:.2e}")

    print("\n--- RESULTADOS ---")
    print(f"Sinal esperado: {result['signal_events']} eventos")
    print(f"Fundo apos veto: {result['background_events']} eventos")
    print(f"Eventos observados: {result['observed_events']}")
    print(f"Significancia: {result['significance_sigma']} sigma")
    print(f"Descoberta: {'SIM' if result['discovery'] else 'EVIDENCIA'}")
    print(f"Phi_C: {result['phi_c']:.3f}")

    # Inicializar AGI para classificacao
    agents = [
        AGIAgent("AGI-MUON-01", "Global", "muon", "DSPy"),
        AGIAgent("AGI-ELEC-01", "Global", "electron", "LangGraph"),
        AGIAgent("AGI-PHOT-01", "Global", "photon", "AutoGen"),
        AGIAgent("AGI-CAL-01", "Global", "calorimetry", "Arkhe-Orch-OR"),
        AGIAgent("AGI-TRIG-01", "Global", "trigger", "MetaGPT"),
    ]
    consensus = AGIConsensus(agents)

    print("\n--- AGI CONSENSUS ---")
    test_event = {"amplitude_mV": 800, "integral_nVs": 5000, "width_ns": 55}
    classification = consensus.classify_event(test_event)
    print(f"Evento teste: {classification['class']} ({classification['avg_confidence']:.2f})")
    print(f"Quorum: {classification['quorum_reached']}")

    # Gerar selo
    seal = exp.get_seal()
    print(f"\n--- SELO CANONICO ---")
    print(f"Hash: {seal}")
    print(f"Status: CANONIZED")

if __name__ == "__main__":
    main()
