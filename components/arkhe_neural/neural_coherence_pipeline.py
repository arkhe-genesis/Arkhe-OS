import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class NeuralTokenizerConfig:
    window_size: int = 256
    stride: int = 32
    embedding_dim: int = 2048
    use_continuous_emb: bool = True
    codebook_size: int = 16384

class VectorQuantizer(nn.Module):
    def __init__(self, num_embeddings: int, embedding_dim: int):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim

    def forward(self, z: torch.Tensor, codebook: torch.Tensor) -> tuple:
        z_flat = z.reshape(-1, self.embedding_dim)
        distances = (
            torch.sum(z_flat**2, dim=1, keepdim=True)
            - 2 * torch.matmul(z_flat, codebook.T)
            + torch.sum(codebook**2, dim=1)
        )
        indices = torch.argmin(distances, dim=1)
        quantized = codebook[indices]
        quantized = quantized.reshape_as(z)
        indices = indices.reshape(z.shape[:-1])
        return quantized, indices

class NeuralSignalProcessor(nn.Module):
    def __init__(self, config: NeuralTokenizerConfig, mode: str = 'continuous', device='cpu'):
        super().__init__()
        self.config = config
        self.mode = mode
        self.device = device

        if mode == 'continuous':
            self.projection = nn.Linear(config.window_size, config.embedding_dim, bias=False)
        else:
            self.codebook = nn.Embedding(config.codebook_size, config.embedding_dim)
            self.encoder = nn.Sequential(
                nn.Linear(config.window_size, config.embedding_dim // 2),
                nn.GELU(),
                nn.Linear(config.embedding_dim // 2, config.embedding_dim)
            )
            self.quantizer = VectorQuantizer(config.codebook_size, config.embedding_dim)
        self.to(device)

    def forward(self, signal: np.ndarray) -> torch.Tensor:
        if signal.ndim == 1:
            signal = signal.reshape(1, -1)

        signal = signal.astype(np.float32)
        num_channels, total_len = signal.shape

        windows = []
        for ch in range(num_channels):
            for start in range(0, total_len - self.config.window_size + 1, self.config.stride):
                window = signal[ch, start:start+self.config.window_size]
                w_mean, w_std = window.mean(), window.std() + 1e-8
                window = (window - w_mean) / w_std
                windows.append(window)

        if not windows:
            # Fallback for short signals
            pad_len = max(0, self.config.window_size - total_len)
            signal_padded = np.pad(signal, ((0, 0), (0, pad_len)))
            windows = [signal_padded[0, :self.config.window_size]]

        windows = np.stack(windows)
        x = torch.from_numpy(windows).unsqueeze(0).to(self.device)

        if self.mode == 'continuous':
            embeddings = self.projection(x)
            return embeddings
        else:
            encoded = self.encoder(x)
            quantized, token_ids = self.quantizer(encoded, self.codebook.weight)
            return token_ids

def compute_omega_from_logits(logits: torch.Tensor) -> torch.Tensor:
    """Calcula Ω = 1 / (1 + H_norm)"""
    probs = F.softmax(logits.float(), dim=-1)
    H = -(probs * torch.log(probs + 1e-10)).sum(dim=-1).mean(dim=-1)
    H_max = np.log(logits.size(-1))
    omega = 1.0 / (1.0 + (H / H_max))
    return omega
