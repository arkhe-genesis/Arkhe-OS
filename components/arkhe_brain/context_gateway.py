import torch
import torch.nn as nn
import numpy as np
from geo_llm import GeoLLMLayer

class ContextCompactor(nn.Module):
    """
    Context Compactor based on GeoLLM O(1) state representation.
    Compresses a sequence of embeddings into a single geometric state vector in H_eta.

    Mirroring the Compresr-ai 'instant history compaction' for the Arkhe(n) Bio-Quantum architecture.
    """
    def __init__(self, embed_dim: int):
        super().__init__()
        self.geo_layer = GeoLLMLayer(embed_dim)

    def compact(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, seq_len, embed_dim)
        Returns: (batch, 3) complex64 tensor representing the cumulative state in H_eta.
        """
        B, S, D = x.shape
        device = x.device

        # 1. Map to geometric space H_eta
        h = self.geo_layer.proj_in(x).to(torch.complex64) # (B, S, 3)

        # 2. Phasing logic (Tribonacci SL(3, Z))
        # This gives each token a unique 'positional' phase based on lambda2
        phase_factor = self.geo_layer.lambda2 / np.abs(self.geo_layer.lambda2)
        powers = torch.arange(S, device=device).float()
        phase_powers = torch.pow(phase_factor, powers).unsqueeze(0).unsqueeze(-1) # (1, S, 1)

        # 3. Apply phasing and compute cumulative sum (O(1) update)
        h_phased = h * phase_powers # (B, S, 3)
        state = torch.cumsum(h_phased, dim=1) # (B, S, 3)

        # 4. Return the final cumulative state (the compressed "memory")
        # This state projection contains the entire history projected onto the spectral base.
        return state[:, -1, :]

    def should_compact(self, history_len: int, threshold: int = 5) -> bool:
        """
        Triggers background compaction when the history length exceeds the threshold.
        """
        return history_len >= threshold

if __name__ == "__main__":
    print("🜏 Arkhe Context Compactor Initialized.")
    embed_dim = 64
    compactor = ContextCompactor(embed_dim)

    # Simulate a history of 10 reports
    dummy_history = torch.randn(1, 10, embed_dim)
    compressed_state = compactor.compact(dummy_history)

    print(f"Original sequence shape: {dummy_history.shape}")
    print(f"Compressed state shape: {compressed_state.shape}")
    print(f"Compressed State (H_eta projection):\n{compressed_state}")
