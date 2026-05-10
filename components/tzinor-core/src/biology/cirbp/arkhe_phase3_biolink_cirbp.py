#!/usr/bin/env python3
"""
arkhe_phase3_biolink_cirbp.py
Synapse-κ #15 – Fase 3: Acoplamento Citosol-Núcleo (Bio-Link 40Hz)
Arkhe(n) | Longevidade e Coerência Genómica

Este script simula a correlação entre a coerência da Calmodulina (λ2_conf)
e a ativação do reparo genômico (CIRBP) sob estímulo de 40Hz.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks
import json
import os

# ============================================================================
# CONSTANTES ARKHE
# ============================================================================
LAMBDA_CRIT = 0.847
FREQ_BIOLINK = 40.0  # Hz
T_SIM = 2.0          # segundos para simulação de alta resolução
DT = 0.0005          # passo de tempo (0.5 ms)

# ============================================================================
# MODELO DE ACOPLAMENTO CaM-CIRBP
# ============================================================================
def coupled_system(t, y, A_field, k_peptide):
    """
    y = [phi_cam, lambda2_cam, cirbp_conc, lambda2_dna]
    """
    phi_cam, l2_cam, cirbp, l2_dna = y

    # 1. Dinâmica da Calmodulina (Oscilador de Kuramoto forçado)
    # d_phi/dt = omega + K*sin(theta_field - phi)
    omega_cam = 2 * np.pi * FREQ_BIOLINK
    theta_field = 2 * np.pi * FREQ_BIOLINK * t
    K_ext = 5.0 * A_field
    d_phi_cam = omega_cam + K_ext * np.sin(theta_field - phi_cam)

    # l2_cam tende a 1.0 se phi_cam estiver em fase com o campo
    target_l2 = 0.5 + 0.5 * np.cos(theta_field - phi_cam)
    dl2_cam = 10.0 * (target_l2 - l2_cam)

    # 2. Ativação do CIRBP (Depende da coerência da CaM)
    # d_cirbp/dt = k_prod * l2_cam - gamma_cirbp * cirbp
    k_prod = 0.5 * (1.0 + k_peptide)
    gamma_cirbp = 0.1
    # Limiar de ativação: CIRBP só sobe se CaM estiver coerente
    activation = 1.0 if l2_cam > LAMBDA_CRIT else 0.1
    dcirbp = k_prod * activation - gamma_cirbp * cirbp

    # 3. Coerência Genômica (λ2_dna)
    # dl2_dna/dt = kappa * cirbp * (1 - l2_dna) - gamma_dmg * l2_dna
    kappa_repair = 0.2
    gamma_dmg = 0.005
    dl2_dna = kappa_repair * cirbp * (1.0 - l2_dna) - gamma_dmg * l2_dna

    return [d_phi_cam, dl2_cam, dcirbp, dl2_dna]

def run_scenario(name, A_field, k_peptide):
    t_span = (0, T_SIM)
    t_eval = np.arange(0, T_SIM, DT)
    y0 = [0.0, 0.5, 1.0, 0.95]

    sol = solve_ivp(coupled_system, t_span, y0, t_eval=t_eval, args=(A_field, k_peptide))

    # Cálculo de PLV (Phase Locking Value) aproximado
    # PLV = |1/N * sum(exp(i * (theta_field - phi_cam)))|
    theta_field = 2 * np.pi * FREQ_BIOLINK * sol.t
    phase_diff = theta_field - sol.y[0]
    plv = np.abs(np.mean(np.exp(1j * phase_diff)))

    return {
        "name": name,
        "t": sol.t,
        "l2_cam": sol.y[1],
        "cirbp": sol.y[2],
        "l2_dna": sol.y[3],
        "plv": float(plv)
    }

# ============================================================================
# SIMULAÇÃO PRINCIPAL
# ============================================================================
def main():
    print("=" * 60)
    print("ARKHE(n) – FASE 3: ACOPLAMENTO BIO-LINK 40Hz")
    print("=" * 60)

    scenarios = [
        ("Baseline", 0.0, 0.0),
        ("Bio-Link 40Hz", 1.0, 0.0),
        ("Peptide + Bio-Link", 1.0, 1.5),
        ("Whale Level", 0.0, 2.0)
    ]

    all_results = []
    summary_data = {}

    plt.figure(figsize=(12, 10))

    for i, (name, A, K) in enumerate(scenarios):
        res = run_scenario(name, A, K)
        all_results.append(res)

        # Estatísticas
        final_l2_dna = res["l2_dna"][-1]
        max_cirbp = np.max(res["cirbp"])
        avg_l2_cam = np.mean(res["l2_cam"])

        summary_data[name] = {
            "cirbp_upregulation": float(max_cirbp / all_results[0]["cirbp"][0]),
            "plv": res["plv"],
            "final_l2_dna": float(final_l2_dna)
        }

        print(f"Scenario: {name}")
        print(f"  PLV: {res['plv']:.4f}")
        print(f"  Final λ2_DNA: {final_l2_dna:.5f}")
        print(f"  Max CIRBP: {max_cirbp:.2f}")

        # Plotting
        plt.subplot(2, 2, i+1)
        plt.plot(res["t"], res["l2_cam"], label="λ2_CaM")
        plt.plot(res["t"], res["l2_dna"], label="λ2_DNA")
        plt.axhline(y=LAMBDA_CRIT, color='r', linestyle='--', alpha=0.5)
        plt.title(f"{name} (PLV={res['plv']:.2f})")
        plt.xlabel("Time (s)")
        plt.legend()
        plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("tzinor-core/src/biology/cirbp/phase3_biolink_results.png")

    # Falsifiable Predictions
    predictions = [
        {"id": "P1", "hypothesis": "Bio-Link 40Hz upregula CIRBP ~2.8x", "test": "RT-qPCR em fibroblastos ± 40Hz"},
        {"id": "P2", "hypothesis": "PLV entre campo e CaM > 0.8 at 40Hz", "test": "FRET calmodulina em tempo real"},
        {"id": "P3", "hypothesis": "Peptídeo + Bio-Link atinge λ2_DNA > 0.99", "test": "Ensaio γ-H2AX comparativo"},
        {"id": "P4", "hypothesis": "Lag temporal CaM -> CIRBP < 5 min", "test": "Time-lapse imaging CaM/CIRBP"}
    ]

    output = {
        "timestamp": "847.635",
        "scenarios": summary_data,
        "predictions": predictions,
        "network_coherence": {
            "plv_cam_field": summary_data["Bio-Link 40Hz"]["plv"],
            "max_l2_dna": max([s["final_l2_dna"] for s in summary_data.values()])
        }
    }

    with open("tzinor-core/src/biology/cirbp/phase3_biolink_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n[OK] Simulação concluída.")
    print("[OK] Resultados salvos em tzinor-core/src/biology/cirbp/phase3_biolink_results.json")

if __name__ == "__main__":
    main()
