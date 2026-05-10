#!/usr/bin/env python3
"""
monte_carlo_noma_6g.py — Simulação Monte Carlo completa para NOMA 6G-IoT.
Reproduz as Figuras 2, 3, 4 e 5 do artigo de Saraswat et al. (2023)
utilizando o NOMAManifold de torção do Substrato 168.

Uso:
  python monte_carlo_noma_6g.py --all
  python monte_carlo_noma_6g.py --fig2
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable
from scipy.stats import rayleigh
from scipy.special import lambertw
import time
import argparse
import os

# ============================================================================
# NOMAManifold — Implementação canônica do Substrato 168
# ============================================================================

@dataclass
class SimulationConfig:
    """Configuração da simulação Monte Carlo."""
    total_iot_devices: int = 25
    sub_channels: int = 12
    max_power_sink: float = 20.0  # W
    min_qos_threshold: float = 1.0  # b/s/Hz
    circuit_power: float = 0.5  # W
    power_gap_sic: float = 0.2  # W
    noise_variance: float = 0.1  # W
    max_devices_per_sc: int = 3
    monte_carlo_runs: int = 5000

class NOMAManifold:
    """
    Manifold de alocação de potência NOMA para IoT 6G.
    A métrica de torção define a curvatura do espaço de busca.
    """
    def __init__(self, config: SimulationConfig):
        self.K = config.total_iot_devices
        self.N = config.sub_channels
        self.Pmax = config.max_power_sink
        self.Pc = config.circuit_power
        self.noise = config.noise_variance
        self.beta = config.power_gap_sic
        self.gamma_min = config.min_qos_threshold
        self.Bmax = config.max_devices_per_sc

    def generate_channels(self) -> np.ndarray:
        """Gera canais Rayleigh i.i.d. para todos os dispositivos."""
        return np.random.rayleigh(scale=1.0, size=(self.K, self.N))

    def sinr(self, power_matrix: np.ndarray, channels: np.ndarray,
             device_idx: int, subch_idx: int) -> float:
        """SINR após SIC ordenado por ganho de canal."""
        col_powers = power_matrix[:, subch_idx]
        col_gains = np.abs(channels[:, subch_idx])**2
        order = np.argsort(col_gains)[::-1]
        pos = np.where(order == device_idx)[0][0]
        # Interferência: soma das potências dos dispositivos com ganho menor
        if pos < len(order) - 1:
            interference = np.sum(col_powers[order[pos+1:]] * col_gains[order[pos+1:]])
        else:
            interference = 0.0
        signal = col_powers[device_idx] * col_gains[device_idx]
        return signal / (interference + self.noise)

    def fitness(self, power_matrix: np.ndarray, channels: np.ndarray) -> Tuple[float, float, float]:
        """(potência total, taxa média, violações de QoS)."""
        total_power = np.sum(power_matrix)
        rates = []
        violations = 0
        for i in range(self.K):
            for n in range(self.N):
                if power_matrix[i, n] > 1e-9:
                    s = self.sinr(power_matrix, channels, i, n)
                    rate = np.log2(1 + s)
                    rates.append(rate)
                    if rate < self.gamma_min:
                        violations += 1
        avg_rate = np.mean(rates) if rates else 0.0
        return total_power, avg_rate, violations

    def geometric_projection(self, power_matrix: np.ndarray, channels: np.ndarray) -> np.ndarray:
        """Projeção no núcleo do manifold: força SIC e limite de potência."""
        proj = power_matrix.copy()
        for n in range(self.N):
            gains = np.abs(channels[:, n])**2
            order = np.argsort(gains)[::-1]
            # Garante ordem decrescente de potência (SIC viável)
            for idx in range(1, min(len(order), self.Bmax)):
                if proj[order[idx], n] > proj[order[idx-1], n] - self.beta / gains[order[idx-1]]:
                    proj[order[idx], n] = max(0, proj[order[idx-1], n] - self.beta / gains[order[idx-1]])
            # Zera potência para dispositivos além do máximo por sub-canal
            if len(order) > self.Bmax:
                proj[order[self.Bmax:], n] = 0.0
        # Projeção no simplex de potência total
        total = np.sum(proj)
        if total > self.Pmax:
            proj *= self.Pmax / total
        return np.maximum(proj, 0.0)

# ============================================================================
# MOGA — Multi-Objective Genetic Algorithm (integrado)
# ============================================================================

class MOGAOptimizer:
    """Otimizador multiobjetivo genético para NOMA power allocation."""
    def __init__(self, manifold: NOMAManifold, pop_size: int = 50, generations: int = 150,
                 crossover_rate: float = 0.9, mutation_rate: float = 0.1):
        self.manifold = manifold
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.history = []  # (gen, best_fitness)

    def _initialize_population(self) -> np.ndarray:
        """Inicializa população com distribuição uniforme [0, Pmax/K]."""
        init_power = self.manifold.Pmax / (self.manifold.K * 2)
        return np.random.uniform(0, init_power, (self.pop_size, self.manifold.K, self.manifold.N))

    def _non_dominated_sort(self, fitness_scores: List[Tuple]) -> List[List[int]]:
        """Ordenação não-dominada (Pareto fronts)."""
        n = len(fitness_scores)
        dominated_by = [[] for _ in range(n)]
        dominates_count = [0] * n
        fronts = [[]]
        for i in range(n):
            for j in range(i+1, n):
                # i domina j? (menor potência, maior taxa, menos violações)
                fi, fj = fitness_scores[i], fitness_scores[j]
                i_dominates_j = (fi[0] <= fj[0] and fi[1] >= fj[1] and fi[2] <= fj[2]) and \
                                 (fi[0] < fj[0] or fi[1] > fj[1] or fi[2] < fj[2])
                j_dominates_i = (fj[0] <= fi[0] and fj[1] >= fi[1] and fj[2] <= fi[2]) and \
                                 (fj[0] < fi[0] or fj[1] > fi[1] or fj[2] < fi[2])
                if i_dominates_j:
                    dominated_by[i].append(j)
                    dominates_count[j] += 1
                elif j_dominates_i:
                    dominated_by[j].append(i)
                    dominates_count[i] += 1
            if dominates_count[i] == 0:
                fronts[0].append(i)
        # Constrói demais fronts
        idx = 0
        while fronts[idx]:
            next_front = []
            for i in fronts[idx]:
                for j in dominated_by[i]:
                    dominates_count[j] -= 1
                    if dominates_count[j] == 0:
                        next_front.append(j)
            idx += 1
            if next_front:
                fronts.append(next_front)
            else:
                break
        return fronts

    def optimize(self, channels: np.ndarray) -> Tuple[np.ndarray, Tuple[float, float, float]]:
        """Executa MOGA e retorna a melhor solução encontrada."""
        pop = self._initialize_population()
        best_solution = None
        best_fitness = (float('inf'), 0.0, float('inf'))

        for gen in range(self.generations):
            # Avalia fitness com projeção geométrica
            for i in range(self.pop_size):
                pop[i] = self.manifold.geometric_projection(pop[i], channels)
            fitness_scores = [self.manifold.fitness(p, channels) for p in pop]

            # Atualiza melhor solução (minimizar violações primeiro)
            for i, fs in enumerate(fitness_scores):
                if fs[2] < best_fitness[2] or (fs[2] == best_fitness[2] and fs[0] < best_fitness[0]):
                    best_fitness = fs
                    best_solution = pop[i].copy()

            # Seleção por ranking não-dominado
            fronts = self._non_dominated_sort(fitness_scores)
            # Constrói nova população: preenche front por front
            new_pop = np.zeros_like(pop)
            filled = 0
            for front in fronts:
                if filled + len(front) <= self.pop_size:
                    new_pop[filled:filled+len(front)] = pop[front]
                    filled += len(front)
                else:
                    # Preenche o restante com repetições do melhor
                    n_remain = self.pop_size - filled
                    new_pop[filled:] = pop[front[:n_remain]]
                    break

            # Crossover (BLX-alpha)
            if self.crossover_rate > 0:
                for i in range(0, self.pop_size-1, 2):
                    if np.random.random() < self.crossover_rate:
                        alpha = 0.5
                        parent1, parent2 = new_pop[i], new_pop[i+1]
                        low = np.minimum(parent1, parent2) - alpha * np.abs(parent1 - parent2)
                        high = np.maximum(parent1, parent2) + alpha * np.abs(parent1 - parent2)
                        child1 = low + np.random.random(parent1.shape) * (high - low)
                        child2 = low + np.random.random(parent1.shape) * (high - low)
                        new_pop[i], new_pop[i+1] = child1, child2

            # Mutação (Gaussiana)
            if self.mutation_rate > 0:
                for i in range(self.pop_size):
                    if np.random.random() < self.mutation_rate:
                        noise = np.random.randn(*new_pop[i].shape) * 0.1 * (1 - gen/self.generations)
                        new_pop[i] += noise

            # Projeção pós-mutação
            for i in range(self.pop_size):
                new_pop[i] = self.manifold.geometric_projection(new_pop[i], channels)

            pop = new_pop
            self.history.append((gen, best_fitness))

        return best_solution, best_fitness

# ============================================================================
# Alocadores de Baseline (para comparação com Fig. 2-5)
# ============================================================================

def ofdma_allocation(manifold: NOMAManifold, channels: np.ndarray) -> np.ndarray:
    """OFDMA: cada sub-canal alocado a um único dispositivo (melhor canal)."""
    power = np.zeros((manifold.K, manifold.N))
    allocated_devices = []
    for n in range(manifold.N):
        gains = np.abs(channels[:, n])**2
        # Seleciona o melhor dispositivo ainda não alocado (round-robin)
        available = [k for k in range(manifold.K) if k not in allocated_devices]
        if available:
            best_k = max(available, key=lambda k: gains[k])
            allocated_devices.append(best_k)
            power[best_k, n] = manifold.Pmax / manifold.N  # divisão igual entre SCs
    return power

def benchmark_noma_allocation(manifold: NOMAManifold, channels: np.ndarray) -> np.ndarray:
    """NOMA de referência: power allocation uniforme com SIC."""
    power = np.zeros((manifold.K, manifold.N))
    for n in range(manifold.N):
        gains = np.abs(channels[:, n])**2
        order = np.argsort(gains)[::-1]
        # Atribui potência decrescente uniforme
        base_power = manifold.Pmax / (manifold.N * manifold.Bmax)
        for idx in range(min(len(order), manifold.Bmax)):
            power[order[idx], n] = base_power * (manifold.Bmax - idx)
    return power

def sqp_noma_allocation(manifold: NOMAManifold, channels: np.ndarray) -> np.ndarray:
    """SQP-NOMA: alocação baseada em water-filling modificado."""
    power = np.zeros((manifold.K, manifold.N))
    for n in range(manifold.N):
        gains = np.abs(channels[:, n])**2
        order = np.argsort(gains)[::-1]
        # Water-filling simplificado com threshold de QoS
        water_level = manifold.Pmax / (manifold.N * manifold.Bmax * 2)
        for idx in range(min(len(order), manifold.Bmax)):
            gain = gains[order[idx]]
            # Potência ∝ 1/gain (inversa para equalizar SINR)
            power[order[idx], n] = min(water_level * 3, manifold.Pmax * 0.1 / (gain + 0.01))
    return power

# ============================================================================
# Funções de simulação Monte Carlo
# ============================================================================

def monte_carlo_energy_vs_devices(config: SimulationConfig, max_K: int = 25):
    """Simula eficiência energética vs número de dispositivos (Fig. 2)."""
    K_values = list(range(1, max_K + 1))
    results = {'OFDMA': [], 'Benchmark_NOMA': [], 'SQP_NOMA': [], 'MOGA_NOMA': []}

    for K in K_values:
        config.total_iot_devices = K
        manifold = NOMAManifold(config)
        moga = MOGAOptimizer(manifold, pop_size=30, generations=80)

        ef_ofdma, ef_bnoma, ef_sqp, ef_moga = [], [], [], []
        for _ in range(config.monte_carlo_runs):
            channels = manifold.generate_channels()

            # OFDMA
            p_ofdma = ofdma_allocation(manifold, channels)
            total_p, avg_r, _ = manifold.fitness(p_ofdma, channels)
            ef_ofdma.append(avg_r / (total_p + config.circuit_power) * 1000 if total_p > 0 else 0)

            # Benchmark NOMA
            p_bnoma = benchmark_noma_allocation(manifold, channels)
            total_p, avg_r, _ = manifold.fitness(p_bnoma, channels)
            ef_bnoma.append(avg_r / (total_p + config.circuit_power) * 1000 if total_p > 0 else 0)

            # SQP NOMA
            p_sqp = sqp_noma_allocation(manifold, channels)
            total_p, avg_r, _ = manifold.fitness(p_sqp, channels)
            ef_sqp.append(avg_r / (total_p + config.circuit_power) * 1000 if total_p > 0 else 0)

            # MOGA NOMA (usa channels reais, otimiza para aquele instante)
            p_moga, _ = moga.optimize(channels)
            total_p, avg_r, _ = manifold.fitness(p_moga, channels)
            ef_moga.append(avg_r / (total_p + config.circuit_power) * 1000 if total_p > 0 else 0)

        results['OFDMA'].append(np.mean(ef_ofdma))
        results['Benchmark_NOMA'].append(np.mean(ef_bnoma))
        results['SQP_NOMA'].append(np.mean(ef_sqp))
        results['MOGA_NOMA'].append(np.mean(ef_moga))

        print(f"  K={K:2d} | OFDMA={results['OFDMA'][-1]:6.1f} | BNOMA={results['Benchmark_NOMA'][-1]:6.1f} | SQP={results['SQP_NOMA'][-1]:6.1f} | MOGA={results['MOGA_NOMA'][-1]:6.1f}")

    return K_values, results

def monte_carlo_energy_vs_power(config: SimulationConfig):
    """Simula eficiência energética vs potência restante no sink (Fig. 3)."""
    P_values = np.arange(10, 21, 1)
    results = {'OFDMA': [], 'Benchmark_NOMA': [], 'SQP_NOMA': [], 'MOGA_NOMA': []}

    for Pmax in P_values:
        config.max_power_sink = Pmax
        manifold = NOMAManifold(config)
        moga = MOGAOptimizer(manifold, pop_size=30, generations=80)

        ef_ofdma, ef_bnoma, ef_sqp, ef_moga = [], [], [], []
        for _ in range(config.monte_carlo_runs):
            channels = manifold.generate_channels()

            p_ofdma = ofdma_allocation(manifold, channels)
            _, avg_r, _ = manifold.fitness(p_ofdma, channels)
            ef_ofdma.append(avg_r / (np.sum(p_ofdma) + config.circuit_power) * 1000 if np.sum(p_ofdma) > 0 else 0)

            p_bnoma = benchmark_noma_allocation(manifold, channels)
            _, avg_r, _ = manifold.fitness(p_bnoma, channels)
            ef_bnoma.append(avg_r / (np.sum(p_bnoma) + config.circuit_power) * 1000 if np.sum(p_bnoma) > 0 else 0)

            p_sqp = sqp_noma_allocation(manifold, channels)
            _, avg_r, _ = manifold.fitness(p_sqp, channels)
            ef_sqp.append(avg_r / (np.sum(p_sqp) + config.circuit_power) * 1000 if np.sum(p_sqp) > 0 else 0)

            p_moga, _ = moga.optimize(channels)
            _, avg_r, _ = manifold.fitness(p_moga, channels)
            ef_moga.append(avg_r / (np.sum(p_moga) + config.circuit_power) * 1000 if np.sum(p_moga) > 0 else 0)

        results['OFDMA'].append(np.mean(ef_ofdma))
        results['Benchmark_NOMA'].append(np.mean(ef_bnoma))
        results['SQP_NOMA'].append(np.mean(ef_sqp))
        results['MOGA_NOMA'].append(np.mean(ef_moga))

    return P_values, results

def monte_carlo_spectral_vs_power(config: SimulationConfig):
    """Simula eficiência espectral vs potência de transmissão (Fig. 4)."""
    P_values = np.arange(6, 21, 2)
    results = {'OFDMA': [], 'Benchmark_NOMA': [], 'SQP_NOMA': [], 'MOGA_NOMA': []}

    for Pmax in P_values:
        config.max_power_sink = Pmax
        manifold = NOMAManifold(config)
        moga = MOGAOptimizer(manifold, pop_size=30, generations=80)

        se_ofdma, se_bnoma, se_sqp, se_moga = [], [], [], []
        for _ in range(config.monte_carlo_runs):
            channels = manifold.generate_channels()

            for alloc_fn, se_list in [(ofdma_allocation, se_ofdma), (benchmark_noma_allocation, se_bnoma),
                                      (sqp_noma_allocation, se_sqp)]:
                p = alloc_fn(manifold, channels)
                _, avg_r, _ = manifold.fitness(p, channels)
                se_list.append(avg_r)

            p_moga, _ = moga.optimize(channels)
            _, avg_r, _ = manifold.fitness(p_moga, channels)
            se_moga.append(avg_r)

        results['OFDMA'].append(np.mean(se_ofdma))
        results['Benchmark_NOMA'].append(np.mean(se_bnoma))
        results['SQP_NOMA'].append(np.mean(se_sqp))
        results['MOGA_NOMA'].append(np.mean(se_moga))

    return P_values, results

def monte_carlo_energy_vs_subchannels(config: SimulationConfig):
    """Simula eficiência energética vs número de sub-canais (Fig. 5)."""
    N_values = np.arange(1, 11, 1)
    results_Bmax2 = {'MOGA_NOMA': []}
    results_Bmax3 = {'MOGA_NOMA': []}

    for N in N_values:
        config.sub_channels = N
        manifold = NOMAManifold(config)
        moga = MOGAOptimizer(manifold, pop_size=30, generations=80)

        ef_moga2, ef_moga3 = [], []
        for _ in range(config.monte_carlo_runs):
            channels = manifold.generate_channels()

            # Bmax = 2
            manifold.Bmax = 2
            p_moga, _ = moga.optimize(channels)
            _, avg_r, _ = manifold.fitness(p_moga, channels)
            ef_moga2.append(avg_r / (np.sum(p_moga) + config.circuit_power) * 1000 if np.sum(p_moga) > 0 else 0)

            # Bmax = 3
            manifold.Bmax = 3
            p_moga, _ = moga.optimize(channels)
            _, avg_r, _ = manifold.fitness(p_moga, channels)
            ef_moga3.append(avg_r / (np.sum(p_moga) + config.circuit_power) * 1000 if np.sum(p_moga) > 0 else 0)

        results_Bmax2['MOGA_NOMA'].append(np.mean(ef_moga2))
        results_Bmax3['MOGA_NOMA'].append(np.mean(ef_moga3))

    config.sub_channels = 12  # restore
    return N_values, results_Bmax2, results_Bmax3

# ============================================================================
# Plotagem
# ============================================================================

def plot_all_figures(config: SimulationConfig):
    """Gera e salva as 4 figuras do artigo."""
    os.makedirs("figures", exist_ok=True)

    print("📊 Gerando Figura 2: Eficiência Energética vs Nº Dispositivos IoT")
    K_vals, fig2_data = monte_carlo_energy_vs_devices(config, max_K=25)

    print("📊 Gerando Figura 3: Eficiência Energética vs Potência Restante")
    P_vals, fig3_data = monte_carlo_energy_vs_power(config)

    print("📊 Gerando Figura 4: Eficiência Espectral vs Potência de Transmissão")
    Psp_vals, fig4_data = monte_carlo_spectral_vs_power(config)

    print("📊 Gerando Figura 5: Eficiência Energética vs Nº Sub‑canais")
    N_vals, fig5_b2, fig5_b3 = monte_carlo_energy_vs_subchannels(config)

    # --- Figura 2 ---
    plt.figure(figsize=(8,5))
    for label, color, marker in [('OFDMA','blue','o'), ('Benchmark_NOMA','orange','s'),
                                   ('SQP_NOMA','green','^'), ('MOGA_NOMA','red','D')]:
        plt.plot(K_vals, fig2_data[label], f'-{marker}', color=color, label=label, markersize=5)
    plt.xlabel('Nº de Dispositivos IoT')
    plt.ylabel('Eficiência Energética (nJ/bit/Hz)')
    plt.title('Fig 2: Eficiência Energética vs Nº Dispositivos')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("figures/fig2_energy_vs_devices.png", dpi=150)
    plt.close()

    # --- Figura 3 ---
    plt.figure(figsize=(8,5))
    for label, color, marker in [('OFDMA','blue','o'), ('Benchmark_NOMA','orange','s'),
                                   ('SQP_NOMA','green','^'), ('MOGA_NOMA','red','D')]:
        plt.plot(P_vals, fig3_data[label], f'-{marker}', color=color, label=label, markersize=5)
    plt.xlabel('Potência Restante no Sink (W)')
    plt.ylabel('Eficiência Energética (nJ/bit/Hz)')
    plt.title('Fig 3: Eficiência Energética vs Potência Restante')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("figures/fig3_energy_vs_power.png", dpi=150)
    plt.close()

    # --- Figura 4 ---
    plt.figure(figsize=(8,5))
    for label, color, marker in [('OFDMA','blue','o'), ('Benchmark_NOMA','orange','s'),
                                   ('SQP_NOMA','green','^'), ('MOGA_NOMA','red','D')]:
        plt.plot(Psp_vals, fig4_data[label], f'-{marker}', color=color, label=label, markersize=5)
    plt.xlabel('Potência de Transmissão no Sink (W)')
    plt.ylabel('Eficiência Espectral (b/s/Hz)')
    plt.title('Fig 4: Eficiência Espectral vs Potência de Transmissão')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("figures/fig4_spectral_vs_power.png", dpi=150)
    plt.close()

    # --- Figura 5 ---
    plt.figure(figsize=(8,5))
    plt.plot(N_vals, fig5_b2['MOGA_NOMA'], 'D-', color='blue', label='MOGA-NOMA (Bmax=2)')
    plt.plot(N_vals, fig5_b3['MOGA_NOMA'], 'o-', color='red', label='MOGA-NOMA (Bmax=3)')
    plt.xlabel('Número de Sub-canais')
    plt.ylabel('Eficiência Energética (nJ/bit/Hz)')
    plt.title('Fig 5: Eficiência Energética vs Número de Sub-canais')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("figures/fig5_energy_vs_subchannels.png", dpi=150)
    plt.close()

    print("\n✅ Todas as figuras salvas no diretório 'figures/'.")

# ============================================================================
# CLI
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Simulação Monte Carlo NOMA 6G-IoT")
    parser.add_argument("--fig2", action="store_true", help="Gerar apenas Figura 2")
    parser.add_argument("--fig3", action="store_true", help="Gerar apenas Figura 3")
    parser.add_argument("--fig4", action="store_true", help="Gerar apenas Figura 4")
    parser.add_argument("--fig5", action="store_true", help="Gerar apenas Figura 5")
    parser.add_argument("--all", action="store_true", help="Gerar todas as figuras")
    parser.add_argument("--runs", type=int, default=500, help="Número de iterações Monte Carlo")
    args = parser.parse_args()

    config = SimulationConfig(monte_carlo_runs=args.runs)

    if args.all or args.fig2:
        plot_all_figures(config)
        return

    if args.fig2:
        print("📊 Figura 2: Eficiência Energética vs Nº Dispositivos IoT")
        K_vals, fig2_data = monte_carlo_energy_vs_devices(config, max_K=25)
        # plot rápido
        for label in fig2_data:
            plt.plot(K_vals, fig2_data[label], '-o', label=label, markersize=4)
        plt.xlabel('Nº Dispositivos IoT'); plt.ylabel('Eficiência Energética (nJ)')
        plt.legend(); plt.grid(True, alpha=0.3)
        plt.title('Fig 2'); plt.tight_layout(); plt.show()
    elif args.fig3:
        print("📊 Figura 3: Eficiência Energética vs Potência Restante")
        P_vals, fig3_data = monte_carlo_energy_vs_power(config)
        for label in fig3_data:
            plt.plot(P_vals, fig3_data[label], '-o', label=label, markersize=4)
        plt.xlabel('Potência Restante (W)'); plt.ylabel('Eficiência Energética (nJ)')
        plt.legend(); plt.grid(True, alpha=0.3)
        plt.title('Fig 3'); plt.tight_layout(); plt.show()
    elif args.fig4:
        print("📊 Figura 4: Eficiência Espectral vs Potência de Transmissão")
        Psp_vals, fig4_data = monte_carlo_spectral_vs_power(config)
        for label in fig4_data:
            plt.plot(Psp_vals, fig4_data[label], '-o', label=label, markersize=4)
        plt.xlabel('Potência de Transmissão (W)'); plt.ylabel('Eficiência Espectral (b/s/Hz)')
        plt.legend(); plt.grid(True, alpha=0.3)
        plt.title('Fig 4'); plt.tight_layout(); plt.show()
    elif args.fig5:
        print("📊 Figura 5: Eficiência Energética vs Número de Sub-canais")
        N_vals, fig5_b2, fig5_b3 = monte_carlo_energy_vs_subchannels(config)
        plt.plot(N_vals, fig5_b2['MOGA_NOMA'], 'D-', label='Bmax=2')
        plt.plot(N_vals, fig5_b3['MOGA_NOMA'], 'o-', label='Bmax=3')
        plt.xlabel('Número de Sub-canais'); plt.ylabel('Eficiência Energética (nJ)')
        plt.legend(); plt.grid(True, alpha=0.3)
        plt.title('Fig 5'); plt.tight_layout(); plt.show()
    else:
        plot_all_figures(config)

if __name__ == "__main__":
    main()
