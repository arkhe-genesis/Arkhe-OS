import pytest
import numpy as np
from src.quadrumvirato_261_264 import (
    ByzantineFaultTolerance, BFTPhase, CausalTensorSharding, CausalClock,
    QuantumCheckpointing, CheckpointState, PentaceneBackendInterface, PentaceneInterfaceStatus,
    PentaceneCommand
)

def test_bft_creation():
    bft = ByzantineFaultTolerance(node_id="test_node_1")
    assert bft.node_id == "test_node_1"

def test_causal_sharding():
    sharding = CausalTensorSharding(node_id="node_1")
    assert sharding.node_id == "node_1"

def test_checkpointing():
    checkpointing = QuantumCheckpointing(node_id="chk_node_1")
    assert checkpointing.node_id == "chk_node_1"

def test_pentacene_interface():
    interface = PentaceneBackendInterface(node_id="penta_node_1")
    assert interface.status == PentaceneInterfaceStatus.OFFLINE
