import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional

class ArkheHybridLoss(nn.Module):
    def __init__(
        self,
        vocab_size: int = 32000,
        state_dim: int = 256,
        lambda_ce: float = 1.0,
        lambda_mse: float = 0.5,
        lambda_causal: float = 0.3,
        lambda_k: float = 1e-5,           # Novo parâmetro
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.state_dim = state_dim
        self.lambda_ce = lambda_ce
        self.lambda_mse = lambda_mse
        self.lambda_causal = lambda_causal
        self.lambda_k = lambda_k
        self.ce_loss = nn.CrossEntropyLoss(ignore_index=-100)
        self.mse_loss = nn.MSELoss()

    def forward(self, predictions, targets, model=None, causal_model=None):
        losses = {}

        # 1. CrossEntropy — linguagem
        if "logits" in predictions and "tokens" in targets:
            logits = predictions["logits"].reshape(-1, self.vocab_size)
            tokens = targets["tokens"].reshape(-1)
            losses["ce"] = self.ce_loss(logits, tokens)
        else:
            losses["ce"] = torch.tensor(0.0, device=predictions["logits"].device if "logits" in predictions else "cpu")

        # 2. MSE — estado físico
        if "state_pred" in predictions and "state_true" in targets:
            losses["mse"] = self.mse_loss(predictions["state_pred"], targets["state_true"])
        else:
            losses["mse"] = torch.tensor(0.0, device=predictions["state_pred"].device if "state_pred" in predictions else "cpu")

        # 3. Causal loss — estrutura DAG + predição contrafactual
        if causal_model is not None and "causal_pred" in predictions and "causal_true" in targets:
            losses["causal"] = causal_model.causal_loss(targets["causal_true"], predictions["causal_pred"])
        else:
            losses["causal"] = torch.tensor(0.0, device=predictions["logits"].device if "logits" in predictions else "cpu")

        # Adicionar Kolmogorov
        loss_k = torch.tensor(0.0)
        if model is not None:
            from .kolmogorov_regularizer import kolmogorov_regularizer
            loss_k = kolmogorov_regularizer(model)
        losses["k"] = loss_k
        losses["total"] = (self.lambda_ce * losses["ce"] +
                           self.lambda_mse * losses["mse"] +
                           self.lambda_causal * losses["causal"] +
                           self.lambda_k * losses["k"])
        return losses

class PhysicsConsistencyLoss(nn.Module):
    """
    Loss de consistência física: penaliza violações de leis físicas.

    Ex: conservação de energia, momento, colisões elásticas.
    """
    def __init__(self):
        super().__init__()

    def forward(
        self,
        state_t: torch.Tensor,     # [batch, state_dim]
        state_t1: torch.Tensor,    # [batch, state_dim]
        action: torch.Tensor,      # [batch, action_dim]
        dt: float = 0.02,
    ) -> torch.Tensor:
        """
        Penaliza inconsistências físicas na transição de estado.

        Stub: em produção, usar simulador diferenciável (Brax/JAX)
        para computar gradientes físicos reais.
        """
        # Conservação de energia aproximada
        # E = ½mv² + mgh (simplificado)
        # Penalizar |E_t - E_t1| > threshold

        # Placeholder: diferença L2 entre estados consecutivos
        consistency = torch.mean((state_t1 - state_t - action * dt) ** 2)
        return consistency


class ContrastiveWorldLoss(nn.Module):
    """
    Loss contrastiva: distingue trajetórias reais de trajetórias impossíveis.

    Usado para treinar o modelo a reconhecer física "intuitiva" vs. violações.
    """
    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(
        self,
        real_emb: torch.Tensor,      # [batch, dim] — trajetória real
        fake_emb: torch.Tensor,      # [batch, dim] — trajetória impossível
        anchor_emb: torch.Tensor,    # [batch, dim] — descrição textual
    ) -> torch.Tensor:
        """
        InfoNCE: anchor (texto) deve estar mais próximo de real que de fake.
        """
        # Normalizar
        real_emb = F.normalize(real_emb, dim=-1)
        fake_emb = F.normalize(fake_emb, dim=-1)
        anchor_emb = F.normalize(anchor_emb, dim=-1)

        # Similaridades
        sim_real = torch.sum(anchor_emb * real_emb, dim=-1) / self.temperature
        sim_fake = torch.sum(anchor_emb * fake_emb, dim=-1) / self.temperature

        # Contrastive loss: log(exp(sim_real) / (exp(sim_real) + exp(sim_fake)))
        logits = torch.stack([sim_real, sim_fake], dim=-1)  # [batch, 2]
        labels = torch.zeros(anchor_emb.size(0), dtype=torch.long, device=anchor_emb.device)

        return F.cross_entropy(logits, labels)
