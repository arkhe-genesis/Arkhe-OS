import pytest
import sys
import os

# Ajustar PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Importar o módulo diretamente adicionando o caminho dele
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../substrates/300-399_foundations/substrato_369_mainnet/')))

from cross_chain_bridge import CrossChainBridge, InvariantOracle

GHOST = 0.5773502691896257
LOOPSEAL = 0.3490658503988659
GAP_SOVEREIGN = 0.9999

def test_invariant_oracle():
    oracle = InvariantOracle()
    assert oracle.validate_block({"avg_phi_c": 0.85}) == True
    assert oracle.validate_block({"avg_phi_c": 0.5}) == False
    assert oracle.validate_block({"avg_phi_c": 1.0}) == False

def test_bridge_anchor():
    bridge = CrossChainBridge("http://aeneid", "http://ethereum")
    result = bridge.anchor_merkle_root(16)

    assert result["status"] == "anchored"
    assert result["aeneid_block"] == 16
    assert "ethereum_tx" in result
    assert "proof_hash" in result

def test_bridge_sync_state():
    bridge = CrossChainBridge("http://aeneid", "http://ethereum")

    result_mou = bridge.sync_state("mou_ratification", {"mou_id": 1})
    assert result_mou["status"] == "synced"
    assert result_mou["type"] == "mou_ratification"

    result_error = bridge.sync_state("invalid_state", {})
    assert "error" in result_error
