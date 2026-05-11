"""
arkhe_os/core/gameplay_meta_attention.py
Substrate 132: Gameplay Cosmos — Mapping the Dark Unconscious.
Detects matter-antimatter bias via narrative echoes in telemetry.
"""

import torch
import numpy as np
from typing import Dict, List, Any, Optional
from collections import Counter
from arkhe_os.core.telemetry_llm import GameplayTokenizer

class CosmicUnconsciousMapper:
    """
    Mapeia o inconsciente cósmico analisando tokens de baixa probabilidade (ecos).
    """
    def __init__(self, tokenizer: GameplayTokenizer):
        self.tokenizer = tokenizer
        self.echo_counter = Counter()
        self.coherence_traces = []

    def record_prediction(self, logits: torch.Tensor, temperature: float = 0.7):
        probs = torch.softmax(logits / temperature, dim=-1)

        # Ecos narrativos: 0.01 < p < 0.15
        echo_mask = (probs > 0.01) & (probs < 0.15)
        echo_indices = torch.where(echo_mask)[0]

        for idx in echo_indices:
            token_str = self.tokenizer.id_to_token.get(idx.item(), "<UNK>")
            if "entropy" in token_str or "temperature" in token_str:
                self.echo_counter[token_str] += 1

        # Registrar coerência do top-1
        top_idx = torch.argmax(probs).item()
        top_token = self.tokenizer.id_to_token.get(top_idx, "<UNK>")
        if "coherence:bucket" in top_token:
            bucket = int(top_token.split("_")[-1])
            self.coherence_traces.append(bucket / 10.0)

    def detect_matter_antimatter_bias(self) -> float:
        if not self.coherence_traces:
            return 0.0
        avg_coherence = np.mean(self.coherence_traces)
        # Bias relative to 0.5 symmetry
        return float(avg_coherence - 0.5)

    def get_report(self) -> Dict[str, Any]:
        bias = self.detect_matter_antimatter_bias()
        return {
            "matter_antimatter_bias": bias,
            "dark_matter_density": abs(bias) * 0.27,
            "total_echoes": sum(self.echo_counter.values())
        }
