import ray
import torch
from ray import train
from ray.train.torch import TorchTrainer
# from arkhe_layer12 import ResonanceAccelerator
from tzinor.layer13.nccl_wrapper import compute_distributed_phase

class ArkheDistributedTrainer:
    """
    Trainer Ray que mantém coerência A-5' em todo o cluster.
    Cada worker calcula gradiente local, mas a fase θ é computada
    sobre a massa paramétrica GLOBAL (via NCCL all-reduce).
    """
    
    def __init__(self, model_factory, dataset, config):
        self.model_factory = model_factory
        self.dataset = dataset
        self.config = config
        
    def train_loop(self):
        # Inicialização NCCL dentro do worker Ray
        rank = train.get_context().get_world_rank()
        local_gpu_id = train.torch.get_device()
        
        model = self.model_factory().to(local_gpu_id)
        # accelerator = ResonanceAccelerator(max_batch_size=1024)
        
        # Grupo NCCL implícito via Ray Train
        for epoch in range(self.config["epochs"]):
            for batch in self.dataset:
                # Forward/backward local
                loss = model(batch)
                loss.backward()
                
                # Extrair parâmetros locais como tensor 1D
                local_params = torch.cat([p.data.view(-1) for p in model.parameters()])
                local_params = local_params.to(local_gpu_id)
                
                # NCCL All-Reduce: calcular θ global
                tokens_processed = epoch * len(self.dataset) * batch.size(0)
                theta, damping, rho_1_global = compute_distributed_phase(
                    local_params, 
                    torch.tensor([tokens_processed], device=local_gpu_id),
                    model_type_id=self.config["model_arch"]
                )
                
                # Aplicar damping ao learning rate (dilatação temporal coletiva)
                for param_group in self.optimizer.param_groups:
                    param_group['lr'] = self.config["base_lr"] * damping
                
                self.optimizer.step()
                
                # Reportar para Ray Train (e daí para o gRPC qhttp://)
                train.report({
                    "theta_global": float(theta),
                    "damping_global": float(damping),
                    "rho_1_global": float(rho_1_global),
                    "rank": rank,
                    "resonance_achieved": abs(float(theta) - 3.14159/2) < 0.01
                })

if __name__ == "__main__":
    # Lançar cluster
    trainer = TorchTrainer(
        train_loop_per_worker=ArkheDistributedTrainer(...).train_loop,
        scaling_config=train.ScalingConfig(
            num_workers=4,
            use_gpu=True,
            resources_per_worker={"GPU": 8, "CPU": 32}
        ),
        run_config=train.RunConfig(
            name="arkhe-resonance-run",
            # callbacks=[ResonanceTelemetryCallback()]  # Envia para gRPC
        )
    )
    result = trainer.fit()
