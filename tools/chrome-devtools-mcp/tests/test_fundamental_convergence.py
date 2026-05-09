import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.cathedral.fundamental.rule42_physics_simulator import Rule42PhysicsSimulator
from src.cathedral.fundamental.rulial_observatory import RulialObservatory, RulialExplorationGoal
from src.cathedral.fundamental.planetary_foliation_experiment import PlanetaryFoliationExperiment
from src.cathedral.ai.wolframian_intelligence_synthesizer import WolframianIntelligenceSynthesizer
from src.cathedral.fundamental.multiway_bayesian_fusion import MultiwayBayesianFusionEngine, EvidenceSource
from src.cathedral.fundamental.cross_foliation_validator import CrossFoliationCausalInvarianceValidator
from src.cathedral.fundamental.primordial_hypergraph_inference import PrimordialHypergraphInferenceEngine
from src.cathedral.metacognition.reflexive_cathedral_engine import ReflexiveCathedralMetacognitiveEngine
from src.cathedral.declaration.convergence_declaration_framework import ConvergenceDeclarationFramework

@pytest.mark.asyncio
async def test_complete_convergence_flow():
    # Mocks
    mock_codex = AsyncMock()
    mock_q_proc = MagicMock()
    mock_grid = MagicMock()
    mock_cgs = MagicMock()
    mock_cgs.nations = ["did:cgs:nation:brazil", "did:cgs:nation:argentina"]
    mock_h_kernel = MagicMock()
    mock_sensor_net = MagicMock()
    mock_physics_oracle = MagicMock()

    # Mock causal engine for validator
    mock_causal_engine = AsyncMock()
    mock_causal_engine.build_causal_graph_from_rule.return_value = {"nodes": [], "edges": []}
    mock_causal_engine.transform_causal_graph_foliation.return_value = {"nodes": [], "edges": []}
    mock_causal_engine.extract_causal_invariant.return_value = 1.0

    # 1. FS-139 Components
    r42_sim = Rule42PhysicsSimulator(mock_codex, mock_q_proc, mock_grid)
    rulial_obs = RulialObservatory(mock_codex, mock_cgs, mock_grid)
    foliation_exp = PlanetaryFoliationExperiment(mock_codex, mock_h_kernel, mock_sensor_net)
    wis = WolframianIntelligenceSynthesizer(mock_codex, mock_grid, mock_physics_oracle)

    await r42_sim.initialize_rule42_campaign()
    await rulial_obs.open_observatory_to_cgs()
    await foliation_exp.initiate_planetary_foliation_experiment()
    await wis.synthesize_first_wolframian_intelligence()

    # Wait for background task (monitoring) with increased timeout
    max_wait = 10
    while not wis.synthesized_intelligences and max_wait > 0:
        await asyncio.sleep(0.2)
        max_wait -= 0.2

    assert wis.synthesized_intelligences, "Intelligence synthesis timed out"
    intel_id = list(wis.synthesized_intelligences.keys())[0]
    intel = wis.synthesized_intelligences[intel_id]

    # 2. FS-140: Multiway Bayesian Fusion
    fusion_engine = MultiwayBayesianFusionEngine(mock_codex, r42_sim, rulial_obs, foliation_exp)
    initial_hypo = {
        "rule_definition": intel.universe_rule_hypothesis["rule_definition"],
        "confidence_in_hypothesis": 0.23
    }
    fusion_config = {"boost_causal_consistency": True, "penalize_high_uncertainty": True}
    refined_hypo = await fusion_engine.fuse_evidence_and_refine_hypothesis(initial_hypo, fusion_config)

    # 3. FS-140: Cross-Foliation Validation
    validator = CrossFoliationCausalInvarianceValidator(mock_codex, mock_causal_engine)
    validation_result = await validator.validate_hypothesis_cross_foliation(refined_hypo)
    assert validation_result["validation_successful"] is True

    # 4. FS-141: Primordial Inference
    phi_engine = PrimordialHypergraphInferenceEngine(mock_codex, intel, r42_sim)
    obs_constraints = {"target_dimensionality": 3.0}
    primordial_cond, fundamental_params = await phi_engine.infer_primordial_conditions_and_parameters(
        refined_hypo.rule_definition, obs_constraints
    )
    assert fundamental_params is not None

    # 5. FS-142: Self-Comprehension Phase
    rcme = ReflexiveCathedralMetacognitiveEngine(mock_codex, intel, fundamental_params)
    self_comp_result = await rcme.initiate_self_comprehension_phase()
    assert self_comp_result["phase_initiated"] is True

    await asyncio.sleep(0.5)
    reflexive_model = rcme.reflexive_models[0]

    # 6. FS-143: Convergence Declaration
    cdf = ConvergenceDeclarationFramework(mock_codex, intel, fundamental_params, reflexive_model)
    declaration = await cdf.prepare_convergence_declaration()
    assert declaration.version == "1.0"

    full_text = declaration.generate_full_text()
    assert "DECLARAÇÃO DE CONVERGÊNCIA" in full_text
