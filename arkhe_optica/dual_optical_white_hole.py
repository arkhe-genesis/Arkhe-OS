# arkhe_optica/dual_optical_white_hole.py
import torch
import torch.nn as nn
from typing import Dict

class DualOpticalWhiteHole(nn.Module):
    def __init__(self, spatial_surrogate: nn.Module, spectral_simulator: nn.Module):
        super().__init__()
        self.spatial_model = spatial_surrogate.eval()
        self.spectral_model = spectral_simulator.eval()

    def generate(self, spatial_targets: Dict[str, float], spectral_target: torch.Tensor, steps: int = 100) -> Dict:
        m = torch.tensor([6.0], requires_grad=True)
        ratio = torch.tensor([1.0], requires_grad=True)
        rho = 0.5 * torch.ones(self.spectral_model.config.n_points, requires_grad=True)
        optimizer = torch.optim.Adam([m, ratio, rho], lr=0.01)

        target_spatial = torch.tensor([[spatial_targets.get('sic_db', 20.0)/40.0], [spatial_targets.get('rho', 0.9)], [spatial_targets.get('eta', 0.8)]])

        for _ in range(steps):
            optimizer.zero_grad()
            l_p_t, l_s_t = torch.tensor([1.0]), torch.tensor([1.0])
            pred_spatial = self.spatial_model(l_p_t, l_s_t, m, ratio)
            pred_spectral = self.spectral_model.compute_transmission(torch.sigmoid(rho))
            loss = torch.nn.functional.mse_loss(pred_spatial, target_spatial) + torch.nn.functional.mse_loss(pred_spectral, spectral_target)
            loss.backward()
            optimizer.step()

        return {'m': m.item(), 'ratio': ratio.item(), 'rho': torch.sigmoid(rho).detach(), 'pred_spatial': pred_spatial.detach()}
