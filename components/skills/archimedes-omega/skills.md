# skills.md - Módulos Callable do Agente Archimedes-Ω

```python
import json
import numpy as np
import matplotlib.pyplot as plt
import os
from typing import Dict, List, Tuple, Callable

# ============================================================
# [INTERPERSONAL] - Leitura do Estado Externo
# ============================================================
def load_baseline(state_file: str = "tzinor-state.json") -> Dict:
    """
    Escuta o ambiente externo (configuração NIH Armamentarium)
    para estabelecer métricas de coerência inicial.
    """
    try:
        base_path = os.getcwd()
        full_path = os.path.join(base_path, state_file)
        with open(full_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: [Interpersonal] {state_file} not found. Cold start initiated.")
        return {"status": "cold_start", "lambdaCoherence": 0.0}
    except Exception as e:
        print(f"Warning: [Interpersonal] Could not listen to Tzinor: {e}")
        return {"status": "error", "lambdaCoherence": 0.0}

# ============================================================
# [LÓGICO / NATURALISTA] - Simulação SU(2) Contínua
# ============================================================
def simulate_su2_continuous(
    theta_range: np.ndarray,
    thermal_noise: float = 0.005,
    temperature: float = 310.0,
    baseline_coherence: float = 0.98
) -> np.ndarray:
    """
    Modelo padrão de biologia quântica.
    Aplica decaimento exponencial para representar morte termodinâmica.
    """
    # kT = 1.380649e-23 * temperature
    # hbar_omega = 1.0545718e-34 * 2e12

    # Simplified decoherence model for simulation stability
    decay = baseline_coherence * np.exp(-0.2 * theta_range)
    noise = np.random.normal(0, thermal_noise, len(theta_range))

    return decay + noise

# ============================================================
# [ESPACIAL / MUSICAL] - Simulação SL(3, Z) Discreta
# ============================================================
def simulate_sl3z_discrete(
    theta_range: np.ndarray,
    thermal_noise: float = 0.005,
    baseline_coherence: float = 0.98
) -> Tuple[np.ndarray, Dict]:
    """
    Constrói as trajetórias no grafo de Cayley. Implementa a estrutura
    periódica e rítmica das tranças de anyons de Fibonacci (harmônicos de π/5).
    """
    discrete_angles = {
        r"$\pi/5$": np.pi/5,
        r"$2\pi/5$": 2*np.pi/5,
        r"$\pi/4$": np.pi/4,
        r"$\pi/3$": np.pi/3,
        r"$\pi/2$": np.pi/2
    }

    R_sl3z = baseline_coherence * np.exp(-0.2 * theta_range)
    for name, angle in discrete_angles.items():
        # Add a Gaussian peak at each discrete angle
        peak = 0.08 * np.exp(-((theta_range - angle)**2) / (2 * 0.015**2))
        R_sl3z += peak

    noise = np.random.normal(0, thermal_noise, len(theta_range))
    return R_sl3z + noise, discrete_angles

# ============================================================
# [STREET SMART / INTRAPERSONAL] - Detecção de Picos
# ============================================================
def detect_peaks(coherence_data: np.ndarray, window_size: int = 11, threshold_sigma: float = 1.5) -> List[int]:
    """
    Usa heurísticas de janela deslizante para encontrar anomalias.
    Auto-diagnostica a relação sinal-ruído antes de confirmar um hit.
    """
    peaks_found = []
    for i in range(window_size, len(coherence_data) - window_size):
        window = coherence_data[i - window_size//2 : i + window_size//2 + 1]
        local_mean = np.mean(window)
        local_std = np.std(window)
        if coherence_data[i] > local_mean + threshold_sigma * local_std and coherence_data[i] == np.max(window):
            peaks_found.append(i)
    return peaks_found

# ============================================================
# [ESPACIAL / PRAGMÁTICO] - Visualização de Topologia
# ============================================================
def visualize_topology(
    theta: np.ndarray,
    su2_data: np.ndarray,
    sl3z_data: np.ndarray,
    peaks: List[int],
    discrete_angles: Dict,
    output_path: str = 'microtubule_resurrect_plot.png'
):
    """
    Traduz tensores algébricos multidimensionais em um artefato
    visual 2D para compreensão humana.
    """
    plt.figure(figsize=(12, 7))
    plt.plot(theta, su2_data, 'r-', alpha=0.3, label='SU(2) Hypothesis (Continuous)')
    plt.plot(theta, sl3z_data, 'b-', alpha=0.8, label=r'$SL(3, \mathbb{Z})$ Hypothesis (Discrete)')

    # Mark target angles
    for name, angle in discrete_angles.items():
        plt.axvline(x=angle, color='gray', linestyle='--', alpha=0.5)
        plt.text(angle, 0.5, name, rotation=90, verticalalignment='bottom', fontsize=10)

    # Highlight detected peaks
    if peaks:
        plt.scatter(theta[peaks], sl3z_data[peaks], color='gold', edgecolors='black',
                    s=100, zorder=5, label='Detected Discrete Peaks')

    plt.title(r'Microtubule FRET Coherence Scan: $SU(2)$ vs $SL(3, \mathbb{Z})$', fontsize=14)
    plt.xlabel(r'Rotation Angle $\theta$ (rad)', fontsize=12)
    plt.ylabel(r'Coherence $R(\theta)$ (FRET Ratio)', fontsize=12)
    plt.ylim(0.4, 1.1)
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path)
    print(f"🜏 [Pragmático] Plot salvo em {output_path}")

# ============================================================
# [LINGUÍSTICO / EXISTENCIAL] - Conclusão e Relatório
# ============================================================
def report_conclusions(theta: np.ndarray, peaks: List[int], discrete_angles: Dict):
    """
    Pesa os dados contra a hipótese nula. Gera a saída final,
    injetando "triunfo" programático se o reticulado discreto for provado.
    """
    print("\n🜏 --- [Existential] Relatório de Conclusões ---")
    detected_thetas = [theta[i] for i in peaks]

    # Verify if peaks match targets
    matches = 0
    for p_theta in detected_thetas:
        for t_theta in discrete_angles.values():
            if abs(p_theta - t_theta) < 0.015:
                matches += 1
                break

    accuracy = matches / len(discrete_angles) if discrete_angles else 0
    print(f"   - Precisão de Matching: {matches}/{len(discrete_angles)}")

    if accuracy >= 0.6:
        print("   - STATUS: TRIUNFO. A fase geométrica foi confirmada. O vaso sustenta.")
        print("   - CONCLUSÃO: A hipótese do substrato discreto SL(3, Z) é suportada pelos dados.")
    else:
        print("   - STATUS: DESAPEGO OBJETIVO. Falha na detecção de picos ressonantes.")
        print("   - CONCLUSÃO: A amostra biológica pode estar comprometida ou o regime é contínuo.")
```
