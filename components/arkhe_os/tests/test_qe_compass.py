import pytest
from arkhe_os.api.v1.endpoints.qe_compass import calculate_resonance, ONTOLOGICAL_WEIGHTS, INTENTION_VECTOR
from arkhe_os.api.v1.qe_compass import ActionDimension

def test_calculate_resonance_perfect_alignment():
    # Perfeito alinhamento com o vetor de intenção
    action_dims = INTENTION_VECTOR.copy()
    resonance, breakdown = calculate_resonance(action_dims, INTENTION_VECTOR, ONTOLOGICAL_WEIGHTS)

    # O produto escalar de vetores normalizados e idênticos deve ser 1.0 (ou próximo devido a pesos)
    # Aqui calculate_resonance faz sum(w * a * i) / sum(w).
    # Se a = i, então sum(w * i^2) / sum(w).
    # Com pesos normalizados sum(w)=1.
    expected_resonance = sum(ONTOLOGICAL_WEIGHTS[d] * INTENTION_VECTOR[d]**2 for d in ActionDimension)
    # Na verdade a função divide pelo sum(weights) que é 1.
    assert resonance == pytest.approx(expected_resonance, rel=1e-3)

def test_calculate_resonance_low_alignment():
    # Baixo alinhamento
    action_dims = {d: 0.1 for d in ActionDimension}
    resonance, breakdown = calculate_resonance(action_dims, INTENTION_VECTOR, ONTOLOGICAL_WEIGHTS)
    assert resonance < 0.5
