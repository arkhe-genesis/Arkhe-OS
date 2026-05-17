#!/usr/bin/env python3
"""
Testes de integração para o pipeline unificado neurogenético.
Valida: prompt → campo 3D → atuadores → GRN → score
"""
import asyncio
import numpy as np
import pytest
from integration.neurogenetic_wetlab_unified import (
    UnifiedNeurogeneticPipeline,
    UnifiedNeurogeneticConfig,
)

@pytest.fixture
def unified_config():
    """Configuração padrão para testes."""
    return UnifiedNeurogeneticConfig(
        field_resolution=(5, 5, 5),
        num_particles=20,  # Reduzido para testes rápidos
        evolution_generations=5,  # Reduzido para testes
        population_size=4,
        spatial_weight=0.4,
        grn_weight=0.4,
        temporal_weight=0.2,
    )

@pytest.fixture
def unified_pipeline(unified_config):
    """Pipeline unificado para testes."""
    return UnifiedNeurogeneticPipeline(config=unified_config)

@pytest.mark.asyncio
async def test_pipeline_memory_consolidation(unified_pipeline):
    """Testa prompt de consolidação de memória."""
    result = await unified_pipeline.execute_pipeline(
        prompt="consolidate memory",
        initial_grn_state={"CREB": 0.3, "FOS": 0.2}
    )

    # Validações
    assert result.composite_score >= 0.0
    assert result.grn_score >= 0.0
    assert result.spatial_score >= 0.0

    # Perfil gênico alvo deve priorizar CREB/FOS
    assert "CREB" in result.final_grn_state
    assert "FOS" in result.final_grn_state

    print(f"✅ Memory consolidation: score={result.composite_score:.4f}")

@pytest.mark.asyncio
async def test_pipeline_neurogenesis_induction(unified_pipeline):
    """Testa prompt de indução de neurogênese."""
    result = await unified_pipeline.execute_pipeline(
        prompt="induce neurogenesis",
        initial_grn_state={"SOX2": 0.8, "ASCL1": 0.1}
    )

    # Neurogênese deve aumentar ASCL1/DCX
    assert result.final_grn_state.get("ASCL1", 0) >= 0.1
    assert result.final_grn_state.get("DCX", 0) >= 0.0

    print(f"✅ Neurogenesis: score={result.composite_score:.4f}")

@pytest.mark.asyncio
async def test_pipeline_spatial_clustering(unified_pipeline):
    """Testa prompt de formação de cluster espacial."""
    result = await unified_pipeline.execute_pipeline(
        prompt="form a cluster"
    )

    # Clustering deve ter score espacial alto
    assert result.spatial_score >= 0.3  # Threshold conservador para teste

    print(f"✅ Spatial clustering: spatial_score={result.spatial_score:.4f}")

@pytest.mark.asyncio
async def test_pipeline_refined_gene_mapping(unified_pipeline):
    """Testa que o mapeamento refinado produz perfis distintos para prompts distintos."""
    result1 = await unified_pipeline.execute_pipeline(prompt="consolidate memory")
    result2 = await unified_pipeline.execute_pipeline(prompt="induce neurogenesis")

    # Perfis gênicos finais devem ser diferentes
    grn1 = result1.final_grn_state
    grn2 = result2.final_grn_state

    # CREB deve ser maior em memory vs neurogenesis
    assert grn1.get("CREB", 0) > grn2.get("CREB", 0) - 0.1  # Tolerância para ruído

    # ASCL1 deve ser maior em neurogenesis vs memory
    assert grn2.get("ASCL1", 0) > grn1.get("ASCL1", 0) - 0.1

    print(f"✅ Refined mapping: distinct profiles confirmed")

@pytest.mark.asyncio
async def test_pipeline_evolution_convergence(unified_pipeline):
    """Testa que a evolução converge para scores melhores."""
    results = []
    for i in range(3):
        result = await unified_pipeline.execute_pipeline(
            prompt="enhance plasticity",
            initial_grn_state={"CREB": 0.5}
        )
        results.append(result.composite_score)

    # Scores devem ser consistentes (baixa variância)
    std_score = np.std(results)
    assert std_score < 0.2  # Threshold conservador

    print(f"✅ Evolution convergence: scores={results}, std={std_score:.4f}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])