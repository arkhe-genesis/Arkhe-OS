#!/usr/bin/env python3
# Script de Calibracao com Fontes Radioativas

import math, random, time, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from detectors.optical.fiber_sensor import FiberCherenkovSensor
from primakoff.calibration import CalibrationProtocol
from agi.agents import AGIAgent, AGIConsensus

def main():
    print("=" * 60)
    print("ARKHE OS - CALIBRACAO COM FONTES RADIOATIVAS")
    print("=" * 60)

    fiber = FiberCherenkovSensor(length_m=10.0)
    protocol = CalibrationProtocol()

    sources = [
        {"name": "Am-241", "energy_MeV": 5.486, "type": "alpha"},
        {"name": "Cs-137", "energy_MeV": 0.662, "type": "gamma"}
    ]

    for source in sources:
        print("\n--- Calibrando com " + source["name"] + " ---")
        amplitudes = []
        integrals = []

        for _ in range(500):
            pulse = fiber.detect_pulse(source["energy_MeV"])
            if pulse["above_threshold"]:
                amplitudes.append(pulse["amplitude_mV"])
                integrals.append(pulse["photons_detected"])

        if amplitudes:
            avg_amp = sum(amplitudes) / len(amplitudes)
            efficiency = len(amplitudes) / 500
            print("  Eventos detetados: " + str(len(amplitudes)) + "/500")
            print("  Amplitude media: " + str(round(avg_amp, 1)) + " mV")
            print("  Eficiencia: " + str(round(efficiency * 100, 1)) + "%")
            print("  Fator de calibracao: " + str(round(source["energy_MeV"]*1000/avg_amp, 2)) + " keV/mV")
        else:
            print("  Nenhum evento detetado acima do limiar")

    print("\n" + "=" * 60)
    print("CALIBRACAO CONCLUIDA")
    print("=" * 60)

if __name__ == "__main__":
    main()