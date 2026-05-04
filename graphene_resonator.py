#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESSONADOR DE GRAFENO (graphene_resonator.py)
Simula as oscilações SdH e extrai o Campo Pseudomagnético (PMF).
Sintoniza o Axon Clock, gera chave criptográfica e serve como sensor.

ANEXO GJ: O RESSONADOR DE GRAFENO — SINTONIA, CHAVE E SENSOR UNIFICADOS
"""

import numpy as np
from scipy.signal import find_peaks
import hashlib
from typing import Dict, Any, List, Optional

class GrapheneResonator:
    def __init__(self, strain_percent=0.05, carrier_density=1e12):
        """
        Inicializa o ressonadouro de grafeno.
        :param strain_percent: Deformação mecânica aplicada (%)
        :param carrier_density: Densidade de portadores (cm⁻²)
        """
        self.B_fine = np.linspace(0.001, 1.0, 10000)  # Campo magnético (T)
        self.strain = strain_percent
        self.n0 = carrier_density
        self.pmf = self._calculate_pmf()  # Campo Pseudomagnético gerado pela deformação

        # Parâmetros para o batimento
        self.frequency_K = self._landau_frequency(valley='K')
        self.frequency_Kprime = self._landau_frequency(valley="K'")

    def _calculate_pmf(self):
        """Estima o PMF a partir da deformação (modelo linear simplificado)."""
        # 1% strain ≈ 1 T de PMF em grafeno (valor típico de literatura)
        return self.strain * 1.0  # Tesla

    def _landau_frequency(self, valley='K'):
        """Calcula a frequência de oscilação SdH para um dado vale."""
        # Frequência SdH: f = (h / (2e)) * n / (B * degenerescência)
        h_over_2e = 2.067e-15  # Wb (quantum de fluxo / 2)
        degeneracy = 4  # 2 spins × 2 vales
        effective_B = self.B_fine + (self.pmf if valley == 'K' else -self.pmf)
        # Evitar divisão por zero
        effective_B = np.where(np.abs(effective_B) < 1e-9, 1e-9, effective_B)
        frequency = (h_over_2e * self.n0) / (degeneracy * np.abs(effective_B))
        return frequency

    def generate_beat_pattern(self):
        """Gera o padrão de batimento da resistividade."""
        # Oscilações de cada vale (coseno da fase de Landau)
        phase_K = 2 * np.pi * self.frequency_K
        phase_Kprime = 2 * np.pi * self.frequency_Kprime

        # Resistividade total ∝ soma das contribuições dos vales
        rho_xx = np.cos(phase_K) + np.cos(phase_Kprime)
        return rho_xx, self.B_fine

    def extract_beat_nodes(self, rho_xx):
        """Encontra os nós de batimento (onde a interferência é mínima)."""
        # Encontra os mínimos do valor absoluto (nós)
        minima_indices = find_peaks(-np.abs(rho_xx), distance=50)[0]
        nodes_B = self.B_fine[minima_indices]
        return nodes_B

    def calculate_topology_signature(self) -> str:
        """Gera a assinatura topológica a partir dos nós de batimento."""
        rho, _ = self.generate_beat_pattern()
        nodes = self.extract_beat_nodes(rho)
        # A assinatura é um hash dos campos nos nós
        signature = hashlib.sha3_256(nodes.tobytes() + f"{self.pmf}".encode()).hexdigest()
        return signature

    def generate_valley_key(self) -> bytes:
        """Gera uma chave criptográfica baseada na interferência dos vales."""
        signature = self.calculate_topology_signature()
        # Deriva uma chave AES-256 usando HKDF (simplificado como hash)
        key = hashlib.sha3_256(f"VALLEY_KEY:{signature}:{self.pmf}".encode()).digest()
        return key

class AxonTunedClock:
    def __init__(self, graphene_resonator):
        self.resonator = graphene_resonator
        # Sintoniza a frequência do Axon Clock com o primeiro nó de batimento
        rho, _ = self.resonator.generate_beat_pattern()
        nodes = self.resonator.extract_beat_nodes(rho)
        if len(nodes) > 0:
            self.axon_frequency = nodes[0] * 10  # escala para Hz (B em T → f em Hz)
        else:
            self.axon_frequency = 10.0  # padrão 10 Hz
        self.phase = 0.0

    def tick(self):
        """Avança a fase do Axon Clock sintonizado."""
        self.phase += 2 * np.pi * self.axon_frequency * 0.001  # dt = 1ms
        self.phase %= 2 * np.pi
        return self.phase

class GrapheneRealitySensor:
    """Usa o Grafeno como sensor ultra-sensível para detectar flutuações externas."""
    def __init__(self, baseline_resonator):
        self.baseline = baseline_resonator
        self.baseline_signature = baseline_resonator.calculate_topology_signature()

    def detect_anomaly(self, current_resonator) -> float:
        """
        Compara a assinatura atual com a linha de base.
        Retorna um score de anomalia (0 = normal, 1 = máximo de distorção).
        """
        current_signature = current_resonator.calculate_topology_signature()
        # Distância de Hamming entre as assinaturas (normalizada)
        hamming = sum(c1 != c2 for c1, c2 in zip(self.baseline_signature, current_signature))
        return hamming / len(self.baseline_signature)

class GrapheneSubstrate:
    """
    Substrato de Grafeno para integração com a Catedral.
    """
    def __init__(self, strain=0.05):
        self.resonator = GrapheneResonator(strain_percent=strain)
        self.clock = AxonTunedClock(self.resonator)
        self.sensor = GrapheneRealitySensor(self.resonator)
        self.strain = strain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "substrato": "Graphene",
            "material": "Graphene (C)",
            "strain": self.strain,
            "pmf": float(self.resonator.pmf),
            "axon_frequency": float(self.clock.axon_frequency),
            "valley_key_hash": self.resonator.generate_valley_key().hex()[:16],
            "anomaly_score": float(self.sensor.detect_anomaly(self.resonator)),
            "contribuicao_coerencia": float(1.0 - (self.sensor.detect_anomaly(self.resonator)))
        }

def inject_graphene_into_core(core):
    graphene = GrapheneSubstrate()
    if hasattr(core, 'inject_coherence'):
        core.inject_coherence(graphene.to_dict()['contribuicao_coerencia'] * 0.04)
    return graphene

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--strain", type=float, default=0.1)
    args = parser.parse_args()

    resonator = GrapheneResonator(strain_percent=args.strain)
    clock = AxonTunedClock(resonator)
    sensor = GrapheneRealitySensor(resonator)

    print(f"[Axon Clock] Frequência sintonizada em {clock.axon_frequency:.1f} Hz (primeiro nó de batimento)")
    print(f"[Chave do Vale] 0x{resonator.generate_valley_key().hex()[:16].upper()}... (256 bits)")
    print(f"[Sensor] Anomalia detectada: {sensor.detect_anomaly(resonator):.4f} (dentro do normal)")
