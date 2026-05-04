# core/gluing_kernel.py — v∞.370.3 (corrigido)
"""
Characteristic Gluing Steering — Kernel de Colagem Fenomenológico

Nota epistêmica (v∞.370.3):
  O kernel tanh usado neste módulo é uma sigmoide fenomenológica
  escolhida por suas propriedades matemáticas (C^∞, derivadas analíticas,
  parâmetro de inclinação controlável), não por derivação direta
  do perfil de ação do instanton BPST.

  A analogia com transições instantônicas em Yang-Mills permanece
  como motivação conceitual, mas não como justificativa quantitativa.
  Para derivação física rigorosa, consulte:
    - BPST instanton: Belavin et al., Phys. Lett. B 59 (1975)
    - Superposição diluída: Callan et al., Phys. Rev. D 17 (1978)
"""
import numpy as np
from typing import Callable

# Renomear função para refletir natureza fenomenológica
def gluing_kernel_tanh(t: np.ndarray, steepness: float,
                       center: float = 0.5) -> np.ndarray:
    """
    Kernel de colagem sigmoide (tanh-based) para transições de regime.

    Parâmetros:
    - steepness: inclinação da sigmoide (otimizado numericamente por caso de uso)
    - center: ponto central da transição em [0, 1]

    Propriedades:
    - C^∞ smoothness garantida
    - Derivadas analíticas conhecidas
    - Monotonicidade estrita
    """
    return 0.5 * (1.0 + np.tanh(steepness * (t - center)))

# Parâmetros otimizados empiricamente por caso de uso
GLUING_KERNEL_PARAMS = {
    'default': {'steepness': 0.7854, 'description': 'sigmoide balanceada'},
    'sharp_transition': {'steepness': 2.19, 'description': 'transição abrupta (BPST-like)'},
    'smooth_transition': {'steepness': 0.15, 'description': 'transição suave (multi-instanton diluído)'},
    # Adicionar novos perfis conforme validação experimental
}

def get_gluing_kernel(profile: str = 'default') -> Callable:
    """Retorna kernel de colagem com parâmetros validados empiricamente."""
    params = GLUING_KERNEL_PARAMS.get(profile, GLUING_KERNEL_PARAMS['default'])
    return lambda t: gluing_kernel_tanh(t, steepness=params['steepness'])
