import pytest
import numpy as np
import torch
from arkhe_os.core.bio_compiler import BiologicalTopologicalCompiler
from arkhe_os.core.tokenized_consciousness import TokenizedConsciousness
from arkhe_os.core.cosmic_tokenizer import AutopoieticCosmicTokenizer
from arkhe_os.core.gameplay_meta_attention import CosmicUnconsciousMapper
from arkhe_os.core.telemetry_llm import GameplayTokenizer, MiniTelemetryLLM, TelemetryConfig
from arkhe_os.core.scaffold import ScaffoldState

def test_bio_compiler_logic():
    compiler = BiologicalTopologicalCompiler()
    prog = ['sigma_1', 'sigma_2', 'gamma_commutator']
    response = compiler.simulate_eeg_response(prog)
    fidelity = compiler.verify_program_fidelity(response, prog)
    assert 0.0 <= fidelity <= 1.0
    cs = compiler.extract_cs_invariant(fidelity)
    assert cs <= 0.618

def test_tokenized_selection_coherence():
    tokenizer = TokenizedConsciousness()
    res = tokenizer.conscious_collapse([1, 2, 3])
    m = tokenizer.get_coherence_from_entropy(res['entropy'])
    assert 0.0 <= m <= 1.0

def test_cosmic_autopoiesis():
    tokenizer = AutopoieticCosmicTokenizer()
    initial_temp = tokenizer.temperature
    res = tokenizer.run_autopoietic_step([{'type': 'particle', 'energy': 5}], 0.5)
    assert res['temperature'] != initial_temp
    assert 0.0 <= res['coherence_M'] <= 1.0

def test_gameplay_matter_antimatter_bias():
    tk = GameplayTokenizer()
    mapper = CosmicUnconsciousMapper(tk)
    # Simulate high coherence telemetry -> matter bias
    logits = torch.randn(512)
    # Favor high coherence bucket
    coh_token = tk.bucket_float("coherence", 0.9)
    tk._add_token(coh_token)
    logits[tk.token_to_id[coh_token]] += 10.0

    mapper.record_prediction(logits)
    bias = mapper.detect_matter_antimatter_bias()
    assert bias > 0 # Should detect matter bias

@pytest.mark.asyncio
async def test_scaffold_unified_v68():
    scaffold = ScaffoldState()
    # Check v∞.68 members
    assert hasattr(scaffold, 'bio_compiler')
    assert hasattr(scaffold, 'tokenizer_conscious')
    assert hasattr(scaffold, 'cosmic_tokenizer')
    assert hasattr(scaffold, 'unconscious_mapper')

    m, phase = await scaffold.update_coherence()
    assert 0.0 <= m <= 1.0
    # Stability check: should be in healthy range
    assert m > 0.60
