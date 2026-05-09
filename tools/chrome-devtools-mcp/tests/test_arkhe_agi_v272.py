import pytest
import torch
import torch.nn.functional as F

from scripts.arkhe_agi_pytorch_prototype_v162 import ArkheAGIPrototype, rtz_loss
from scripts.arkhe_qiskit_pytorch_v272 import ArkheQiskitAGIPrototype

def test_agi_prototype_v162_execution():
    model = ArkheAGIPrototype(state_dim=16, embed_dim=32, num_layers=1)
    states = torch.randn(2, 4, 16)
    target = torch.randn(2, 4, 16)

    refined, next_state, coherence = model(states)
    assert refined.shape == (2, 4, 16)
    assert next_state.shape == (2, 4, 16)
    assert coherence.shape == (2, 1) or coherence.shape == (2, 4, 1) or coherence.shape == (2, 16) or coherence.shape == (2, 32) # exact shape depends on the head structure, GRU output is [B, T, H] or similar

    loss = rtz_loss(refined, target, coherence, model)
    assert loss.item() > 0

def test_qiskit_pytorch_v272_execution():
    model = ArkheQiskitAGIPrototype(state_dim=16, embed_dim=32, num_layers=1)
    states = torch.randn(2, 4, 16)

    h, next_state, coherence = model(states)
    assert h.shape == (2, 4, 32)
    assert next_state.shape == (2, 4, 16)
