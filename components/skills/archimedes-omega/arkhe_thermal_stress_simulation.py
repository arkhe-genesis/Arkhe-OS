#!/usr/bin/env python3
"""
arkhe_thermal_stress_simulation.py
Arkhe(n) – Thermal cooling simulation for 96‑well plate after photopolymerization.
Predicts waiting time before cell inoculation to ensure temperature ≤ 37°C.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timezone
import json

# ============================================================================
# CONSTANTES FÍSICAS
# ============================================================================
RHO = 1000.0          # kg/m³ (densidade do polímero/água)
CP = 4180.0           # J/(kg·K) (calor específico)
H_CONV = 10.0         # W/(m²·K) (coeficiente de convecção natural)
T_AMBIENT = 25.0      # °C (temperatura do laboratório)
T_SAFE = 37.0         # °C (temperatura máxima para células)
T_MAX_MEASURED = 41.2 # °C (pico medido no teste de estresse, poço central)

# Geometria da placa de 96 poços (padrão ANSI/SLAS)
WELL_DIAMETER_MM = 6.4
WELL_RADIUS_M = (WELL_DIAMETER_MM / 2) / 1000.0
AREA_BOTTOM = np.pi * WELL_RADIUS_M**2  # m²

# Tabela de volumes (µL) para cada tipo de nervo (da calculadora)
VOLUME_TABLE = {
    "Ciatico (Rato)": 31.42,
    "Ciatico (Humano)": 259.18,
    "Mediano (Humano)": 87.96,
    "Ulnar (Humano)": 65.97,
    "Femoral (Humano)": 148.44,
    "Tibial (Humano)": 204.20,
    "Radial (Humano)": 113.10,
    "Peroneiro (Humano)": 87.96,
}

# ============================================================================
# MODELO DE RESFRIAMENTO
# ============================================================================
def cooling_time_constant(volume_ul):
    """Calcula constante de tempo τ (segundos) para um dado volume."""
    volume_m3 = volume_ul * 1e-9
    mass = RHO * volume_m3
    # Área de contacto: a parte líquida está em contacto com o fundo do poço
    # Para volumes pequenos, a altura é pequena e a área lateral é desprezível;
    # assumimos que a transferência de calor ocorre principalmente pelo fundo.
    # No entanto, para volumes maiores, a área lateral também contribui.
    # Usamos uma correção empírica: A_eff = A_bottom + 0.5 * lateral
    height_m = volume_m3 / AREA_BOTTOM
    lateral_area = np.pi * WELL_RADIUS_M * 2 * height_m  # cilindro
    A_eff = AREA_BOTTOM + 0.5 * lateral_area
    tau = mass * CP / (H_CONV * A_eff)
    return tau

def cooling_curve(t, T_max, tau):
    """Temperatura em função do tempo (segundos) após irradiação."""
    return T_AMBIENT + (T_max - T_AMBIENT) * np.exp(-t / tau)

def time_to_cool(T_max, tau, target_temp):
    """Calcula o tempo necessário para atingir target_temp (segundos)."""
    if T_max <= target_temp:
        return 0.0
    return -tau * np.log((target_temp - T_AMBIENT) / (T_max - T_AMBIENT))

# ============================================================================
# SIMULAÇÃO
# ============================================================================
def main():
    print("=" * 70)
    print("ARKHE(n) – Simulação de Resfriamento Térmico In Silico")
    print("=" * 70)

    # Para cada tipo de nervo, calcular τ e tempo de resfriamento até 37°C
    results = []
    for nerve, vol in VOLUME_TABLE.items():
        tau = cooling_time_constant(vol)
        # T_max é extrapolado a partir da medição experimental (poço central)
        T_max = T_MAX_MEASURED
        t_cool = time_to_cool(T_max, tau, T_SAFE)
        results.append({
            "Nervo": nerve,
            "Volume (µL)": vol,
            "tau_s": round(float(tau), 1),
            "T_max_C": T_max,
            "Time_to_37C_s": round(float(t_cool), 1),
            "Time_to_37C_min": round(float(t_cool / 60), 1)
        })

    df = pd.DataFrame(results)
    print("\n📊 Resultados da Simulação de Resfriamento")
    print(df.to_string(index=False))

    # Gráfico das curvas de resfriamento para os volumes extremos
    plt.figure(figsize=(10, 6))
    t_range = np.linspace(0, 600, 500)  # 0-10 minutos
    for nerve, vol in VOLUME_TABLE.items():
        tau = cooling_time_constant(vol)
        T_curve = cooling_curve(t_range, T_MAX_MEASURED, tau)
        plt.plot(t_range / 60, T_curve, label=f"{nerve} ({vol:.0f} µL)", lw=1.5)
    plt.axhline(y=T_SAFE, color='red', linestyle='--', label=f"Limite seguro (37°C)")
    plt.xlabel("Tempo (minutos)")
    plt.ylabel("Temperatura (°C)")
    plt.title("Simulação de Resfriamento Pós‑Polimerização")
    plt.legend(loc='upper right', fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("thermal_cooling_simulation.png", dpi=150)
    print("\n📈 Gráfico salvo: thermal_cooling_simulation.png")

    # Registrar na Arkhe‑Chain (simulação)
    report = {
        "protocol": "THERMAL_COOLING_SIMULATION_v1",
        "timestamp": datetime.now().isoformat(),
        "ambient_temp_C": float(T_AMBIENT),
        "safe_temp_C": float(T_SAFE),
        "measured_T_max_C": float(T_MAX_MEASURED),
        "results": results
    }
    with open("thermal_cooling_simulation.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\n✅ Resultados salvos em thermal_cooling_simulation.json")

    # Recomendação de espera
    max_time = max(r["Time_to_37C_s"] for r in results)
    print(f"\n⏱️  Recomendação: Aguardar pelo menos {max_time:.0f} segundos ({max_time/60:.1f} minutos)")
    print("   antes da inoculação celular para garantir que todos os poços estejam ≤ 37°C.")

if __name__ == "__main__":
    main()
