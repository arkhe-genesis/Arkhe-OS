import numpy as np
from numba import njit, prange
import time

@njit(parallel=True, cache=True)
def simulate_large_cluster(
    steps: int, num_nodes: int, num_electrons: int,
    spawn_rate: float, kolmogorov_limit: float
):
    """
    Simulação ultra-otimizada para 100+ nós.
    Todas as estruturas são arrays NumPy pré-alocados.
    """
    # Pré-alocação de arrays (contíguos em memória)
    kt_gap = np.zeros((num_nodes,), dtype=np.float32)
    coherence_grad = np.zeros((num_nodes,), dtype=np.float32)
    sf = np.full((num_nodes,), 9, dtype=np.int8)
    bw = np.full((num_nodes,), 250, dtype=np.int16)
    tx_power = np.full((num_nodes,), 14, dtype=np.int8)
    rssi = np.random.normal(-75, 10, (num_nodes,)).astype(np.float32)

    # Elétrons: arrays por atributo (estrutura de arrays, não array de estruturas)
    max_electrons = 200
    e_energy = np.zeros((max_electrons,), dtype=np.float32)
    e_position = np.zeros((max_electrons,), dtype=np.int32)
    e_kt_gap = np.zeros((max_electrons,), dtype=np.float32)
    e_active = np.zeros((max_electrons,), dtype=np.bool_)
    e_reached = np.zeros((max_electrons,), dtype=np.bool_)
    num_active = 0

    # Métricas agregadas
    total_energy_history = np.zeros((steps,), dtype=np.float32)
    avg_kt_history = np.zeros((steps,), dtype=np.float32)
    reached_count_history = np.zeros((steps,), dtype=np.int32)

    # Loop principal
    for step in range(steps):
        # 1. Spawn de novos elétrons
        if np.random.random() < spawn_rate and num_active < max_electrons - num_electrons:
            for _ in range(np.random.poisson(1)):
                if num_active >= max_electrons:
                    break
                idx = num_active
                e_energy[idx] = 0.5 + np.random.random() * 0.5
                e_position[idx] = np.random.randint(0, num_nodes)
                e_kt_gap[idx] = 1.0
                e_active[idx] = True
                e_reached[idx] = False
                num_active += 1

        # 2. Atualizar agentes (vetorizado)
        query_len = 50 + np.random.randint(0, 100, (num_nodes,)).astype(np.float32)
        context_len = 30 + np.random.randint(0, 60, (num_nodes,)).astype(np.float32)
        kt_gap[:] = np.abs(query_len - context_len) / np.maximum(query_len, context_len) * 10.0
        kt_gap += np.random.normal(0, 0.5, (num_nodes,)).astype(np.float32)
        kt_gap = np.clip(kt_gap, 0, 50)

        # Gradiente de coerência: diferença entre nó e média dos vizinhos (simplificado: ruído)
        coherence_grad[:] = np.abs(np.random.normal(0.3, 0.2, (num_nodes,)).astype(np.float32))

        # 3. Calibração LoRa adaptativa (vetorizada com Numba)
        sf[:] = np.clip(7 + (5 * kt_gap / 50).astype(np.int32), 7, 12)
        bw[:] = np.where(coherence_grad > 0.5, 500, np.where(coherence_grad > 0.2, 250, 125))
        # TX power simplificado
        tx_power[:] = np.clip(2 + ((20-2) * (1 / (1 + np.exp(-(0.8 * coherence_grad - 0.3 * (rssi+100)/100))))), 2, 20).astype(np.int8)

        # 4. Aceleração de elétrons (vetorizada)
        for i in prange(num_active):
            if not e_active[i] or e_reached[i]:
                continue
            node = e_position[i]
            # Aceleração: baseada na coerência do nó
            acc = max(0.0, 10.0 - kt_gap[node]) * 0.15
            e_energy[i] += acc
            if e_energy[i] >= kolmogorov_limit:
                e_reached[i] = True
                e_active[i] = False
            # Salto para próximo nó (probabilidade 30%)
            if np.random.random() < 0.3:
                e_position[i] = (e_position[i] + 1) % num_nodes

        # 5. Métricas
        active_mask = e_active[:num_active] & ~e_reached[:num_active]
        if np.any(active_mask):
            total_energy_history[step] = np.sum(e_energy[:num_active])
            avg_kt_history[step] = np.mean(e_kt_gap[:num_active])
            reached_count_history[step] = np.sum(e_reached[:num_active])

    return total_energy_history, avg_kt_history, reached_count_history, sf.copy(), bw.copy()

# Execução
if __name__ == "__main__":
    start = time.time()
    te, ak, rc, sf, bw = simulate_large_cluster(
        steps=500, num_nodes=128, num_electrons=32,
        spawn_rate=0.05, kolmogorov_limit=100.0
    )
    elapsed = time.time() - start
    print(f"Simulação 128 nós concluída em {elapsed:.2f}s")
    print(f"Elétrons que atingiram limiar: {rc[-1]}")
