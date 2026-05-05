import torch
import torch.nn as nn

class Manifold5DFRC2G(nn.Module):
    def __init__(self, base_dim=4, learnable=True):
        super().__init__()
        self.base_dim = base_dim
        self.total_dim = base_dim + 1
        self.learnable = learnable

        if learnable:
            self.L_base = nn.Parameter(torch.eye(base_dim, dtype=torch.float64))
            self.log_lambda = nn.Parameter(torch.tensor(0.0, dtype=torch.float64))
        else:
            self.register_buffer('L_base', torch.eye(base_dim, dtype=torch.float64))
            self.register_buffer('log_lambda', torch.tensor(0.0, dtype=torch.float64))

    def get_metric(self):
        g_base = self.L_base @ self.L_base.T
        scale = torch.exp(-2 * self.log_lambda)

        g_5d = torch.zeros(self.total_dim, self.total_dim, dtype=torch.float64, device=self.L_base.device)
        g_5d[:self.base_dim, :self.base_dim] = g_base
        g_5d[self.base_dim, self.base_dim] = scale
        return g_5d

    def get_metric_inverse(self):
        g_5d = self.get_metric()
        return torch.inverse(g_5d)
