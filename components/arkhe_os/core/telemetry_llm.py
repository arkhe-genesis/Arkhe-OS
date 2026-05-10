"""
arkhe_os/core/telemetry_llm.py
Mini-LLM auditável para aprender padrões de gameplay tokenizados.
Implementa as cinco invariantes éticas (I1-I5).
"""

import json
import torch
import torch.nn as nn
from dataclasses import dataclass
from typing import Dict, List, Any

FORBIDDEN_FIELDS = {
    "player_id", "raw_player_id", "ip", "email",
    "name", "chat_text", "precise_location",
}

SAFE_GAME_ACTIONS = {
    "spawn_enemy", "spawn_powerup", "adjust_music",
    "shift_temperature", "increase_entropy",
    "decrease_entropy", "narrative_echo",
}

@dataclass
class TelemetryConfig:
    vocab_size: int = 512
    context_length: int = 64
    embed_dim: int = 128
    num_heads: int = 4
    num_layers: int = 4
    seed: int = 1618

class TelemetrySanitizer:
    def sanitize(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if event.get("consent") is not True:
            raise ValueError("Telemetry rejected: consent is required.")
        clean = {k: v for k, v in event.items() if k not in FORBIDDEN_FIELDS}
        return clean

class GameplayTokenizer:
    def __init__(self):
        self.token_to_id = {"<PAD>": 0, "<UNK>": 1, "<BOS>": 2, "<EOS>": 3}
        self.id_to_token = {v: k for k, v in self.token_to_id.items()}

    def _add_token(self, token: str) -> int:
        if token not in self.token_to_id:
            idx = len(self.token_to_id)
            self.token_to_id[token] = idx
            self.id_to_token[idx] = token
        return self.token_to_id[token]

    def bucket_float(self, name: str, value: float) -> str:
        bucket = int(max(0, min(10, round(value * 10))))
        return f"{name}:bucket_{bucket}"

    def encode_event(self, event: Dict[str, Any]) -> List[int]:
        tokens = ["<BOS>", f"event:{event.get('event_type', 'unknown')}"]
        for key in ["coherence", "entropy", "temperature"]:
            if key in event:
                tokens.append(self.bucket_float(key, float(event[key])))
        tokens.append("<EOS>")
        return [self._add_token(t) for t in tokens]

class MiniTelemetryLLM(nn.Module):
    def __init__(self, config: TelemetryConfig):
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.embed_dim)
        self.position_embedding = nn.Embedding(config.context_length, config.embed_dim)
        layer = nn.TransformerEncoderLayer(d_model=config.embed_dim, nhead=config.num_heads, batch_first=True)
        self.transformer = nn.TransformerEncoder(layer, num_layers=config.num_layers)
        self.output = nn.Linear(config.embed_dim, config.vocab_size)

    def forward(self, x):
        seq_len = x.shape[1]
        pos = torch.arange(seq_len, device=x.device).unsqueeze(0)
        h = self.token_embedding(x) + self.position_embedding(pos)
        h = self.transformer(h)
        return self.output(h)
