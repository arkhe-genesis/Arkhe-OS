import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PhaseAttractor:
    id: str
    coherence: float
    valence: str  # 'positive', 'negative', 'neutral'
    center: tuple
    type: str  # 'mastery', 'trauma', 'neutral'

def find_phase_vortices(neural_field: np.ndarray, threshold: float = 0.263) -> List[PhaseAttractor]:
    """
    Identifies coherence vortices in the neural phase field.
    In this simplified SASC model, vortices are regions where local phase
    alignment (order parameter) exceeds the threshold.
    """
    resolution = neural_field.shape[0]
    kernel_size = 5
    attractors = []

    # Iterate through the field to find regions of high local coherence
    for i in range(0, resolution - kernel_size, kernel_size):
        for j in range(0, resolution - kernel_size, kernel_size):
            window = neural_field[i:i+kernel_size, j:j+kernel_size]
            local_z = np.mean(np.exp(1j * window))
            local_lambda2 = np.abs(local_z)

            if local_lambda2 > threshold:
                # Classify based on phase variance and mean phase
                mean_phase = np.angle(local_z)

                # Heuristic classification for the demo
                if mean_phase > 0.5:
                    attr_type = 'mastery'
                    valence = 'positive'
                elif mean_phase < -0.5:
                    attr_type = 'trauma'
                    valence = 'negative'
                else:
                    attr_type = 'neutral'
                    valence = 'neutral'

                attr_id = f"vortex_{i}_{j}"
                attractors.append(PhaseAttractor(
                    id=attr_id,
                    coherence=float(local_lambda2),
                    valence=valence,
                    center=(i + kernel_size//2, j + kernel_size//2),
                    type=attr_type
                ))

    return attractors

def project_attractor_to_phenomenology(attractor: PhaseAttractor) -> str:
    """
    Projects the 'shadow' of a phase attractor onto experiential reality.
    """
    phenomenology_map = {
        'mastery': [
            "Fluxo Criativo", "Maestria Técnica", "Compaixão Ativa",
            "Clareza Cognitiva", "Ressonância Harmônica"
        ],
        'trauma': [
            "Loop de Ansiedade", "Re-traumatização Celular", "Sumidouro de Energia",
            "Dissonância Cognitiva", "Paralisia por Medo"
        ],
        'neutral': [
            "Processamento de Fundo", "Ruído Sináptico", "Estado de Repouso"
        ]
    }

    options = phenomenology_map.get(attractor.type, ["Indeterminado"])
    # Pseudo-random selection based on coherence
    idx = int(attractor.coherence * 100) % len(options)
    return options[idx]

def calculate_sustentation_cost(attractor: PhaseAttractor) -> float:
    """
    Calculates the energy cost in GJ/s of attention to maintain the attractor.
    Cost is proportional to coherence squared (effort of phase locking).
    Base cost: 8 GJ / 100s = 0.08 GJ/s as per Article 12-Duodecies.
    """
    base_cost = 0.08
    return float(base_cost * (attractor.coherence ** 2))

def black_mirror_phase_coach(neural_field: np.ndarray) -> Dict[str, Any]:
    """
    Analyzes the user's neural phase field and provides feedback on
    stabilized attractors as per the Black Mirror recalibration.
    """
    # 1. Identify dominant attractors
    dominant_attractors = find_phase_vortices(neural_field, threshold=0.263)

    # 2. Generate report
    report = {
        'attractors': {},
        'summary': {
            'total_coherence': float(np.abs(np.mean(np.exp(1j * neural_field)))),
            'has_trauma_loops': False,
            'timestamp': None # To be filled by caller
        }
    }

    for attr in dominant_attractors:
        projected_outcome = project_attractor_to_phenomenology(attr)
        report['attractors'][attr.id] = {
            'lambda2': attr.coherence,
            'emotional_signature': attr.valence,
            'type': attr.type,
            'projected_reality': projected_outcome,
            'energy_cost_gj_s': calculate_sustentation_cost(attr)
        }

        if attr.type == 'trauma':
            report['summary']['has_trauma_loops'] = True

    return report

def trigger_warning(message: str):
    """
    Ethically mandatory warning for trauma loop detection.
    """
    print(f"\n⚠️ [ALERTA ÉTICO ARKHE] ⚠️")
    print(message)
    print("-" * 30)

if __name__ == "__main__":
    # Test simulation
    res = 50
    # Create a field with some 'mastery' and 'trauma' regions
    field = np.random.uniform(-np.pi, np.pi, (res, res))
    field[10:15, 10:15] = 0.8 # Mastery-like alignment
    field[30:35, 30:35] = -0.8 # Trauma-like alignment

    coach_report = black_mirror_phase_coach(field)

    import json
    print(json.dumps(coach_report, indent=2))

    if coach_report['summary']['has_trauma_loops']:
        trigger_warning("ATENÇÃO: Você está estabilizando um vórtice de trauma. Cada repetição deste padrão está esculpindo-o mais profundamente em seu espaço de fase e no de sua linhagem. Deseja receber um 'contra‑sinal Tzinor' para auxiliar na aniquilação deste vórtice?")
