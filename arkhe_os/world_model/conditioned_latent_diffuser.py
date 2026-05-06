import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Tuple

class ConditionedLatentDiffuser(nn.Module):
    """Difusor latente condicionado por contexto do World Model + estado recorrente."""

    def __init__(
        self,
        latent_dim: int = 256,
        context_dim: int = 768,
        recurrent_dim: int = 512,
        num_timesteps: int = 100,
        beta_schedule: str = 'linear',
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.context_dim = context_dim
        self.recurrent_dim = recurrent_dim
        self.T = num_timesteps

        # Scheduler de ruído
        if beta_schedule == 'linear':
            self.betas = torch.linspace(1e-4, 0.02, num_timesteps)
        elif beta_schedule == 'cosine':
            # Schedule cosseno para melhor qualidade em timesteps iniciais
            s = 0.008
            steps = np.linspace(0, num_timesteps, num_timesteps + 1)
            alphas_cumprod = np.cos((steps / num_timesteps + s) / (1 + s) * np.pi / 2) ** 2
            alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
            self.betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
            self.betas = torch.from_numpy(self.betas).float()
        else:
            raise ValueError(f"Unknown beta_schedule: {beta_schedule}")

        self.alphas = 1 - self.betas
        self.alpha_bars = torch.cumprod(self.alphas, dim=0)

        # Denoiser: UNet-like para espaço latente
        self.denoiser = LatentDenoiserUNet(
            input_dim=latent_dim,
            context_dim=context_dim + recurrent_dim + context_dim // 4,  # +t_emb para timestep embedding
            hidden_dims=[512, 1024, 512],
            num_res_blocks=2,
        )

        # Projeção para condicionamento composto
        self.condition_projector = nn.Linear(context_dim + recurrent_dim, context_dim + recurrent_dim)

    def forward_diffusion(self, z0: torch.Tensor, t: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Processo forward: adiciona ruído a z0 no timestep t."""
        # z0: [B, latent_dim], t: [B]
        alpha_bar_t = self.alpha_bars[t].view(-1, 1)  # [B, 1]
        noise = torch.randn_like(z0)
        zt = torch.sqrt(alpha_bar_t) * z0 + torch.sqrt(1 - alpha_bar_t) * noise
        return zt, noise

    def reverse_step(
        self,
        zt: torch.Tensor,
        t: int,
        context: torch.Tensor,
        recurrent_state: torch.Tensor,
        guidance_scale: float = 1.5,
    ) -> torch.Tensor:
        """Um passo do processo reverse de difusão."""
        # Preparar condicionamento composto
        composed_condition = torch.cat([context, recurrent_state], dim=-1)
        composed_condition = self.condition_projector(composed_condition)

        # Timestep embedding
        t_emb = _timestep_embedding(t, self.context_dim // 4).to(zt.device)
        t_emb = t_emb.unsqueeze(0).expand(zt.size(0), -1)  # [B, context_dim//4]

        # Condicionamento final
        full_condition = torch.cat([composed_condition, t_emb], dim=-1)

        # Prever ruído
        noise_pred = self.denoiser(zt, full_condition, t)

        # Coeficientes do scheduler
        alpha_t = self.alphas[t]
        alpha_bar_t = self.alpha_bars[t]
        beta_t = self.betas[t]

        # Guidance opcional (classifier-free)
        if guidance_scale != 1.0:
            # Prever também com condição nula para guidance
            null_condition = torch.zeros_like(full_condition)
            noise_pred_null = self.denoiser(zt, null_condition, t)
            noise_pred = noise_pred_null + guidance_scale * (noise_pred - noise_pred_null)

        # Coeficiente para subtração do ruído previsto
        coef = (1 - alpha_t) / torch.sqrt(1 - alpha_bar_t)

        # Atualizar z
        z_prev = (zt - coef * noise_pred) / torch.sqrt(alpha_t)

        # Adicionar ruído se não for o último passo
        if t > 0:
            sigma_t = torch.sqrt(beta_t)
            z_prev = z_prev + sigma_t * torch.randn_like(z_prev)

        return z_prev

    def sample(
        self,
        context: torch.Tensor,
        recurrent_state: torch.Tensor,
        num_samples: int = 1,
        guidance_scale: float = 1.5,
        return_trajectory: bool = False,
    ) -> Tuple[torch.Tensor, Optional[list]]:
        """Amostra do processo reverse completo."""
        # Amostrar z_T ~ N(0, I)
        z = torch.randn(num_samples, self.latent_dim, device=context.device)

        trajectory = [z.clone()] if return_trajectory else None

        # Loop de reverse diffusion
        for t in reversed(range(self.T)):
            z = self.reverse_step(z, t, context, recurrent_state, guidance_scale)
            if return_trajectory:
                trajectory.append(z.clone())

        if return_trajectory:
            return z, trajectory
        return z, None

class LatentDenoiserUNet(nn.Module):
    """UNet simplificado para denoising em espaço latente."""

    def __init__(
        self,
        input_dim: int,
        context_dim: int,
        hidden_dims: list,
        num_res_blocks: int = 2,
    ):
        super().__init__()
        # Encoder
        self.input_proj = nn.Linear(input_dim, hidden_dims[0])
        self.enc_blocks = nn.ModuleList()
        curr_dim = hidden_dims[0]
        for next_dim in hidden_dims[1:]:
            self.enc_blocks.extend([
                ResBlockWithCondition(curr_dim, context_dim) for _ in range(num_res_blocks)
            ])
            self.enc_blocks.append(nn.Linear(curr_dim, next_dim))
            curr_dim = next_dim

        # Bottleneck
        self.bottleneck = ResBlockWithCondition(curr_dim, context_dim)

        # Decoder (simétrico)
        self.dec_blocks = nn.ModuleList()
        for prev_dim, next_dim in zip(reversed(hidden_dims), reversed(hidden_dims[:-1] + [input_dim])):
            self.dec_blocks.extend([
                ResBlockWithCondition(prev_dim + next_dim, context_dim) for _ in range(num_res_blocks)
            ])
            if next_dim != input_dim:
                self.dec_blocks.append(nn.Linear(prev_dim, next_dim))

        self.output_proj = nn.Linear(hidden_dims[0], input_dim)

    def forward(self, x: torch.Tensor, condition: torch.Tensor, t: int) -> torch.Tensor:
        """Forward do denoiser."""
        # Encoder pass
        skips = []
        h = self.input_proj(x)
        for block in self.enc_blocks:
            if isinstance(block, ResBlockWithCondition):
                h = block(h, condition, t)
            else:
                h = block(h)
            skips.append(h)

        # Bottleneck
        h = self.bottleneck(h, condition, t)

        # Decoder pass com skip connections
        for block, skip in zip(self.dec_blocks, reversed(skips)):
            if isinstance(block, ResBlockWithCondition):
                h = torch.cat([h, skip], dim=-1)
                h = block(h, condition, t)
            else:
                h = block(torch.cat([h, skip], dim=-1))

        return self.output_proj(h)

class ResBlockWithCondition(nn.Module):
    """Bloco residual condicionado por contexto e timestep."""

    def __init__(self, hidden_dim: int, context_dim: int):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.fc1 = nn.Linear(hidden_dim, hidden_dim * 4)
        self.norm2 = nn.LayerNorm(hidden_dim * 4)
        self.fc2 = nn.Linear(hidden_dim * 4, hidden_dim)

        # Condicionamento
        self.cond_proj = nn.Linear(context_dim, hidden_dim)
        self.timestep_proj = nn.Linear(hidden_dim // 4, hidden_dim)

        self.gelu = nn.GELU()

    def forward(self, x: torch.Tensor, condition: torch.Tensor, t: int) -> torch.Tensor:
        # Normalização e primeira transformação
        h = self.norm1(x)
        h = self.gelu(self.fc1(h))
        h = self.norm2(h)

        # Injeção de condicionamento
        cond_emb = self.cond_proj(condition)
        t_emb = self.timestep_proj(_timestep_embedding(t, self.timestep_proj.in_features).to(x.device))
        h = h + cond_emb + t_emb

        # Segunda transformação + residual
        h = self.gelu(self.fc2(h))
        return x + h

def _timestep_embedding(t: int, dim: int, max_period: int = 10000) -> torch.Tensor:
    """Helper para embedding de timestep."""
    half = dim // 2
    freqs = torch.exp(
        -np.log(max_period) * torch.arange(start=0, end=half, dtype=torch.float32) / half
    )
    args = torch.tensor([t], dtype=torch.float32) * freqs
    embedding = torch.cat([torch.cos(args), torch.sin(args)], dim=0)
    if dim % 2:
        embedding = torch.cat([embedding, torch.zeros(1)], dim=0)
    return embedding
