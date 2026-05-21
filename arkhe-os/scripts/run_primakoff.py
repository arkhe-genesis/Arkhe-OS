#!/usr/bin/env python3
# Executar Experimento Primakoff Gold

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
    print("Bobina: " + str(result["coil_length_m"]) + " m, " + str(result["coil_field_t"]) + " T")
    print("Feixe: " + str(result["beam_energy_gev"]) + " GeV, " + str(result["days"]) + " dias")
    print("Total de eletroes: " + str(result["total_electrons"]))
    print("Probabilidade Primakoff: " + str(result["primakoff_probability"]))

    print("\n--- RESULTADOS ---")
    print("Sinal esperado: " + str(result["signal_events"]) + " eventos")
    print("Fundo apos veto: " + str(result["background_events"]) + " eventos")
    print("Eventos observados: " + str(result["observed_events"]))
    print("Significancia: " + str(result["significance_sigma"]) + " sigma")
    print("Descoberta: " + ("SIM" if result["discovery"] else "EVIDENCIA"))
    print("PHI_C: " + str(round(result["phi_c"], 3)))

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
    print("Evento teste: " + classification["class"] + " (" + str(round(classification["avg_confidence"], 2)) + ")")
    print("Quorum: " + str(classification["quorum_reached"]))

    # Gerar selo
    seal = exp.get_seal()
    print("\n--- SELO CANONICO ---")
    print("Hash: " + seal)
    print("Status: CANONIZED")

if __name__ == "__main__":
    main()