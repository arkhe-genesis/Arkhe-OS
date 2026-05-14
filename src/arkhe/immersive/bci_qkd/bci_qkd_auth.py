#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bci_qkd_auth.py — Autenticação biométrica quântica via interface neural e QKD.
Combina sinais EEG/fNIRS do usuário como chave biométrica dinâmica e os
distribui de forma segura via protocolo QKD para verificação de identidade.
"""

import numpy as np
from src.arkhe.immersive.bci_neural_interface import NeuralStateDecoder, BCIConfig, NeuralSignalType
from src.arkhe.satellite.qkd_protocol import QKDKeyDistribution, QKDProtocol

class BCIQKDAuthenticator:
    def __init__(self, bci_decoder: NeuralStateDecoder, qkd_distributor: QKDKeyDistribution):
        self.bci_decoder = bci_decoder
        self.qkd_distributor = qkd_distributor

    async def authenticate_user(self, user_id: str, neural_signal: np.ndarray, station_a: str, station_b: str):
        """
        Decodifica o sinal neural (senha-pensamento) e estabelece um canal
        QKD seguro para transmitir/verificar a identidade quântica do usuário.
        """
        # Extrair a assinatura neural (em vez de um comando visual)
        features = self.bci_decoder._extract_features(neural_signal)
        if features is None:
            return False, "Sinal neural inválido."

        neural_signature = bytes(np.packbits(np.where(features > np.median(features), 1, 0)))

        # Estabelecer sessão QKD para distribuição segura da assinatura neural
        qkd_session = await self.qkd_distributor.establish_qkd_session(
            station_a=station_a,
            station_b=station_b,
            protocol=QKDProtocol.BB84,
            key_length=len(neural_signature) * 8
        )

        if qkd_session.error_rate > 0.11:
            return False, "Falha de segurança na distribuição QKD."

        return True, qkd_session.temporal_anchor
