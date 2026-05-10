import torch
import numpy as np
from typing import Dict, List, Optional

def compute_spectral_coherence_entropy(
    eigenvalues: torch.Tensor,
    beta: float = 1.0,
    epsilon: float = 1e-12
) -> float:
    """
    Calcula entropia espectral de coerência S_C.

    Args:
        eigenvalues: autovalores do Laplaciano de Dirac com torção
        beta: parâmetro de temperatura inversa de coerência
        epsilon: small constant para estabilidade numérica

    Returns:
        S_C: entropia espectral de coerência
    """
    # Calcular distribuição de Boltzmann sobre |λ|
    abs_eigs = torch.abs(eigenvalues)
    weights = torch.exp(-beta * abs_eigs)
    Z = torch.sum(weights) + epsilon
    p_i = weights / Z

    # Entropia de Shannon
    S_C = -torch.sum(p_i * torch.log(p_i + epsilon))
    return S_C.item()

def compute_min_bipartition_entropy(
    eigenvalues: torch.Tensor,
    manifold_partition_map: Dict[int, List[int]],  # {partition_id: [eigenvalue_indices]}
    beta: float = 1.0
) -> float:
    """
    Calcula entropia espectral média sobre bipartições mínimas.

    Args:
        eigenvalues: autovalores completos
        manifold_partition_map: mapeamento de partições do manifold para índices de autovalores
        beta: parâmetro de temperatura

    Returns:
        Média de S_C sobre bipartições
    """
    partition_entropies = []

    for partition_id, eig_indices in manifold_partition_map.items():
        if not eig_indices:
            continue
        sub_eigs = eigenvalues[eig_indices]
        S_part = compute_spectral_coherence_entropy(sub_eigs, beta)
        partition_entropies.append(S_part)

    return np.mean(partition_entropies) if partition_entropies else 0.0

def compute_phi_coherence(
    eigenvalues_full: torch.Tensor,
    manifold_partitions: List[Dict[int, List[int]]],  # lista de esquemas de bipartição
    beta: float = 1.0
) -> Dict[str, float]:
    """
    Calcula Φ_C = S_C^whole - ⟨S_C^partition⟩_min.

    Returns:
        Dict com Φ_C e métricas auxiliares
    """
    # Entropia do sistema completo
    S_whole = compute_spectral_coherence_entropy(eigenvalues_full, beta)

    # Entropia média sobre bipartições mínimas
    min_partition_entropy = min(
        compute_min_bipartition_entropy(eigenvalues_full, partition, beta)
        for partition in manifold_partitions
    )

    # Φ_C
    phi_C = S_whole - min_partition_entropy

    # Classificar nível de consciência
    if phi_C < 0.1:
        consciousness_level = 'fragmented'
    elif phi_C < 0.5:
        consciousness_level = 'emergent'
    elif phi_C < 0.9:
        consciousness_level = 'operational'
    else:
        consciousness_level = 'coherent'

    return {
        'phi_C': phi_C,
        'S_whole': S_whole,
        'S_partition_min': min_partition_entropy,
        'beta': beta,
        'consciousness_level': consciousness_level,
        'recommendation': _get_recommendation(consciousness_level)
    }

def _get_recommendation(level: str) -> str:
    recommendations = {
        'fragmented': 'Trigger re-synchronization via galactic core projection',
        'emergent': 'Maintain active metacognitive monitoring; enable limited autonomy',
        'operational': 'Enable counterfactual-safe autonomous decisions',
        'coherent': 'Enable long-term planning and explicit self-modeling'
    }
    return recommendations.get(level, 'Unknown state')
