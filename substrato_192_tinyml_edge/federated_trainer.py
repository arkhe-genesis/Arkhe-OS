import numpy as np

class FederatedTinyTrainer:
    def __init__(self):
        self.global_weights = None
        self.node_updates = []

    def receive_update(self, node_id, quantized_gradients):
        """Recebe gradientes quantizados (8-bit) de um nó com privacidade diferencial."""
        # Simulando recepção de gradientes (com ruído de Laplace já adicionado no nó)
        self.node_updates.append((node_id, quantized_gradients))
        print(f"[{node_id}] Gradientes quantizados recebidos.")

    def aggregate(self):
        """Agregação global a cada hora via Phi-Bus."""
        if not self.node_updates:
            print("[Federated] Sem atualizações para agregar.")
            return

        print(f"[Federated] Agregando atualizações de {len(self.node_updates)} nós...")

        # Simulação de agregação
        # Na prática, isso faria a média dos gradientes e aplicaria aos pesos globais
        self.node_updates = []
        print("[Federated] Agregação concluída. Novo modelo global pronto para distribuição.")

def deploy_to_pilots():
    pilots = ["energia", "agua", "gas", "manufatura"]
    print("\n--- IMPLANTANDO NOS 4 PILOTOS SCADA ---")
    for pilot in pilots:
        print(f"-> Implantando modelo TFLite Micro no Gateway ESP32 do piloto: {pilot.upper()}")
        print(f"   [OK] {pilot.upper()} - Inferência local e federated training ativados.")

if __name__ == "__main__":
    trainer = FederatedTinyTrainer()

    # Simular updates
    trainer.receive_update("node_energia_01", np.array([1, 2, -1, 0]))
    trainer.receive_update("node_agua_05", np.array([0, 1, 1, -2]))

    trainer.aggregate()

    deploy_to_pilots()
