import torch
import numpy as np
import pytest
from context_gateway import ContextCompactor
from latent_coherence import LatentCoherence

def test_compactor_output_shape():
    embed_dim = 64
    compactor = ContextCompactor(embed_dim)
    seq_len = 10
    batch_size = 2

    x = torch.randn(batch_size, seq_len, embed_dim)
    compressed = compactor.compact(x)

    # GeoLLM projects to 3D H_eta space
    assert compressed.shape == (batch_size, 3)
    assert compressed.dtype == torch.complex64

def test_compaction_coherence():
    """
    Verifies that the compressed context maintains a coherence λ2 >= 0.847
    when measured by the LatentCoherence module.
    """
    embed_dim = 64
    compactor = ContextCompactor(embed_dim)

    # Create a 'coherent' input history (using same reference vector logic as CoCT)
    ref_vec = torch.randn(1, 1, embed_dim)
    ref_vec /= torch.norm(ref_vec)

    # 10 steps of a coherent 'thought'
    history = ref_vec.repeat(1, 10, 1) + 0.01 * torch.randn(1, 10, embed_dim)

    compressed_state = compactor.compact(history)

    # For LatentCoherence.compute_metrics, we need (batch, dim)
    # We use the absolute magnitude or real part of the H_eta projection
    # Here we take the real part to check coherence in the physical embedding projection
    state_np = compressed_state.detach().real.numpy() # (1, 3)

    # Latent dimension is 3 (H_eta)
    metrics = LatentCoherence.compute_metrics(state_np, step=0, latent_dim=3)

    print(f"Compressed State Coherence λ2: {metrics.lambda2:.4f}")
    print(f"Status: {metrics.coherence_status}")

    # We expect the projection of a coherent history to be coherent in H_eta
    # Threshold λ2 >= 0.847
    assert metrics.lambda2 >= 0.847
    assert metrics.coherence_status in ["COHERENT", "EP_ATTAINED"]

def test_should_compact():
    compactor = ContextCompactor(64)
    assert compactor.should_compact(5, threshold=5) is True
    assert compactor.should_compact(4, threshold=5) is False
