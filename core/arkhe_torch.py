import torch
import torch.nn as nn

class CrystalSAE(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(768, 768)

    def forward(self, x):
        return x, x
