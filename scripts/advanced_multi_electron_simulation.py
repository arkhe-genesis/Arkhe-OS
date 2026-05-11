import numpy as np
import time
from collections import deque
import matplotlib.pyplot as plt

# ------------------------------------------------------------------------
# Rede LoRa simulada com calibração adaptativa
# ------------------------------------------------------------------------
class AdaptiveLoRaNetwork:
    def __init__(self, num_nodes, base_loss=0.1, max_delay=2.0):
        self.loss_rate = base_loss
        self.max_delay = max_delay
        self.pending = []  # (payload, src, dst, arrival_time)
        # Parâmetros adaptativos por nó
        self.sf = [9] * num_nodes           # inicial SF9
        self.tx_interval = [30.0] * num_nodes  # segundos
        self.base_loss = base_loss

    def config_loss(self, sf):
        """Perda aumenta com SF maior (mais tempo no ar -> maior chance de colisão)."""
        return self.base_loss * (sf / 7.0)

    def tx_time(self, sf, payload_bytes=24):
        """Estima tempo no ar (ms) para 24 bytes de payload."""
        # Fórmula simplificada: tempo ~ 2^SF / (BW * 4/5) * símbolos
        bw = 250000  # Hz
        cr = 1.25    # 4/5 coding rate
        symbols = payload_bytes * 8 * cr
        return symbols * (2**sf) / bw

    def send(self, payload, src_id, dst_id=None, broadcast=False, sf=None):
        if sf is None:
            sf = self.sf[src_id]
        p_loss = self.config_loss(sf)
        if np.random.random() < p_loss:
            return False
        delay = np.random.uniform(0.05, self.max_delay)  # latência básica de processamento + propagação
        arrival = time.time() + delay
        self.pending.append((payload, src_id, dst_id, broadcast, arrival))
        return True

    def receive_all(self, node_id):
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

    def update_parameters(self, node_id, coherence_gradient, loss_measured):
        """Ajusta SF e TX interval com base no gradiente de coerência e perda."""
        tau = 0.2  # limiar de gradiente
        # Ajuste de SF
        if coherence_gradient < -tau and self.sf[node_id] > 7:
            self.sf[node_id] -= 1  # reduz SF para acelerar troca
        elif coherence_gradient > tau and self.sf[node_id] < 11:
            self.sf[node_id] += 1  # aumenta SF para economizar energia

        # Ajuste de intervalo de transmissão
        if loss_measured > 0.2 and self.tx_interval[node_id] > 10:
            self.tx_interval[node_id] -= 10  # transmite mais frequentemente
        elif loss_measured < 0.05 and self.tx_interval[node_id] < 60:
            self.tx_interval[node_id] += 5


# ------------------------------------------------------------------------
# Agente Wakefield com gradiente de coerência
# ------------------------------------------------------------------------
class AdaptiveWakefieldAgent:
    def __init__(self, node_id, alpha=0.001):
        self.id = node_id
        self.alpha = alpha
        self.kt_gap = 1.0
        self.hallucination = False
        self.phase_error = 0.05
        self.last_snapshot = None
        # Cache de gaps de vizinhos para gradiente
        self.neighbor_gaps = deque(maxlen=20)

    def update(self, query_len, context_len):
        """Atualiza o gap local (simula medição FREM)."""
        self.kt_gap = abs(query_len - context_len) / max(query_len, context_len, 1) * 10.0 + np.random.normal(0, 0.5)
        self.hallucination = self.kt_gap > 15.0
        self.phase_error = 0.9 * self.phase_error + 0.1 * np.random.uniform(0, 0.1)
        if self.hallucination:
            self.alpha *= 0.99
        else:
            self.alpha = min(0.01, self.alpha * 1.0001)

    def snapshot(self):
        return {
            'id': self.id,
            'kt_gap': self.kt_gap,
            'hallucination': self.hallucination,
            'alpha': self.alpha,
            'timestamp': time.time()
        }

    def ingest_snapshot(self, snap):
        """Recebe snapshot de vizinho e atualiza o cache de gaps."""
        self.neighbor_gaps.append(snap['kt_gap'])

    def coherence_gradient(self):
        """Calcula gradiente de coerência: gap_local - média dos vizinhos."""
        if len(self.neighbor_gaps) == 0:
            return 0.0
        avg_neighbor = np.mean(self.neighbor_gaps)
        return self.kt_gap - avg_neighbor


# ------------------------------------------------------------------------
# Elétron Virtual múltiplo
# ------------------------------------------------------------------------
class VirtualElectron:
    def __init__(self, eid, energy=0.5):
        self.id = eid
        self.energy = energy
        self.node = 0
        self.history = [(0, energy)]

    def accelerate(self, delta):
        self.energy += delta
        self.history.append((self.node, self.energy))

    def move_to(self, node):
        self.node = node

    def hallucination_level(self):
        """Define um nível de alucinação simulado para prioridade (na prática, seria o gap da query)."""
        return np.random.exponential(5)


