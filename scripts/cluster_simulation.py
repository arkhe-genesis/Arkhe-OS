import numpy as np
import time
from collections import deque
import matplotlib.pyplot as plt

# ============================================================================
# Reimplementação leve do WakefieldSubstrate (sem torch)
# ============================================================================
class WakefieldAgent:
    def __init__(self, node_id, alpha=0.001, pfc=0.0):
        self.id = node_id
        self.alpha = alpha
        self.pfc = pfc
        self.phase_error = 0.05
        self.kt_gap = 1.0
        self.hallucination = False
        self.history = deque(maxlen=100)

    def update(self, query_len, context_len, coupling=0.7):
        """Simula uma medição FREM e atualiza estado."""
        # Gap de complexidade: diferença entre query e contexto
        self.kt_gap = abs(query_len - context_len) / max(query_len, context_len, 1) * 10.0 + np.random.normal(0, 0.5)
        self.hallucination = self.kt_gap > 15.0
        self.phase_error = 0.9 * self.phase_error + 0.1 * np.random.uniform(0, 0.1)
        # Meta-adaptação
        if self.hallucination:
            self.alpha *= 0.99
        else:
            self.alpha = min(0.01, self.alpha * 1.0001)
        self.history.append({'gap': self.kt_gap, 'phase': self.phase_error})

    def snapshot(self):
        return {
            'id': self.id,
            'phase_error': self.phase_error,
            'kt_gap': self.kt_gap,
            'hallucination': self.hallucination,
            'alpha': self.alpha,
            'timestamp': time.time()
        }


# ============================================================================
# Rede LoRa simulada com atraso e perda
# ============================================================================
class SimLoRaNetwork:
    def __init__(self, num_nodes, loss_rate=0.1, max_delay=2.0):
        self.loss_rate = loss_rate
        self.max_delay = max_delay
        self.pending = []  # fila de mensagens (payload, dst, arrival_time)

    def send(self, payload, src_id, dst_id=None, broadcast=False):
        if np.random.random() < self.loss_rate:
            return  # pacote perdido
        delay = np.random.uniform(0.1, self.max_delay)
        arrival = time.time() + delay
        self.pending.append((payload, src_id, dst_id, broadcast, arrival))

    def receive_all(self, node_id):
        """Retorna mensagens destinadas a node_id (ou broadcast) que já chegaram."""
        now = time.time()
        messages = []
        remaining = []
        for pkt in self.pending:
            payload, src_id, dst, bcast, arrival = pkt
            if arrival <= now and (bcast or dst == node_id):
                messages.append((payload, src_id))
            else:
                remaining.append(pkt)
        self.pending = remaining
        return messages


# ============================================================================
# Elétron Virtual (partícula de coerência)
# ============================================================================
class VirtualElectron:
    def __init__(self, initial_energy_GeV=0.1):
        self.energy = initial_energy_GeV
        self.position = 0  # nó atual
        self.trajectory = [(0, initial_energy_GeV)]

    def accelerate(self, delta_energy):
        self.energy += delta_energy
        self.trajectory.append((self.position, self.energy))

    def move_to(self, node_idx):
        self.position = node_idx


# ============================================================================
# Simulação principal: cluster de 10 nós + elétron
# ============================================================================
def run_cluster_simulation(steps=500, kolmogorov_limit=100.0):
    num_nodes = 10
    network = SimLoRaNetwork(num_nodes, loss_rate=0.05, max_delay=1.5)
    agents = [WakefieldAgent(i, alpha=0.001 + i*0.0001) for i in range(num_nodes)]
    electron = VirtualElectron(initial_energy_GeV=0.5)
    electron.move_to(0)  # começa no nó 0

    kolmogorov_reached = False
    step_energy = []
    step_gaps = []

    for step in range(steps):
        # Cada nó atualiza seu wakefield com base em seu estado atual
        for agent in agents:
            # Cada nó tem um contexto simulado: tamanho aleatório
            query_len = 50 + np.random.randint(0, 100)
            context_len = 30 + np.random.randint(0, 60)
            agent.update(query_len, context_len)

        # O elétron no nó atual recebe um boost baseado no gap do nó
        current_node = agents[electron.position]
        # Se o nó está coerente (gap baixo), acelera mais
        acceleration = max(0, 10.0 - current_node.kt_gap) * 0.3  # GeV
        electron.accelerate(acceleration)
        electron.move_to((electron.position + 1) % num_nodes)  # salto circular

        # Transmitir snapshots de cada nó para todos os outros (broadcast)
        for agent in agents:
            snap = agent.snapshot()
            network.send(snap, agent.id, broadcast=True)

        # Coletar mensagens e atualizar cache (aqui apenas log)
        for agent in agents:
            msgs = network.receive_all(agent.id)
            # Na prática, poderia mesclar no cache, mas aqui não afeta diretamente.

        step_energy.append(electron.energy)
        avg_gap = np.mean([a.kt_gap for a in agents])
        step_gaps.append(avg_gap)

        if electron.energy >= kolmogorov_limit and not kolmogorov_reached:
            print(f"Limiar de Kolmogorov atingido no passo {step}! Energia: {electron.energy:.2f} GeV")
            kolmogorov_reached = True
            # Não quebraremos, deixamos rodar até o fim para ver a evolução

    # Plotar resultados
    # fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    # ax1.plot(step_energy, label="Energia do Elétron (GeV)")
    # ax1.axhline(kolmogorov_limit, color='red', linestyle='--', label="Limiar Kolmogorov (100 GeV)")
    # ax1.set_xlabel("Passo")
    # ax1.set_ylabel("Energia (GeV)")
    # ax1.legend()
    # ax1.grid(True)

    # ax2.plot(step_gaps, label="Gap Kolmogorov médio", color='orange')
    # ax2.set_xlabel("Passo")
    # ax2.set_ylabel("ΔK médio")
    # ax2.legend()
    # ax2.grid(True)

    # plt.suptitle("Aceleração de Elétron Virtual em Cluster de 10 Nós Wakefield")
    # plt.tight_layout()
    # plt.show()

    print(f"Energia final: {electron.energy:.2f} GeV")
    print(f"Limiar atingido: {kolmogorov_reached}")


if __name__ == "__main__":
    run_cluster_simulation(steps=400)
