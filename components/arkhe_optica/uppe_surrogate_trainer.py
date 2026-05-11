# arkhe_optica/uppe_surrogate_trainer.py
import torch
import torch.nn as nn

class UPPEPhysicsSurrogate(nn.Module):
    """
    Surrogate neural que aproxima a física do UPPE.
    """
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 3) # Output: sic_db, rho, eta
        )

    def forward(self, l_p, l_s, m, ratio):
        x = torch.stack([l_p.float(), l_s.float(), m, ratio], dim=1)
        return self.net(x)
