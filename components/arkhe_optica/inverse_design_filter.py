# arkhe_optica/inverse_design_filter.py
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class FilterDesignConfig:
    design_length_um: float = 10.0
    n_points: int = 256
    lambda_min_um: float = 0.4
    lambda_max_um: float = 0.6
    n_wavelengths: int = 100
    n_low: float = 1.5
    n_high: float = 1.7

class SpectralFilterSimulator(nn.Module):
    def __init__(self, config: FilterDesignConfig):
        super().__init__()
        self.config = config
        self.dx = config.design_length_um / config.n_points
        self.wavelengths = torch.linspace(config.lambda_min_um, config.lambda_max_um, config.n_wavelengths)

    def compute_transmission(self, rho: torch.Tensor) -> torch.Tensor:
        n = self.config.n_low + rho * (self.config.n_high - self.config.n_low)
        phi = 2 * np.pi * n.unsqueeze(1) * self.dx / self.wavelengths.unsqueeze(0)
        transmission = torch.ones(self.config.n_wavelengths)
        for i in range(self.config.n_points - 1):
            R = ((n[i] - n[i+1]) / (n[i] + n[i+1] + 1e-8)) ** 2
            transmission = transmission * (1 - R)
        total_phase = phi.sum(dim=0)
        interference = 0.5 + 0.5 * torch.cos(total_phase)
        return torch.clamp(transmission * interference, 0.0, 1.0)

class InverseDesignFilterOptimizer(nn.Module):
    def __init__(self, config: FilterDesignConfig):
        super().__init__()
        self.config = config
        self.simulator = SpectralFilterSimulator(config)

    def forward(self, rho: torch.Tensor) -> torch.Tensor:
        return self.simulator.compute_transmission(rho)

    def optimize(self, target_transmission: torch.Tensor, n_iterations: int = 200) -> Dict:
        rho = 0.5 * torch.ones(self.config.n_points, requires_grad=True)
        optimizer = torch.optim.Adam([rho], lr=0.01)
        for _ in range(n_iterations):
            optimizer.zero_grad()
            T_pred = self.forward(torch.sigmoid(rho))
            loss = torch.nn.functional.mse_loss(T_pred, target_transmission)
            loss.backward()
            optimizer.step()
        rho_optimal = torch.sigmoid(rho).detach()
        return {'rho_optimal': rho_optimal, 'transmission_achieved': self.forward(rho_optimal).detach()}

    def to_liquid_crystal_director(self, rho: torch.Tensor) -> Dict:
        theta = torch.asin(torch.sqrt(torch.clamp(rho, 0.0, 1.0)))
        return {'theta_rad': theta.numpy().tolist(), 'n_effective': torch.sqrt(self.config.n_low**2 + (self.config.n_high**2 - self.config.n_low**2) * torch.sin(theta)**2).numpy().tolist()}
