import numpy as np
from scipy.special import lambertw
from typing import List, Dict, Tuple

class NOMAManifold:
    """
    Manifold de alocação de potência NOMA para IoT 6G.
    Cada dispositivo é um ponto no manifold com coordenada (potência, canal).
    A métrica é definida pela razão sinal‑ruído‑interferência (SINR).
    """
    def __init__(self, num_devices=24, num_subchannels=12, Pmax=20, noise=0.1):
        self.K = num_devices
        self.N = num_subchannels
        self.Pmax = Pmax
        self.noise = noise
        # Canais Rayleigh sintéticos
        self.channels = np.random.rayleigh(scale=1.0, size=(self.K, self.N))

    def sinr(self, power_matrix: np.ndarray, device_idx: int, subch_idx: int) -> float:
        """SINR após SIC: remove potência dos dispositivos mais fortes."""
        sorted_idx = np.argsort(power_matrix[:, subch_idx])[::-1]
        pos = np.where(sorted_idx == device_idx)[0][0]
        interference = np.sum(power_matrix[sorted_idx[pos+1:], subch_idx]**2) if pos < len(sorted_idx)-1 else 0
        return (power_matrix[device_idx, subch_idx] * abs(self.channels[device_idx, subch_idx])**2) / (interference + self.noise)

    def fitness(self, power_matrix: np.ndarray) -> Tuple[float, float, float]:
        """
        Retorna (energia total, taxa média, violação de QoS).
        Queremos minimizar energia, maximizar taxa, e violação = 0.
        """
        total_power = np.sum(power_matrix)
        rates = []
        violations = 0
        for i in range(self.K):
            for n in range(self.N):
                if power_matrix[i,n] > 0:
                    sinr = self.sinr(power_matrix, i, n)
                    rate = np.log2(1 + sinr)
                    rates.append(rate)
                    if rate < 1.0:   # QoS threshold
                        violations += 1
        avg_rate = np.mean(rates) if rates else 0
        return total_power, avg_rate, violations

    def geometric_projection(self, power_matrix: np.ndarray) -> np.ndarray:
        """
        Projeção no núcleo do manifold de potência: força soluções para a região viável
        usando a métrica de torção (penalidade por violação de SIC).
        """
        # Implementa a condição de SIC: potência decrescente com canal
        for n in range(self.N):
            gains = abs(self.channels[:, n])**2
            order = np.argsort(gains)[::-1]
            for idx in range(1, len(order)):
                if power_matrix[order[idx], n] < power_matrix[order[idx-1], n]:
                    power_matrix[order[idx], n] = power_matrix[order[idx-1], n] * 0.5
        # Projeção no simplex de potência total
        total = np.sum(power_matrix)
        if total > self.Pmax:
            power_matrix *= self.Pmax / total
        return np.maximum(power_matrix, 0)

# MOGA wrapper já embutido no Unified Orchestrator – pode-se invocar diretamente.
