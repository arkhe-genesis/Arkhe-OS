import torch
import torch.distributed as dist
import arkhe_cuda

class DistributedResonanceSync:
    """
    Sincroniza a 'Massa Semântica' (ρ₁) através de múltiplas GPUs usando NCCL 
    antes de invocar os Fused Kernels da Camada 12.
    """
    def __init__(self, k1=0.015311, k2=0.05200, lam=0.001013, rho_eq=0.367879):
        self.k1 = k1
        self.k2 = k2
        self.lam = lam
        self.rho_eq = rho_eq
        self.is_distributed = dist.is_initialized()

    def compute_global_resonance(self, base_loss, local_param_tensor, rho_2_tokens):
        # 1. Normas locais (quadrado para soma pitagórica)
        # O tensor local_param_tensor é apenas o fragmento (shard) nesta GPU
        local_sq_norm = torch.sum(local_param_tensor ** 2)

        # 2. Sincronização em anel via NCCL (NVLink)
        if self.is_distributed:
            dist.all_reduce(local_sq_norm, op=dist.ReduceOp.SUM)
        
        # 3. Massa global real do modelo
        global_norm = torch.sqrt(local_sq_norm)

        # 4. Chamada ao Kernel CUDA (Layer 12) usando a norma global
        # Nota: assumindo que o kernel C++ foi atualizado para aceitar o float da norma diretamente
        arkhe_loss, phase, damping = arkhe_cuda.compute_with_norm(
            base_loss, 
            global_norm, 
            rho_2_tokens, 
            self.k1, self.k2, self.lam, self.rho_eq
        )

        return arkhe_loss, phase, damping
