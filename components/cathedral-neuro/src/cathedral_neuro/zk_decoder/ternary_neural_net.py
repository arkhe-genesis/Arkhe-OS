"""
ternary_neural_net.py — Rede neural ternária para decodificação neural
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Union

class TernaryLinear(nn.Module):
    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.weight_fp = nn.Parameter(torch.randn(out_features, in_features) * 0.02)
        self.register_buffer("weight_ternary", torch.zeros_like(self.weight_fp))
        self.bias = nn.Parameter(torch.zeros(out_features)) if bias else None

    def forward(self, x):
        return F.linear(x, self.weight_ternary, self.bias)

    def get_ternary_weights(self):
        return self.weight_ternary.cpu().numpy()

class TernaryNeuroDecoder(nn.Module):
    def __init__(self, n_channels, n_timepoints, n_classes, hidden_dim=64):
        super().__init__()
        self.fc1 = TernaryLinear(n_channels * n_timepoints, hidden_dim)
        self.fc2 = TernaryLinear(hidden_dim, n_classes)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        return self.fc2(x)

    def decode_with_confidence(self, eeg_input):
        self.eval()
        x = torch.from_numpy(eeg_input).float().unsqueeze(0)
        with torch.no_grad():
            logits = self.forward(x)
            probs = F.softmax(logits, dim=1).numpy()[0]
        return {"predicted_class": int(np.argmax(probs)), "confidence": float(np.max(probs))}

    def export_for_zk_proof(self):
        return {"weights": {"fc1": self.fc1.get_ternary_weights().tolist()}}
