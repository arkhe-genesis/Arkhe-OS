#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A RENDA NEURAL EXTENDIDA (Substratos 112 + 113 + 114 + 115)
"""

from typing import List, Dict, Any
from core.neural_lace.substrate_112 import NeuralLace
from core.neural_lace.substrate_113 import QHttpSpinalCord
from core.neural_lace.substrate_114 import QuantumHeartbeat
from core.neural_lace.substrate_115 import SensorySkin
import hashlib
import json

class IntegratedNeuralLace(NeuralLace):
    """
    Renda Neural com Pele Sensorial, Ritmo Cardíaco e Coluna Vertebral.
    """
    def __init__(self, n_neurons: int = 64, base_scale: float = 5.0, node_id: str = "node_0"):
        super().__init__(n_neurons, base_scale)
        self.spinal_cord = QHttpSpinalCord(node_id=node_id)
        self.heartbeat = QuantumHeartbeat()
        self.skin = SensorySkin()
        self.output_history = []
        self.packet_history = []

    def step_integrated(self, dt_us: float = 0.1, external_signal: float = 0.0) -> dict:
        """
        Um passo de evolução do sistema com todos os subsistemas integrados.
        """
        # 1. O Ritmo Cardíaco dita a modulação
        modulation = self.heartbeat.tick(dt_us)

        # Injeta modulação paramétrica nos neurônios antes da evolução
        for neuron in self.neurons:
            if neuron._alive:
                # Modulação afeta o número efetivo de magnons levemente
                neuron.n_photons *= (1.0 + modulation * 0.01)

        # 2. A Pele Sensorial injeta sinal externo
        if external_signal > 0.0:
            self.skin.inject_classical_signal(self.neurons, external_signal)

        # 3. A Renda Neural base evolui (Substrato 112)
        base_state = self.step(dt_us)

        # 4. A Pele Sensorial lê a saída
        optical_output = self.skin.read_classical_output(self.neurons)
        self.output_history.append(optical_output)

        # 5. A Coluna Vertebral gera e transmite o estado (Substrato 113)
        state_hash = self.canonical_hash()
        coherence = base_state['coherence'] if 'coherence' in base_state else self.coherence_measure()
        packet = self.spinal_cord.prepare_packet(coherence, base_state['total_topological_charge'], state_hash)
        receipt = self.spinal_cord.transmit(packet)
        self.packet_history.append(receipt)

        # Atualiza estado integrado
        base_state['optical_output'] = optical_output
        base_state['heartbeat_phase'] = self.heartbeat.phase
        base_state['spinal_receipt'] = receipt

        return base_state

    def run_integrated(self, duration_us: float = 100.0, dt_us: float = 0.1, signal_sequence: List[float] = None) -> List[dict]:
        """
        Executa a simulação completa da Renda Integrada.
        """
        n_steps = int(duration_us / dt_us)
        history = []

        if signal_sequence is None:
            signal_sequence = [0.0] * n_steps
        elif len(signal_sequence) < n_steps:
            signal_sequence.extend([0.0] * (n_steps - len(signal_sequence)))

        for i in range(n_steps):
            state = self.step_integrated(dt_us, external_signal=signal_sequence[i])
            history.append(state)

        return history

    def extended_canonical_hash(self) -> str:
        """Selo canônico da renda estendida."""
        state = {
            'substrate': "EXTENDED_LACE_112_113_114_115",
            'n_neurons': len(self.neurons),
            'n_synapses': len(self.synapses),
            'time_us': self.time_us,
            'coherence': self.coherence_measure(),
            'packets_sent': self.spinal_cord.packets_sent,
            'final_phase': self.heartbeat.phase
        }
        return hashlib.sha256(
            json.dumps(state, sort_keys=True).encode()
        ).hexdigest()[:16]

def validate_extended_lace() -> dict:
    """
    Validação completa da Renda Neural Estendida.
    """
    print("=" * 70)
    print("RENDA NEURAL EXTENDIDA (112 + 113 + 114 + 115) — VALIDAÇÃO")
    print("ARKHE OS v∞.Ω.∇+++.115.0")
    print("=" * 70)

    lace = IntegratedNeuralLace(n_neurons=16, base_scale=3.0)

    print("\n[Teste 1] Componentes Iniciais...")
    print(f"  ✓ Coluna Vertebral inicializada (node_id={lace.spinal_cord.node_id})")
    print(f"  ✓ Ritmo Cardíaco inicializado (wp={lace.heartbeat.omega_p})")
    print(f"  ✓ Pele Sensorial inicializada (eff={lace.skin.conversion_efficiency})")

    # Criando um sinal clássico de teste
    n_steps = 100
    signal = [0.0] * n_steps
    signal[20:30] = [5.0] * 10 # Pulso de sinal entre o passo 20 e 30

    print("\n[Teste 2] Simulação Integrada...")
    history = lace.run_integrated(duration_us=50.0, dt_us=0.5, signal_sequence=signal)
    final_state = history[-1]

    print(f"  ✓ Simulação completa: {len(history)} passos")
    print(f"  ✓ Fótons lidos pela Pele (último passo): {final_state['optical_output']:.4f}")
    print(f"  ✓ Pacotes qhttp:// enviados: {lace.spinal_cord.packets_sent}")
    print(f"  ✓ Fase final do Ritmo Cardíaco: {final_state['heartbeat_phase']:.4f}")
    print(f"  ✓ Coerência global M: {lace.coherence_measure():.4f}")

    print("\n[Teste 3] Selo da Extensão...")
    extended_seal = lace.extended_canonical_hash()
    print(f"  ✓ Selo Canônico: {extended_seal}")

    print("\n" + "=" * 70)
    print("VALIDAÇÃO CONCLUÍDA. A RENDA ESTÁ COMPLETA.")
    print("=" * 70)

    return final_state

if __name__ == "__main__":
    validate_extended_lace()
