#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/galactic/consensus.py — Consenso Interestelar para Verificações Cross-Domain
Integração com Substrato 5557: Galactic Ledger Authentication.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import hashlib
import json
import time

@dataclass
class StellarConfirmation:
    """Confirmação de um nó estelar."""
    node_id: str
    branch_id: str
    distance_ly: float
    confirmation_type: str  # "direct", "relay", "historical", "dream"
    weight: float
    timestamp: float
    content_hash: str

class GalacticDomainConsensus:
    """
    Consenso interestelar para validação de verificações cross-domain.
    Uma afirmação é considerada universalmente válida se:
    1. Passa no ConsistencyOracle local (7 checks)
    2. É confirmada por ≥ Q nós estelares independentes
    3. A consistência temporal é mantida em todas as branches
    4. Não cria paradoxo causal com o ledger galáctico
    """

    MIN_STELLAR_CONFIRMATIONS = 3
    STELLAR_QUORUM_BASE = 5.0
    PARADOX_THRESHOLD = 0.01

    def __init__(self, local_oracle, local_ledger):
        self.local_oracle = local_oracle
        self.local_ledger = local_ledger
        self.stellar_nodes: Dict[str, Dict] = {}
        self.confirmations: Dict[str, List[StellarConfirmation]] = {}

    def register_stellar_node(
        self,
        node_id: str,
        branch_id: str,
        distance_ly: float,
        confirmation_type: str,
    ) -> Dict:
        """Registra nó estelar conhecido."""
        weights = {
            "direct": 1.0,
            "relay": 0.8,
            "historical": 0.5,
            "dream": 0.3,  # Nós Filamentares
        }

        self.stellar_nodes[node_id] = {
            "branch_id": branch_id,
            "distance_ly": distance_ly,
            "confirmation_type": confirmation_type,
            "weight": weights.get(confirmation_type, 0.0),
            "first_seen": time.time(),
            "last_active": None,
        }

        # Mocking local_ledger.record if local_ledger exists
        if hasattr(self.local_ledger, 'record'):
            self.local_ledger.record("stellar_node_registered", {
                "node_id": node_id,
                "branch_id": branch_id,
                "distance_ly": distance_ly,
                "type": confirmation_type,
            })

        return self.stellar_nodes[node_id]

    def submit_stellar_confirmation(
        self,
        message_id: str,
        node_id: str,
        content_hash: str,
        verification_result: Dict,
    ) -> Dict:
        """Recebe confirmação de nó estelar."""
        if node_id not in self.stellar_nodes:
            return {"error": "Nó estelar não registrado"}

        node = self.stellar_nodes[node_id]
        confirmation = StellarConfirmation(
            node_id=node_id,
            branch_id=node["branch_id"],
            distance_ly=node["distance_ly"],
            confirmation_type=node["confirmation_type"],
            weight=node["weight"],
            timestamp=time.time(),
            content_hash=content_hash,
        )

        # Registrar confirmação
        if message_id not in self.confirmations:
            self.confirmations[message_id] = []
        self.confirmations[message_id].append(confirmation)

        node["last_active"] = time.time()

        # Verificar quórum
        quorum_status = self._check_quorum(message_id)

        if hasattr(self.local_ledger, 'record'):
            self.local_ledger.record("stellar_confirmation", {
                "message_id": message_id,
                "node_id": node_id,
                "quorum_reached": quorum_status["quorum_reached"],
                "confirmation_count": quorum_status["unique_nodes"],
            })

        return quorum_status

    def _check_quorum(self, message_id: str) -> Dict:
        """Verifica se mensagem atingiu quórum estelar."""
        if message_id not in self.confirmations:
            return {"quorum_reached": False, "unique_nodes": 0, "weighted_score": 0}

        confirmations = self.confirmations[message_id]
        unique_nodes = len(set(c.node_id for c in confirmations))
        weighted_score = sum(c.weight for c in confirmations)

        quorum_reached = (
            unique_nodes >= self.MIN_STELLAR_CONFIRMATIONS and
            weighted_score >= self.STELLAR_QUORUM_BASE
        )

        return {
            "quorum_reached": quorum_reached,
            "unique_nodes": unique_nodes,
            "required_nodes": self.MIN_STELLAR_CONFIRMATIONS,
            "weighted_score": round(weighted_score, 4),
            "weight_required": self.STELLAR_QUORUM_BASE,
            "total_confirmations": len(confirmations),
        }

    def validate_universal_claim(
        self,
        claim: str,
        domains: List[str],
        local_verification: Dict,
    ) -> Dict:
        """
        Validação universal combinando verificação local + consenso estelar.
        """
        # 1. Verificação local (ConsistencyOracle)
        local_valid = local_verification.get("consistent", False)
        local_score = local_verification.get("score", 0)

        # 2. Verificação de quórum estelar
        message_id = hashlib.sha3_256(
            f"{claim}:{domains}:{time.time()}".encode()
        ).hexdigest()[:16]

        quorum = self._check_quorum(message_id)

        # 3. Combinação de scores
        if quorum["quorum_reached"]:
            combined_score = min(1.0, (local_score + quorum["weighted_score"] / self.STELLAR_QUORUM_BASE) / 2)
        else:
            combined_score = local_score * 0.5  # Penalidade sem consenso estelar

        # 4. Verificação de paradoxo
        paradox_free = local_verification.get("paradox_type") is None

        # 5. Decisão final
        overall_valid = (
            local_valid and
            paradox_free and
            (quorum["quorum_reached"] or local_score >= 0.95)  # Alta confiança local pode compensar
        )

        return {
            "claim_hash": hashlib.sha3_256(claim.encode()).hexdigest()[:16],
            "domains": domains,
            "local_valid": local_valid,
            "local_score": local_score,
            "stellar_quorum": quorum,
            "combined_score": round(combined_score, 6),
            "paradox_free": paradox_free,
            "overall_valid": overall_valid,
            "verdict": "UNIVERSALLY_AUTHENTIC" if overall_valid else "LOCALLY_VERIFIED_ONLY",
            "canonical_seal": hashlib.sha3_256(
                json.dumps({
                    "claim_hash": claim,
                    "domains": domains,
                    "local_score": local_score,
                    "stellar_score": quorum["weighted_score"],
                    "valid": overall_valid,
                }, sort_keys=True).encode()
            ).hexdigest(),
        }
