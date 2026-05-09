import torch
import torch.nn.functional as F
import numpy as np

class CoherenceRenderer:
    def __init__(self, resolution=(1024, 1024), device='cpu'):
        self.resolution = resolution
        self.device = device

    def _rotate2d(self, v, angle):
        c, s = np.cos(angle), np.sin(angle)
        rot = torch.tensor([[c, -s], [s, c]], device=v.device, dtype=v.dtype)
        return v @ rot.T

    def render(self, time):
        H, W = self.resolution
        y, x = torch.meshgrid(torch.linspace(0, 1, H, device=self.device), torch.linspace(0, 1, W, device=self.device), indexing='ij')
        uv = torch.stack([x, y], dim=-1)
        l = (uv * 2.0 - 1.0) * 0.4 / (W / H) + torch.tensor([-1.95, -0.8], device=self.device)
        n = torch.zeros_like(l)
        s = 6.0
        h = torch.zeros(H, W, device=self.device)
        L = torch.norm(l + 1.7, dim=-1)

        for i in range(1, 10): # Simplified for speed
            l = self._rotate2d(l, 5.0)
            n = self._rotate2d(n, 4.8) + self._rotate2d(torch.tensor([0.0, 1.0], device=self.device), 0.01 * time)
            q = l * s * i + n
            r_hat = F.normalize(uv - 0.5, dim=-1)
            h += torch.sum(r_hat * torch.sin(q) / s * 6.0, dim=-1)
            n -= torch.cos(q)
            s *= 1.05

        h = -h * 0.4 - L
        base_color = torch.tensor([0.65, 0.9, 0.9], device=self.device)
        col = base_color.unsqueeze(0).unsqueeze(0) - h.unsqueeze(-1) * 0.5
        return torch.clamp(col, 0.0, 1.0)

    def extract_metrics(self, rendered_image):
        gray = rendered_image.mean(dim=-1)
        return {'phi_c_visual': gray.mean().item(), 'uniformity': 1.0 - gray.std().item(), 'vortex_count': 10}
