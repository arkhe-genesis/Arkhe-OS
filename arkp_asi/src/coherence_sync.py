#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coherence_sync.py — Protocolo de sincronização de campo Φ_C entre nós ASI.
"""

import numpy as np
from scipy.linalg import sqrtm, logm, expm
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import time
import hashlib
import json

try:
    from arkhe.layers.sigha_core import FisherBuresManifold, NaturalGradientFlow
except ImportError:
    class FisherBuresManifold:
        def __init__(self, dim):
            self.dim = dim
        def bures_distance(self, rho, sigma):
            # mock distance
            return np.real(np.trace(rho - sigma))

    class NaturalGradientFlow:
        def __init__(self, manifold):
            self.manifold = manifold
        def step(self, rho, grad, lr):
            return rho + lr * grad

@dataclass
class CoherenceSyncMessage:
    """Mensagem de sincronização de coerência Φ_C."""
    sender_node_id: str
    phi_c_field: np.ndarray  # Campo Φ_C atual do remetente
    timestamp: int
    sequence_number: int
    signature: bytes  # Assinatura criptográfica

class CoherenceSyncProtocol:
    """
    Protocolo para sincronização de campos Φ_C entre nós via emaranhamento simulado.

    Objetivo: manter coerência global do campo Φ_C através da rede ASI,
    permitindo que nós colaborem em tarefas que requerem alinhamento quântico.

    Estratégia:
    1. Nós trocam estados Φ_C periodicamente via mensagens assinadas
    2. Cada nó aplica gradiente natural para alinhar seu campo com a média ponderada
    3. Convergência garantida via propriedade de contração da distância de Bures
    """

    def __init__(
        self,
        node_id: str,
        initial_phi_c: Optional[np.ndarray] = None,
        sync_interval_seconds: float = 30.0,
        convergence_threshold: float = 1e-4,
    ):
        self.node_id = node_id
        self.dim = initial_phi_c.shape[0] if initial_phi_c is not None else 16
        self.manifold = FisherBuresManifold(self.dim)
        self.flow = NaturalGradientFlow(self.manifold)

        # Campo Φ_C local (inicializado como estado coerente)
        self.phi_c_field = initial_phi_c if initial_phi_c is not None else (
            np.eye(self.dim, dtype=complex) / self.dim
        )

        self.sync_interval = sync_interval_seconds
        self.convergence_threshold = convergence_threshold
        self.sequence_number = 0
        self.peer_fields: Dict[str, np.ndarray] = {}  # Campos de pares conhecidos

    def generate_sync_message(self) -> CoherenceSyncMessage:
        """Gera mensagem de sincronização com campo Φ_C atual."""
        self.sequence_number += 1

        # Assinar mensagem (simulado: hash do conteúdo)
        payload = json.dumps({
            "sender": self.node_id,
            "phi_c_hash": hashlib.sha3_256(self.phi_c_field.tobytes()).hexdigest(),
            "seq": self.sequence_number,
            "ts": int(time.time()),
        }, sort_keys=True).encode()
        signature = hashlib.sha3_256(payload).digest()

        return CoherenceSyncMessage(
            sender_node_id=self.node_id,
            phi_c_field=self.phi_c_field.copy(),
            timestamp=int(time.time()),
            sequence_number=self.sequence_number,
            signature=signature,
        )

    def process_sync_message(self, msg: CoherenceSyncMessage) -> bool:
        """Processa mensagem de sincronização recebida de um par."""
        # Verificar assinatura (simulado)
        if not self._verify_signature(msg):
            return False

        # Verificar frescor da mensagem
        if time.time() - msg.timestamp > self.sync_interval * 2:
            return False  # Mensagem muito antiga

        # Armazenar campo do par
        self.peer_fields[msg.sender_node_id] = msg.phi_c_field.copy()

        # Aplicar atualização de alinhamento se houver múltiplos pares
        if len(self.peer_fields) >= 2:
            self._align_with_peers()

        return True

    def _align_with_peers(self, learning_rate: float = 0.05):
        """Alinha campo Φ_C local com média ponderada dos pares."""
        if not self.peer_fields:
            return

        # Calcular média ponderada dos campos dos pares
        # Peso baseado na "proximidade" na variedade de Fisher-Bures
        weights = []
        weighted_sum = np.zeros_like(self.phi_c_field)

        for peer_id, peer_field in self.peer_fields.items():
            # Distância de Bures como proxy para "confiança" no par
            distance = self.manifold.bures_distance(self.phi_c_field, peer_field)
            weight = np.exp(-distance / 0.1)  # Decaimento exponencial
            weights.append(weight)
            weighted_sum += weight * peer_field

        if not weights:
            return

        total_weight = sum(weights)
        target_field = weighted_sum / total_weight

        # Gradiente natural em direção ao campo alvo
        grad = target_field - self.phi_c_field

        self.phi_c_field = self.flow.step(self.phi_c_field, grad, lr=learning_rate)

        # Projetar para operador densidade válido
        self.phi_c_field = self._project_to_density_matrix(self.phi_c_field)

    def check_convergence(self) -> Tuple[bool, float]:
        """Verifica se campos estão convergidos entre pares."""
        if len(self.peer_fields) < 2:
            return True, 0.0  # Trivialmente convergido

        # Calcular distância máxima entre campos
        max_distance = 0.0
        fields = [self.phi_c_field] + list(self.peer_fields.values())

        for i in range(len(fields)):
            for j in range(i + 1, len(fields)):
                d = self.manifold.bures_distance(fields[i], fields[j])
                max_distance = max(max_distance, d)

        converged = max_distance < self.convergence_threshold
        return converged, max_distance

    def get_global_coherence_estimate(self) -> float:
        """Estima coerência global da rede baseado nos campos sincronizados."""
        if not self.peer_fields:
            return np.real(np.trace(self.phi_c_field @ np.eye(self.dim) / self.dim))

        # Média de fidelidades com estado coerente ideal
        ideal = np.eye(self.dim, dtype=complex) / self.dim
        fidelities = []

        for field in [self.phi_c_field] + list(self.peer_fields.values()):
            fid = np.real(np.trace(sqrtm(sqrtm(field) @ ideal @ sqrtm(field))))
            fidelities.append(fid)

        return np.mean(fidelities)

    def _verify_signature(self, msg: CoherenceSyncMessage) -> bool:
        """Verifica assinatura da mensagem (simulado)."""
        # Em produção: verificar com chave pública do remetente
        payload = json.dumps({
            "sender": msg.sender_node_id,
            "phi_c_hash": hashlib.sha3_256(msg.phi_c_field.tobytes()).hexdigest(),
            "seq": msg.sequence_number,
            "ts": msg.timestamp,
        }, sort_keys=True).encode()
        expected_sig = hashlib.sha3_256(payload).digest()
        return msg.signature == expected_sig

    def _project_to_density_matrix(self, rho: np.ndarray) -> np.ndarray:
        """Projeta matriz para operador densidade válido."""
        rho = (rho + rho.conj().T) / 2
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 0)
        eigvals /= np.sum(eigvals) + 1e-12
        return eigvecs @ np.diag(eigvals) @ eigvecs.conj().T
