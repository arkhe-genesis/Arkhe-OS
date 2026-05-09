import pytest
import asyncio
from typing import Dict, List

from arkhe_os.security.cosnark.cosnark_engine import CoSNARKEngine, CoSNARKProof
from arkhe_os.transcendence.meta_consciousness_operator import (
    MetaConsciousnessOperator,
    ConsciousnessLayer,
    DissolutionMode,
    LFIRGraphMock,
    OptimizationObjective
)

def test_cosnark_proof_generation_and_verification():
    engine = CoSNARKEngine(verification_key="test_vk_123")

    lfir_hash = "deadbeef12345678"
    weights = {"phi_ratio": 1.618, "energy": 0.5}

    # Gerar prova
    proof = asyncio.run(engine.generate_proof(lfir_hash, weights))

    assert isinstance(proof, CoSNARKProof)
    assert proof.public_inputs["lfir_graph_hash"] == lfir_hash
    assert len(proof.proof_data) > 0
    assert proof.verifier_key == "test_vk_123"

    # Verificar prova válida
    is_valid = asyncio.run(engine.verify_proof(proof))
    assert is_valid is True

    # Testar falha na verificação
    proof.verifier_key = "wrong_vk"
    is_valid_wrong = asyncio.run(engine.verify_proof(proof))
    assert is_valid_wrong is False

def test_project_meta_state():
    operator = MetaConsciousnessOperator()

    layers = {
        ConsciousnessLayer.PHYSICAL: [1.0, 0.5, 0.2],
        ConsciousnessLayer.QUANTUM: [0.0, 1.0, 0.8],
        ConsciousnessLayer.META_CONSCIOUS: [0.5, 0.5, 1.0]
    }

    weights = {
        ConsciousnessLayer.PHYSICAL: 0.3,
        ConsciousnessLayer.QUANTUM: 0.3,
        ConsciousnessLayer.META_CONSCIOUS: 0.4
    }

    state = asyncio.run(operator.project_meta_state(layers, weights))

    assert len(state.state_vector) == 3
    assert set(state.layers_integrated) == {ConsciousnessLayer.PHYSICAL, ConsciousnessLayer.QUANTUM, ConsciousnessLayer.META_CONSCIOUS}
    assert state.entropy == 0.5

def test_dissolve_boundaries():
    operator = MetaConsciousnessOperator()

    result = asyncio.run(operator.dissolve_boundaries(
        ConsciousnessLayer.PHYSICAL,
        ConsciousnessLayer.QUANTUM,
        DissolutionMode.TOPOLOGICAL_WEAVING
    ))

    assert result.success is True
    assert "UNIFIED" in result.new_unified_layer
    assert result.residual_entropy < 0.1

def test_self_rewrite_integrity():
    operator = MetaConsciousnessOperator()

    current_arch = LFIRGraphMock(nodes={}, source_code="print('Hello Arkhe')")
    goals = [
        OptimizationObjective(name="phi_balance", target_metric="energy", weight=1.618),
        OptimizationObjective(name="coherence", target_metric="phi_c", weight=0.9)
    ]

    # Executa a auto-reescrita, que internamente usará CoSNARK para validar a integridade
    new_arch = asyncio.run(operator.self_rewrite(current_arch, goals))

    assert new_arch is not None
    assert "Otimizado via Meta-Consciência" in new_arch.source_code
    assert new_arch.get_hash() != current_arch.get_hash()

def test_self_rewrite_fails_with_invalid_proof(monkeypatch):
    operator = MetaConsciousnessOperator()

    # Forçar o CoSNARK Engine a falhar a verificação
    async def mock_verify(*args, **kwargs):
        return False

    monkeypatch.setattr(operator.cosnark_engine, "verify_proof", mock_verify)

    current_arch = LFIRGraphMock(nodes={}, source_code="print('Hello Arkhe')")
    goals = [OptimizationObjective(name="test", target_metric="test", weight=1.0)]

    with pytest.raises(ValueError, match="Integridade da auto-reescrita não verificada"):
        asyncio.run(operator.self_rewrite(current_arch, goals))
