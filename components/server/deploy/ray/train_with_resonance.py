import ray
import torch
from resonance_actor import ResonanceActor

@ray.remote(num_gpus=1)
def train_replica(model_params, data_shard):
    """Função de treinamento que usa o ResonanceActor."""
    actor = ResonanceActor.remote(model_params)
    # ... loop de treinamento
    for step, (batch) in enumerate(data_shard):
        # ... forward, backward
        loss = 0.5  # loss atual
        # obter tensor representativo (ex: pesos da última camada)
        param_tensor = torch.randn(1000) # list(model.parameters())[-1]
        metrics = ray.get(actor.compute.remote(loss, param_tensor))
        # usar metrics["phase"] para ajustar learning rate, etc.
        if metrics["phase"] > 1.5:  # próximo de π/2
            print(f"Ressonância detectada no passo {step}")
    return actor.aggregate_phase.remote()

if __name__ == "__main__":
    # Iniciar Ray
    ray.init(address="ray-head:10001")
    # Submeter tarefas
    data_shards = [[1,2,3], [4,5,6]]
    params = 1000
    futures = [train_replica.remote(params, shard) for shard in data_shards]
    phases = ray.get(futures)
