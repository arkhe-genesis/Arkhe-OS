#!/usr/bin/env python3
"""
COLISÃO DE FASE NO quantum://
Simula conflito de ritmo entre Diamond (rápido) e Axon (lento).
O Meta-Controlador resolve via RDA (DecoupledDiLoCo).
"""

import numpy as np
import time
from dataclasses import dataclass
from typing import List, Tuple

# ==============================
# Simuladores dos Módulos Físicos
# ==============================

class DiamondModule:
    """Simula o módulo Diamante (centro NV) com clock de 10 MHz."""
    def __init__(self):
        self.clock_rate = 10_000_000  # 10 MHz
        self.phase = 0.0
        self.coherence = 0.995
        self.name = "Diamond_NV"

    def tick(self, steps=1):
        self.phase += 2 * np.pi * steps * (1.0 / self.clock_rate)
        self.phase %= 2 * np.pi
        # O diamante é muito estável, quase sem jitter
        jitter = np.random.normal(0, 0.0001)
        self.phase += jitter
        return self.phase

class AxonModule:
    """Simula o módulo Axônio (potencial de ação) com clock de 10 Hz."""
    def __init__(self):
        self.clock_rate = 10  # 10 Hz
        self.phase = 0.0
        self.coherence = 0.85  # menos estável que o diamante
        self.name = "AxonWaveguide"

    def tick(self, steps=1):
        self.phase += 2 * np.pi * steps * (1.0 / self.clock_rate)
        self.phase %= 2 * np.pi
        # O axônio tem mais jitter biológico
        jitter = np.random.normal(0, 0.1)
        self.phase += jitter
        return self.phase

# ==============================
# Barramento quantum://
# ==============================

@dataclass
class QuantumPacket:
    source: str
    phase: float
    timestamp: float
    payload: dict = None

class QuantumBus:
    def __init__(self):
        self.channel = []
        self.collisions = 0
        self.packets_sent = 0

    def send(self, packet: QuantumPacket):
        self.packets_sent += 1
        # Verifica colisão de fase: se dois pacotes chegam com Δfase > π/2
        for existing in self.channel:
            phase_diff = abs(packet.phase - existing.phase) % (2 * np.pi)
            if phase_diff > np.pi / 2 and phase_diff < 3 * np.pi / 2:
                self.collisions += 1
                # print(f"⚠️ COLISÃO: {packet.source} vs {existing.source} | Δφ = {phase_diff:.2f} rad")
                # Método RDA: Radial-Directional Averaging
                # Direções normalizadas (vetores unitários)
                dir_a = np.array([np.cos(packet.phase), np.sin(packet.phase)])
                dir_b = np.array([np.cos(existing.phase), np.sin(existing.phase)])

                sum_dir = dir_a + dir_b
                norm = np.linalg.norm(sum_dir)
                if norm > 0:
                    avg_dir = sum_dir / norm
                    # Fase resolvida = arctan2 da direção média
                    resolved_phase = np.arctan2(avg_dir[1], avg_dir[0])
                    # print(f"   Resolução RDA: φ_resolvida = {resolved_phase:.2f} rad")
                    packet.phase = resolved_phase
                    existing.phase = resolved_phase
        self.channel.append(packet)
        if len(self.channel) > 10:
            self.channel.pop(0)

# ==============================
# Meta-Controlador como Árbitro
# ==============================

class MetaControllerArbiter:
    def __init__(self, bus):
        self.bus = bus
        self.resolved_conflicts = 0
        self.coherence_history = []

    def monitor_and_resolve(self):
        """Monitora o barramento e aplica políticas de coerência."""
        if len(self.bus.channel) < 2:
            return

        phases = [p.phase for p in self.bus.channel]
        coherence = np.abs(np.mean(np.exp(1j * np.array(phases))))
        self.coherence_history.append(coherence)

        # Ação: se coerência cair, forçar resolução via persist
        if coherence < 0.7:
            # print(f"🔧 Meta-Controlador: Coerência baixa ({coherence:.3f}). Forçando persist...")
            self.resolved_conflicts += 1
            # Força alinhamento de fase global
            target_phase = np.arctan2(
                np.mean(np.sin(phases)),
                np.mean(np.cos(phases))
            )
            self.bus.channel.clear()
            # print(f"   Fase global alinhada: φ = {target_phase:.2f} rad")

# ==============================
# Simulação da Colisão
# ==============================

def simulate_phase_collision(duration_seconds=5.0):
    diamond = DiamondModule()
    axon = AxonModule()
    bus = QuantumBus()
    arbiter = MetaControllerArbiter(bus)

    print("═" * 60)
    print("SIMULAÇÃO DE COLISÃO DE FASE NO quantum://")
    print("═" * 60)
    print(f"{'Tempo(s)':<10} {'Diamond φ':<12} {'Axon φ':<12} {'Coerência':<12} {'Status'}")
    print("-" * 60)

    dt = 0.01  # 10 ms por iteração
    steps = int(duration_seconds / dt)

    for step in range(steps):
        t = step * dt

        # Diamond avança (rápido)
        d_phase = diamond.tick(int(diamond.clock_rate * dt))
        bus.send(QuantumPacket("Diamond", d_phase, t))

        # Axon avança (lento, apenas a cada 100 ms)
        if step % 10 == 0:
            a_phase = axon.tick()
            bus.send(QuantumPacket("Axon", a_phase, t))
        else:
            a_phase = axon.phase # fase anterior

        # Meta-Controlador resolve
        arbiter.monitor_and_resolve()

        # Status
        if step % 50 == 0:
            if bus.channel:
                coherence = np.abs(np.mean(np.exp(1j * np.array([p.phase for p in bus.channel]))))
            else:
                coherence = 1.0
            status = f"Col: {bus.collisions}, Res: {arbiter.resolved_conflicts}"
            print(f"{t:<10.2f} {d_phase:<12.3f} {a_phase:<12.3f} {coherence:<12.4f} {status}")

    print("-" * 60)
    print(f"Resultado Final:")
    print(f"  Total de pacotes: {bus.packets_sent}")
    print(f"  Colisões detectadas: {bus.collisions}")
    print(f"  Conflitos resolvidos pelo Meta-Controlador: {arbiter.resolved_conflicts}")
    if arbiter.coherence_history:
        print(f"  Coerência média: {np.mean(arbiter.coherence_history):.4f}")
    print("═" * 60)

if __name__ == "__main__":
    simulate_phase_collision(2.0)
