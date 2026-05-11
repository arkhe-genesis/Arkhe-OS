import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import json
import os
from skills import SynapseKValidator, TMSModulator, ARChromestheticInterface

def run_validation_protocol():
    """
    Protocolo completo de validação Synapse-κ para Arkhe-Ω
    """
    print("="*70)
    print("VALIDADOR λ₂ - Protocolo Synapse-κ / Arkhe-Ω v2.1")
    print("="*70)

    # 1. Validação EEG
    validator = SynapseKValidator()

    print("\n[1] Simulação EEG: Sinestetas vs Controles")
    print("-" * 50)

    n_subjects = 50 # Reduzido para teste mais rápido
    results = {'syn': [], 'ctrl': []}

    for _ in range(n_subjects):
        # Simula sinesteta (κ alto)
        eeg_syn = validator.generate_eeg_synapse(kappa=0.9)
        val_syn = validator.validate_synaesthete(eeg_syn)
        results['syn'].append(val_syn['lambda_total'])

        # Simula controle (κ baixo)
        eeg_ctrl = validator.generate_eeg_control()
        val_ctrl = validator.validate_synaesthete(eeg_ctrl)
        results['ctrl'].append(val_ctrl['lambda_total'])

    # Estatísticas
    mean_syn = np.mean(results['syn'])
    mean_ctrl = np.mean(results['ctrl'])
    t_stat, p_value = stats.ttest_ind(results['syn'], results['ctrl'])

    print(f"Sinestetas (n={n_subjects}):")
    print(f"  λ₂ médio: {mean_syn:.4f} (esperado > 0.85)")

    print(f"\nControles (n={n_subjects}):")
    print(f"  λ₂ médio: {mean_ctrl:.4f} (esperado < 0.70)")

    print(f"\nTeste t: t={t_stat:.2f}, p={p_value:.2e}")
    print(f"{'✓ Diferença significativa detectada' if p_value < 0.001 else '✗ Sem diferença'}")

    # 2. Modulação TMS
    print("\n[2] Modelagem TMS - Modulação de κ")
    print("-" * 50)
    tms = TMSModulator()

    kappa_baseline = 0.2
    intensity_optimal = 65

    kappa_result = tms.modulate_kappa(kappa_baseline, intensity_optimal, duration_min=10)
    print(f"Baseline κ: {kappa_baseline}")
    print(f"Após TMS {intensity_optimal}% (10min): κ = {kappa_result:.3f}")
    print(f"{'✓ Indução sinestésica bem-sucedida' if kappa_result > 0.7 else '✗ Efeito insuficiente'}")

    # 3. Interface AR
    print("\n[3] Protótipo AR - Mapeamento 36° × 17.14°")
    print("-" * 50)
    ar = ARChromestheticInterface()

    test_freqs = [440, 660, 880, 1320]

    print("Mapeamento Áudio-Visual:")
    for freq in test_freqs:
        res = ar.audio_to_color(freq, kappa=0.9)
        print(f"  {freq}Hz → Camada {res['phase_idx']} (Arkhe), Posição {res['pent_idx']} (Pent)")
        print(f"       Cor HSV: ({res['h']}°, {res['s']}, {res['v']})")

    # Visualizações
    intensities = np.linspace(0, 100, 100)
    kappas_low = [tms.modulate_kappa(0.2, i, 5) for i in intensities]

    plt.figure(figsize=(10, 6))
    plt.plot(intensities, kappas_low, 'b-', label='Baseline κ=0.2')
    plt.axvline(x=50, color='gray', linestyle='--')
    plt.xlabel('Intensidade TMS (%)')
    plt.ylabel('κ')
    plt.title('Modulação de κ via TMS')
    plt.grid(True, alpha=0.3)
    plt.savefig('tms_modulation_kappa.png')
    plt.close()

    cmap, _, _ = ar.generate_chromatic_map()
    plt.figure(figsize=(8, 8))
    # Simplified visualization of the map
    plt.imshow(cmap, aspect='auto')
    plt.title('Mapa Cromático Synapse-κ (HSV)')
    plt.savefig('ar_chromatic_unified.png')
    plt.close()

    print("\n[+] Visualizações salvas.")

    return {
        'eeg_validation': {'syn_mean': float(mean_syn), 'ctrl_mean': float(mean_ctrl), 'p_value': float(p_value)},
        'tms_feasible': bool(kappa_result > 0.7),
        'ar_states': 210
    }

if __name__ == "__main__":
    results = run_validation_protocol()
    with open('synapse_k_validation.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nPROTOCOLO CONCLUÍDO")
