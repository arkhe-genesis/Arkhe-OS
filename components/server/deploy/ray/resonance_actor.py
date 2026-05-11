import ray
import torch
# import arkhe_cuda
from typing import Dict, List

@ray.remote(num_gpus=1)
class ResonanceActor:
    """Ray Actor que calcula e agrega métricas de ressonância em cada GPU."""
    
    def __init__(self, model_params: int, device: str = "cuda"):
        self.model_params = model_params
        self.device = torch.device(device)
        self.tokens_processed = 0
        self.phase_history = []
        self.damping_history = []
    
    def compute(self, loss: float, param_tensor: torch.Tensor) -> Dict[str, float]:
        # Enviar tensor para GPU se necessário
        if param_tensor.device != self.device:
            param_tensor = param_tensor.to(self.device)
        loss_t = torch.tensor([loss], device=self.device)
        
        # Usar a extensão CUDA compilada
        # arkhe_loss, phase, damping = arkhe_cuda.compute(
        #     loss_t, param_tensor, self.tokens_processed,
        #     0.015311, 0.05200, 0.001013, 0.367879
        # )
        
        # Mock para simulação
        arkhe_loss = loss_t
        phase = torch.tensor([1.57])
        damping = torch.tensor([0.95])
        
        self.tokens_processed += 1  # simplificado
        self.phase_history.append(phase.item())
        self.damping_history.append(damping.item())
        
        return {
            "loss": arkhe_loss.item(),
            "phase": phase.item(),
            "damping": damping.item()
        }
    
    def aggregate_phase(self) -> float:
        """Retorna fase média (pode ser usada para early stopping)."""
        return sum(self.phase_history) / max(1, len(self.phase_history))
    
    def reset(self):
        self.tokens_processed = 0
        self.phase_history.clear()
        self.damping_history.clear()
