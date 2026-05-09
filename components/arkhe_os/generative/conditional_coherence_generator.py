import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import time
import hashlib

@dataclass
class GenerationCondition:
    current_phi_c: float
    target_phi_c: Optional[float]
    time_horizon_gyr: float
    zone_context: str
    mission_criticality: float
    external_perturbations: Optional[Dict[str, float]]
    creativity_temperature: float = 0.7

class CoherenceShaderParams:
    def __init__(self, params: Dict[str, float]):
        self.params = params

class ConditionalCoherenceVAE(nn.Module):
    def __init__(self, latent_dim=64, condition_dim=32, hidden_dim=256, image_channels=3, image_size=256):
        super().__init__()
        self.latent_dim = latent_dim
        self.condition_dim = condition_dim
        self.encoder = nn.Sequential(
            nn.Conv2d(image_channels + 32, 64, 4, 2, 1), nn.ReLU(),
            nn.Conv2d(64, 128, 4, 2, 1), nn.ReLU(),
            nn.Conv2d(128, 256, 4, 2, 1), nn.ReLU(),
            nn.Conv2d(256, 512, 4, 2, 1), nn.ReLU(),
        )
        self.fc_mu = nn.Linear(512 * 16 * 16 + 256, latent_dim)
        self.fc_logvar = nn.Linear(512 * 16 * 16 + 256, latent_dim)
        self.fc_decode = nn.Linear(latent_dim + 256, 512 * 16 * 16)
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(512, 256, 4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(256, 128, 4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(64, image_channels, 4, 2, 1), nn.Sigmoid(),
        )
        self.condition_projector = nn.Sequential(
            nn.Linear(condition_dim, 128), nn.ReLU(), nn.Linear(128, 256),
        )

    def encode(self, image, condition):
        B, _, H, W = image.shape

        cond_spatial = condition.unsqueeze(-1).unsqueeze(-1).expand(-1, self.condition_dim, H, W)


        x = torch.cat([image, cond_spatial], dim=1) # Note: condition is expected to be [B, 1] if dim=1 or we reduce it

        features = self.encoder(x)
        features_flat = features.view(B, -1)
        cond_embed = self.condition_projector(condition)
        combined = torch.cat([features_flat, cond_embed], dim=1)
        return self.fc_mu(combined), self.fc_logvar(combined)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z, condition):
        B = z.shape[0]
        cond_embed = self.condition_projector(condition)

        B = z.shape[0]
        cond_embed = self.condition_projector(condition)
        combined = torch.cat([z, cond_embed], dim=1)

        features = self.fc_decode(combined).view(B, 512, 16, 16)
        return self.decoder(features)

    def forward(self, image, condition):
        mu, logvar = self.encode(image, condition)
        z = self.reparameterize(mu, logvar)
        return self.decode(z, condition), mu, logvar

    def sample(self, condition, n_samples=1, temperature=1.0):
        B = condition.shape[0] if condition.dim() > 1 else 1
        z = torch.randn(B * n_samples, self.latent_dim, device=condition.device) * temperature
        return self.decode(z, condition.repeat_interleave(n_samples, dim=0))

class ShaderParameterTransformer(nn.Module):
    def __init__(self, latent_dim=64, param_dim=16, embed_dim=128, num_heads=4, num_layers=3):
        super().__init__()
        self.input_proj = nn.Linear(latent_dim, embed_dim)
        encoder_layer = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=num_heads, dim_feedforward=embed_dim*4, dropout=0.1, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.param_head = nn.Sequential(nn.Linear(embed_dim, 64), nn.ReLU(), nn.Linear(64, param_dim), nn.Sigmoid())
        self.param_dim = param_dim

    def forward(self, latent):
        x = self.input_proj(latent.unsqueeze(1))
        x = self.transformer(x)
        return self.param_head(x.squeeze(1))

class ConditionalCoherenceGenerator:
    def __init__(self, latent_dim=64, condition_dim=32, shader_param_dim=16, device='cpu'):
        self.device = device
        self.vae = ConditionalCoherenceVAE(latent_dim, condition_dim).to(device)
        self.param_transformer = ShaderParameterTransformer(latent_dim, shader_param_dim).to(device)
        self.condition_encoder = nn.Sequential(nn.Linear(8, 32), nn.ReLU(), nn.Linear(32, condition_dim)).to(device)

    def encode_condition(self, cond):
        features = [cond.current_phi_c, cond.target_phi_c or cond.current_phi_c, min(1.0, cond.time_horizon_gyr / 10.0), cond.mission_criticality, cond.creativity_temperature]
        features.extend(list(cond.external_perturbations.values())[:3] if cond.external_perturbations else [0.0]*3)
        while len(features) < 8: features.append(0.0)
        features_tensor = torch.tensor(features[:8], dtype=torch.float32, device=self.device)
        with torch.no_grad():
            return self.condition_encoder(features_tensor.unsqueeze(0))

    def generate_coherence_state(self, condition, n_variations=3, return_params=True):
        self.vae.eval()
        self.param_transformer.eval()
        cond_embed = self.encode_condition(condition)
        with torch.no_grad():
            images = self.vae.sample(cond_embed, n_samples=n_variations, temperature=condition.creativity_temperature)
            z_mean = self.vae.encode(images[:1], cond_embed.repeat(1, 1))[0]
            shader_params_raw = self.param_transformer(z_mean)
            param_names = ['fractal_iterations', 'rotation_speed', 'color_shift', 'noise_scale', 'vortex_density', 'radial_bias', 'angular_frequency', 'decay_rate', 'symmetry_factor', 'contrast_boost', 'saturation', 'brightness', 'temporal_smoothing', 'edge_enhancement', 'depth_factor', 'coherence_threshold']
            params_dict = {name: shader_params_raw[0, i].item() for i, name in enumerate(param_names)}
        generated_image = images[0].permute(1, 2, 0).cpu()
        if return_params:
            return generated_image, CoherenceShaderParams(params_dict)
        return generated_image
