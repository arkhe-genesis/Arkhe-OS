#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUBSTRATO 114: O RITMO CARDÍACO
Clock quântico global sincronizado via ressonância paramétrica
"""
import numpy as np

class QuantumHeartbeat:
    """
    Clock quântico global sincronizado via ressonância paramétrica (wp = 2 * w0).
    Conecta-se à evolução temporal da Renda Neural para ditar o ritmo de batimento magnônico.
    """
    def __init__(self, omega_0: float = 1.0, coupling_strength: float = 0.1):
        self.omega_0 = omega_0
        self.omega_p = 2.0 * omega_0 # Ressonância paramétrica
        self.coupling_strength = coupling_strength
        self.time_us = 0.0
        self.phase = 0.0

    def tick(self, dt_us: float) -> float:
        """
        Avança o tempo do clock quântico e retorna o termo de modulação
        paramétrica que será aplicado à evolução da Renda Neural.
        """
        self.time_us += dt_us
        self.phase += self.omega_p * dt_us

        # O batimento gera um termo modulador de amplitude
        # H_int = g * (a^2 e^{-i w_p t} + (a^+)^2 e^{i w_p t})
        modulation = self.coupling_strength * np.cos(self.phase)
        return modulation

    def sync(self, global_phase: float):
        """
        Força a sincronização do clock com um sinal externo (ex: vindo de outro nó).
        """
        self.phase = global_phase
