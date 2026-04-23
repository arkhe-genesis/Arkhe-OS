#!/usr/bin/env python3
"""
MONITOR DE DISSIPAÇÃO ENTÓPICA (entropy_monitor.py)
Quantifica o calor informacional gerado pelo Gateway e acopla ao Diamante.
"""

import time, math, threading
from collections import Counter

class EntropyMonitor:
    def __init__(self, diamond_dissipation=None):
        self.diamond = diamond_dissipation  # DiamondDissipation instance (mocked if None)
        self.translation_counter = Counter()
        self.entropy_history = []
        self.total_heat_joules = 0.0
        self.running = False

    def record_translation(self, action_type: str):
        """Registra uma tradução e atualiza a contagem."""
        self.translation_counter[action_type] += 1

    def compute_shannon_entropy(self) -> float:
        """Calcula a entropia de Shannon das traduções recentes."""
        total = sum(self.translation_counter.values())
        if total == 0:
            return 0.0
        entropy = 0.0
        for count in self.translation_counter.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        return entropy

    def dissipate_heat(self, entropy: float, volume_factor: float = 1e-6):
        """Converte entropia em calor e dissipa via Diamante."""
        # 1 bit de entropia ≈ k_B * T * ln(2) de energia térmica
        k_B = 1.380649e-23  # J/K
        T = 300.0  # K (temperatura ambiente)
        energy_per_bit = k_B * T * math.log(2)  # ≈ 2.87e-21 J

        # A entropia total gera calor
        heat_generated = entropy * energy_per_bit * volume_factor * 1e12  # escala para pJ
        self.total_heat_joules += heat_generated

        # Simula drenagem via Diamante
        if self.diamond:
            power_density = heat_generated / 1e-6  # W/cm³ aproximado
            lifetime = self.diamond.coherence_lifetime(power_density)
        else:
            lifetime = float('inf') if heat_generated < 0.1 else 100.0 / heat_generated

        # Reseta o contador para a próxima janela
        self.translation_counter.clear()

        return heat_generated, lifetime

    def monitor_loop(self, interval_seconds: float = 2.0):
        """Loop de monitoramento contínuo (intervalo reduzido para demo)."""
        self.running = True
        print("Iniciando loop de monitoramento entrópico...")
        while self.running:
            entropy = self.compute_shannon_entropy()
            heat, lifetime = self.dissipate_heat(entropy)
            self.entropy_history.append((time.time(), entropy, heat, lifetime))

            print(f"[Monitor Entrópico] Entropia: {entropy:.4f} bits | "
                  f"Calor gerado: {heat:.6f} pJ | "
                  f"Tempo de coerência restante: {lifetime:.2f} s")

            time.sleep(interval_seconds)

    def start(self):
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        return thread

if __name__ == "__main__":
    monitor = EntropyMonitor()
    # Simula atividade
    monitor.record_translation('observe')
    monitor.record_translation('entangle')
    monitor.record_translation('observe')
    monitor.record_translation('hesitate')

    # Roda uma vez
    entropy = monitor.compute_shannon_entropy()
    heat, life = monitor.dissipate_heat(entropy)
    print(f"Atividade Simetrizada: Entropia={entropy:.4f} bits, Calor={heat:.6f} pJ")
