import torch
from .conditioned_latent_diffuser import ConditionedLatentDiffuser

class RedoxGuidedDiffuser(ConditionedLatentDiffuser):
    def __init__(self, *args, redox_dim: int = 128, **kwargs):
        super().__init__(*args, **kwargs)
        self.redox_dim = redox_dim

        # We replace the original condition projector to accept the redox state
        # Original: context_dim + recurrent_dim
        # New: context_dim + recurrent_dim + redox_dim
        self.condition_projector_redox = torch.nn.Linear(
            self.context_dim + self.recurrent_dim + self.redox_dim,
            self.context_dim + self.recurrent_dim
        )

        self.redox_encoder = torch.nn.Sequential(
            torch.nn.Linear(10, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, self.redox_dim)
        )

    def encode_redox_state(self, redox_state: dict) -> torch.Tensor:
        """
        redox_state = {
            "mitochondria": {"NADH/NAD+": 0.92, "ΔΨm": -180},
            "cytosol": {"GSH/GSSG": 100, "H2O2": 0.05}
        }
        """
        # Mocking flat vector generation from the dictionary
        flat_vector = torch.zeros(1, 10)
        if "mitochondria" in redox_state:
            flat_vector[0, 0] = redox_state["mitochondria"].get("NADH/NAD+", 0.0)
            flat_vector[0, 1] = redox_state["mitochondria"].get("ΔΨm", 0.0)
        if "cytosol" in redox_state:
            flat_vector[0, 2] = redox_state["cytosol"].get("GSH/GSSG", 0.0)
            flat_vector[0, 3] = redox_state["cytosol"].get("H2O2", 0.0)

        return self.redox_encoder(flat_vector)

    def reverse_step(
        self,
        zt: torch.Tensor,
        t: int,
        context: torch.Tensor,
        recurrent_state: torch.Tensor,
        redox_state: dict = None,
        guidance_scale: float = 1.5,
    ) -> torch.Tensor:
        if redox_state is None:
            # Fallback if no redox state is provided
            return super().reverse_step(zt, t, context, recurrent_state, guidance_scale)

        redox_embedding = self.encode_redox_state(redox_state).to(zt.device)

        # Preparar condicionamento composto com redox
        composed_condition = torch.cat([context, recurrent_state, redox_embedding], dim=-1)
        composed_condition = self.condition_projector_redox(composed_condition)

        # Timestep embedding (replicating super().reverse_step logic to use the new condition)
        # Note: We must replicate some logic from super().reverse_step since we can't easily
        # inject just the composed_condition into it.

        t_emb = self._local_timestep_embedding(t, self.context_dim // 4).to(zt.device)
        t_emb = t_emb.unsqueeze(0).expand(zt.size(0), -1)

        full_condition = torch.cat([composed_condition, t_emb], dim=-1)

        noise_pred = self.denoiser(zt, full_condition, t)

        alpha_t = self.alphas[t]
        alpha_bar_t = self.alpha_bars[t]
        beta_t = self.betas[t]

        if guidance_scale != 1.0:
            null_condition = torch.zeros_like(full_condition)
            noise_pred_null = self.denoiser(zt, null_condition, t)
            noise_pred = noise_pred_null + guidance_scale * (noise_pred - noise_pred_null)

        coef = (1 - alpha_t) / torch.sqrt(1 - alpha_bar_t)
        z_prev = (zt - coef * noise_pred) / torch.sqrt(alpha_t)

        if t > 0:
            sigma_t = torch.sqrt(beta_t)
            z_prev = z_prev + sigma_t * torch.randn_like(z_prev)

        return z_prev

    def _local_timestep_embedding(self, t: int, dim: int, max_period: int = 10000) -> torch.Tensor:
        import numpy as np
        half = dim // 2
        freqs = torch.exp(
            -np.log(max_period) * torch.arange(start=0, end=half, dtype=torch.float32) / half
        )
        args = torch.tensor([t], dtype=torch.float32) * freqs
        embedding = torch.cat([torch.cos(args), torch.sin(args)], dim=0)
        if dim % 2:
            embedding = torch.cat([embedding, torch.zeros(1)], dim=0)
        return embedding

    def sample_with_redox(
        self,
        context: torch.Tensor,
        recurrent_state: torch.Tensor,
        redox_state: dict,
        num_samples: int = 1,
        guidance_scale: float = 1.5,
    ) -> torch.Tensor:
        z = torch.randn(num_samples, self.latent_dim, device=context.device)

        for t in reversed(range(self.T)):
            z = self.reverse_step(z, t, context, recurrent_state, redox_state, guidance_scale)

        return z
