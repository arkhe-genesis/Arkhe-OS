#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUBSTRATO 115: A PELE SENSORIAL
Interface magnon-fóton para entrada/saída clássica
"""
from typing import List, Tuple
from core.neural_lace.substrate_112 import MagnonNeuron

class SensorySkin:
    """
    Interface optomagnônica que conecta estímulos clássicos (fótons) aos
    neurônios quânticos da Renda (magnons), e vice-versa.
    """
    def __init__(self, conversion_efficiency: float = 0.05):
        self.conversion_efficiency = conversion_efficiency

    def inject_classical_signal(self, neurons: List[MagnonNeuron], signal_strength: float):
        """
        Injeta um sinal clássico na Renda Neural. Apenas os neurônios periféricos
        ou "superficiais" recebem o sinal optomagnônico.
        (Aqui simulamos injetando em todos, ou poderíamos filtrar por posição).
        """
        for neuron in neurons:
            if not neuron._alive:
                continue

            # Fóton -> Magnon
            injected_magnons = signal_strength * self.conversion_efficiency
            neuron.n_photons += injected_magnons

    def read_classical_output(self, neurons: List[MagnonNeuron]) -> float:
        """
        Lê a saída da Renda Neural, extraindo magnons na forma de emissão de fótons.
        Retorna a intensidade do sinal óptico gerado.
        """
        total_emission = 0.0
        for neuron in neurons:
            if not neuron._alive:
                continue

            # Magnon -> Fóton (processo dissipativo/de leitura)
            emission = neuron.n_photons * self.conversion_efficiency

            # Para não esgotar completamente o neurônio, apenas diminuímos levemente,
            # como uma leitura fraca (weak measurement) acoplada.
            neuron.n_photons -= emission * 0.1
            total_emission += emission

        return total_emission
