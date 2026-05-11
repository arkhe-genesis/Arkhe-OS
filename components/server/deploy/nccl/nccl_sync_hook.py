import torch
import torch.distributed as dist
# import arkhe_cuda

class ResonanceSyncHook:
    """
    Hook que, antes de cada passo de otimização, sincroniza as normas
    dos parâmetros e recalcula a fase global.
    """
    def __init__(self, model, k1=0.015311, k2=0.05200, lam=0.001013, rho_eq=0.367879):
        self.model = model
        self.k1 = k1
        self.k2 = k2
        self.lam = lam
        self.rho_eq = rho_eq
        self.tokens_processed = 0
        self.global_phase = 0.0
        self.global_damping = 1.0
        
        # Registrar hook no backward
        self._register_hooks()
    
    def _register_hooks(self):
        """Insere hooks nos gradientes para capturar as normas."""
        for param in self.model.parameters():
            if param.requires_grad:
                param.register_post_accumulate_grad_hook(self._sync_hook)
    
    def _sync_hook(self, param):
        """Hook chamado após gradientes serem acumulados."""
        if param.grad is None:
            return
        
        # 1. Calcular norma local quadrada (para redução)
        local_sq_norm = param.grad.data.pow(2).sum()
        
        # 2. Sincronizar com todas as GPUs
        if dist.is_initialized():
            dist.all_reduce(local_sq_norm, op=dist.ReduceOp.SUM)
        
        # 3. Norma global (raiz quadrada)
        global_norm = torch.sqrt(local_sq_norm)
        
        # 4. Calcular métricas globais (usando o primeiro parâmetro como representante)
        # Aqui poderíamos acumular em um buffer e só chamar o kernel CUDA a cada N passos
        self.tokens_processed += 1
        
        # Chamada ao kernel CUDA com a norma global (não precisa de gradientes individuais)
        # Nota: adaptamos a função CUDA para receber a norma diretamente.
        dummy_loss = torch.tensor([1.0], device=param.device)
        # arkhe_loss, phase, damping = arkhe_cuda.compute_with_norm(
        #     dummy_loss, global_norm.unsqueeze(0), self.tokens_processed,
        #     self.k1, self.k2, self.lam, self.rho_eq
        # )
        # self.global_phase = phase.item()
        # self.global_damping = damping.item()
        
        # Mock
        self.global_phase = 1.57
        self.global_damping = 0.95
    
    def get_global_metrics(self):
        return {"phase": self.global_phase, "damping": self.global_damping}