# ------------------------------------------------------------------------
# Simulação Principal Multi-Elétron
# ------------------------------------------------------------------------
def run_multi_electron_sim(
    num_nodes=10, num_electrons=5, steps=500, kolmogorov_limit=100.0
):
    network = AdaptiveLoRaNetwork(num_nodes, base_loss=0.08)
    agents = [AdaptiveWakefieldAgent(i, alpha=0.001 + i*0.0001) for i in range(num_nodes)]
    electrons = [VirtualElectron(eid) for eid in range(num_electrons)]

    # Coloca cada elétron em um nó aleatório
    for el in electrons:
        el.move_to(np.random.randint(0, num_nodes))

    kolmogorov_reached = False
    step_energies = []       # energia média dos elétrons
    step_gaps = []          # gap médio dos nós
    sf_history = []         # SF médio
    tx_interval_history = []
    waiting_queries = [[] for _ in range(num_nodes)]  # fila de elétrons por nó

    for step in range(steps):
        # 1. Atualizar agentes e calcular gradiente
        for agent in agents:
            agent.update(50 + np.random.randint(0, 100), 30 + np.random.randint(0, 60))
            # Transmitir snapshot se o intervalo permitir (simplificado: sempre tenta)
            snap = agent.snapshot()
            network.send(snap, agent.id, broadcast=True, sf=network.sf[agent.id])

        # 2. Coletar mensagens e atualizar gradientes
        loss_counts = [0] * num_nodes
        for agent in agents:
            msgs = network.receive_all(agent.id)
            for snap, src_id in msgs:
                agent.ingest_snapshot(snap)
                # Contabilizar perda: se esperávamos mensagens de todos os vizinhos
                # Aqui simplificamos: medimos perda como fração de vizinhos que não enviaram
            # Estima perda para agent.id: número de vizinhos que não recebemos
            total_neighbors = num_nodes - 1
            received = len(msgs)
            loss = 1.0 - (received / total_neighbors) if total_neighbors > 0 else 0.0
            grad = agent.coherence_gradient()
            network.update_parameters(agent.id, grad, loss)
            loss_counts[agent.id] = loss

        # 3. Escalonamento de elétrons: cada nó atende o elétron com maior "alucinação" (gap estimado)
        for node_id in range(num_nodes):
            # Lista de elétrons atualmente neste nó
            local_els = [el for el in electrons if el.node == node_id]
            if not local_els:
                continue
            # Prioridade: maior energia de alucinação (simulada, poderia ser o gap da query associada)
            priorities = [el.hallucination_level() for el in local_els]
            chosen_idx = int(np.argmax(priorities))
            chosen_el = local_els[chosen_idx]

            # Aceleração oferecida pelo nó: depende da coerência do nó
            agent = agents[node_id]
            acc = max(0, 10.0 - agent.kt_gap) * 0.3  # GeV
            chosen_el.accelerate(acc)

        # 4. Mover elétrons para o próximo nó (round-robin, exceto aquele que já foi acelerado permanece? Melhor: salto após aceleração)
        for el in electrons:
            new_node = (el.node + 1) % num_nodes
            el.move_to(new_node)

        # 5. Coleta de métricas
        avg_energy = np.mean([el.energy for el in electrons])
        avg_gap = np.mean([a.kt_gap for a in agents])
        avg_sf = np.mean([network.sf[i] for i in range(num_nodes)])
        avg_interval = np.mean([network.tx_interval[i] for i in range(num_nodes)])

        step_energies.append(avg_energy)
        step_gaps.append(avg_gap)
        sf_history.append(avg_sf)
        tx_interval_history.append(avg_interval)

        if avg_energy >= kolmogorov_limit and not kolmogorov_reached:
            print(f"Limiar de Kolmogorov atingido no passo {step}! Energia média: {avg_energy:.2f} GeV")
            kolmogorov_reached = True

    # Plot
    # fig, axs = plt.subplots(4, 1, figsize=(12, 12), sharex=True)
    # axs[0].plot(step_energies, label='Energia Média dos Elétrons (GeV)')
    # axs[0].axhline(kolmogorov_limit, color='red', linestyle='--', label='Limiar Kolmogorov')
    # axs[0].set_ylabel('Energia (GeV)')
    # axs[0].legend()
    # axs[0].grid(True)

    # axs[1].plot(step_gaps, color='orange', label='Gap ΔK médio dos nós')
    # axs[1].set_ylabel('ΔK médio')
    # axs[1].legend()
    # axs[1].grid(True)

    # axs[2].plot(sf_history, color='green', label='Spreading Factor médio')
    # axs[2].set_ylabel('SF')
    # axs[2].set_ylim(6, 12)
    # axs[2].legend()
    # axs[2].grid(True)

    # axs[3].plot(tx_interval_history, color='purple', label='Intervalo TX médio (s)')
    # axs[3].set_ylabel('Intervalo (s)')
    # axs[3].set_xlabel('Passo')
    # axs[3].legend()
    # axs[3].grid(True)

    # plt.suptitle('Simulação Multi-Elétron com Prioridade por Gradiente de Coerência e Calibração LoRa')
    # plt.tight_layout()
    # plt.show()

    # Análise
    final_gap = step_gaps[-1]
    final_sf = sf_history[-1]
    print(f"Resultados finais - Energia média: {step_energies[-1]:.2f} GeV, ΔK médio: {final_gap:.3f}, SF final: {final_sf:.1f}, Intervalo TX: {tx_interval_history[-1]:.1f} s")
    print(f"Convergência ao limiar: {'Sim' if kolmogorov_reached else 'Não'}")

if __name__ == "__main__":
    run_multi_electron_sim(num_nodes=10, num_electrons=5, steps=600)
