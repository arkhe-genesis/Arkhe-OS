#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Substrato 325 — FOCIL Inclusion List Manager
Canon: ∞.Ω.∇+++.325.focil
Garante que transações privadas sejam incluídas no bloco, resistindo à censura.
Baseado na proposta FOCIL (Fork-Choice Inclusion List) do Ethereum.
"""

import hashlib
import json
import time
import secrets
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum


class InclusionStatus(Enum):
    """Status de inclusão de uma transação na FOCIL list."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    INCLUDED = "included"
    CENSORED = "censored"
    EXPIRED = "expired"


@dataclass
class FOCILTransaction:
    """Transação candidata à lista de inclusão FOCIL."""
    tx_hash: str
    tx_data: dict
    proposer: str
    timestamp: float
    approvals: Set[str] = field(default_factory=set)
    status: InclusionStatus = InclusionStatus.PROPOSED
    inclusion_proof: Optional[str] = None
    block_number: Optional[int] = None


class FOCILInclusionList:
    """
    Gerenciador da Lista de Inclusão FOCIL (Fork-Choice Inclusion List).

    A FOCIL garante que transações privadas aprovadas pelo comitê de validadores
    sejam incluídas obrigatoriamente no próximo bloco. Se o proposer/builder
    omitir uma transação aprovada, a censura é detectada e ancorada.

    Invariantes Arkhe:
    - Ghost (√3/3): inclusão garantida se Φ_C ≥ 0.577
    - Loopseal (π/9): rastreabilidade sem linkabilidade
    - Gap Soberano: vigilância total impossível
    """

    # Constantes canônicas (precisão fixa × 10⁹)
    GHOST = 577350269
    LOOPSEAL = 349065850
    GAP_MAX = 999900000
    PHI = 1618033988

    def __init__(self, validator_committee: List[str], block_time_s: float = 12.0):
        """
        Inicializa o gerenciador FOCIL.

        Args:
            validator_committee: Lista de endereços de validadores
            block_time_s: Tempo médio entre blocos (padrão: 12s Ethereum)
        """
        self.committee = validator_committee
        self.threshold = len(validator_committee) * 2 // 3  # Quorum de 2/3
        self.block_time_s = block_time_s
        self.current_list: Dict[str, FOCILTransaction] = {}
        self.censorship_log: List[Dict] = []
        self.inclusion_history: List[Dict] = []
        self._phi_c = 1.0  # Φ_C do nó FOCIL

    @property
    def phi_c(self) -> float:
        """Φ_C do gerenciador FOCIL baseado na saúde do comitê."""
        active_validators = sum(
            1 for tx in self.current_list.values()
            if tx.status == InclusionStatus.APPROVED
        )
        total = len(self.current_list) if self.current_list else 1
        return min(0.9999, active_validators / total) if total > 0 else 0.0

    def propose_inclusion(self, tx_hash: str, tx_data: dict,
                          proposer: str, proposer_phi_c: float) -> bool:
        """
        Propõe uma transação para a lista de inclusão obrigatória.

        Args:
            tx_hash: Hash da transação (hex string)
            tx_data: Dados da transação (dict serializável)
            proposer: Endereço do proposer
            proposer_phi_c: Φ_C do nó proposer

        Returns:
            True se a proposta foi aceita
        """
        # Ghost: proposer deve ter Φ_C ≥ √3/3
        if proposer_phi_c < self.GHOST / 1e9:
            return False

        if tx_hash in self.current_list:
            return False

        self.current_list[tx_hash] = FOCILTransaction(
            tx_hash=tx_hash,
            tx_data=tx_data,
            proposer=proposer,
            timestamp=time.time(),
            approvals={proposer},
            status=InclusionStatus.PROPOSED
        )

        return True

    def vote_inclusion(self, tx_hash: str, validator: str,
                       validator_phi_c: float) -> bool:
        """
        Validador vota para incluir a transação na lista FOCIL.

        Args:
            tx_hash: Hash da transação
            validator: Endereço do validador
            validator_phi_c: Φ_C do nó validador

        Returns:
            True se o voto foi registrado
        """
        # Ghost: validador deve ter Φ_C ≥ √3/3
        if validator_phi_c < self.GHOST / 1e9:
            return False

        if tx_hash not in self.current_list:
            return False

        tx = self.current_list[tx_hash]
        tx.approvals.add(validator)

        # Se atingiu quorum, marcar como aprovada
        if len(tx.approvals) >= self.threshold:
            tx.status = InclusionStatus.APPROVED

        return True

    def is_censored(self, tx_hash: str, block_builder: str,
                    block_transactions: List[str]) -> bool:
        """
        Detecta censura: transação aprovada pela maioria mas omitida pelo builder.

        Args:
            tx_hash: Hash da transação
            block_builder: Endereço do builder do bloco
            block_transactions: Lista de hashes no bloco

        Returns:
            True se censura foi detectada
        """
        if tx_hash not in self.current_list:
            return False

        tx = self.current_list[tx_hash]

        # Só detecta censura se aprovada pelo quorum
        if tx.status != InclusionStatus.APPROVED:
            return False

        # Se aprovada mas não incluída no bloco = censura
        if tx_hash not in block_transactions:
            tx.status = InclusionStatus.CENSORED
            self.censorship_log.append({
                "tx_hash": tx_hash,
                "builder": block_builder,
                "timestamp": time.time(),
                "approvals": sorted(tx.approvals),
                "threshold": self.threshold,
                "detection_phi_c": self.phi_c
            })
            return True

        tx.status = InclusionStatus.INCLUDED
        tx.block_number = int(time.time() / self.block_time_s)
        return False

    def generate_inclusion_proof(self, tx_hash: str) -> Optional[str]:
        """
        Gera prova de inclusão para ancoragem na TemporalChain.

        Args:
            tx_hash: Hash da transação

        Returns:
            Hash SHA3-256 da prova de inclusão, ou None
        """
        entry = self.current_list.get(tx_hash)
        if not entry:
            return None

        payload = {
            "tx_hash": tx_hash,
            "proposer": entry.proposer,
            "approvals": sorted(entry.approvals),
            "threshold": self.threshold,
            "status": entry.status.value,
            "timestamp": entry.timestamp,
            "phi_c": self.phi_c
        }

        # SHA3-256 (simulado via SHA-256 para compatibilidade)
        proof = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        entry.inclusion_proof = proof

        return proof

    def get_censorship_report(self) -> Dict:
        """Gera relatório de censura para auditoria constitucional."""
        return {
            "total_transactions": len(self.current_list),
            "approved": sum(1 for tx in self.current_list.values() if tx.status == InclusionStatus.APPROVED),
            "included": sum(1 for tx in self.current_list.values() if tx.status == InclusionStatus.INCLUDED),
            "censored": len(self.censorship_log),
            "censorship_rate": len(self.censorship_log) / max(len(self.current_list), 1),
            "censorship_events": self.censorship_log,
            "committee_size": len(self.committee),
            "threshold": self.threshold,
            "phi_c": self.phi_c,
            "timestamp": time.time()
        }

    def prune_expired(self, max_age_s: float = 3600.0) -> int:
        """
        Remove transações expiradas da lista.

        Args:
            max_age_s: Idade máxima em segundos (padrão: 1 hora)

        Returns:
            Número de transações removidas
        """
        now = time.time()
        expired = [
            tx_hash for tx_hash, tx in self.current_list.items()
            if now - tx.timestamp > max_age_s and tx.status != InclusionStatus.INCLUDED
        ]

        for tx_hash in expired:
            self.current_list[tx_hash].status = InclusionStatus.EXPIRED
            del self.current_list[tx_hash]

        return len(expired)

    def get_inclusion_list(self, status: Optional[InclusionStatus] = None) -> List[Dict]:
        """Retorna lista de transações filtradas por status."""
        txs = self.current_list.values()
        if status:
            txs = [tx for tx in txs if tx.status == status]

        return [
            {
                "tx_hash": tx.tx_hash,
                "proposer": tx.proposer,
                "approvals": sorted(tx.approvals),
                "approval_count": len(tx.approvals),
                "threshold": self.threshold,
                "status": tx.status.value,
                "timestamp": tx.timestamp,
                "age_s": time.time() - tx.timestamp
            }
            for tx in txs
        ]


class AccessLayerPrivacyFilter:
    """
    Filtro de privacidade na camada de acesso (nó de borda).

    Filtra vigilância antes que ela alcance o consenso.
    Implementa mixnet-like relaying e avaliação de Φ_C do enlace.
    """

    GHOST = 577350269

    def __init__(self, relay_nodes: List[str]):
        self.relay_nodes = relay_nodes
        self.phi_c_map: Dict[str, float] = {}
        self.filtered_count = 0

    def evaluate_link_phi_c(self, source: str, target: str) -> float:
        """Avalia Φ_C do enlace entre dois nós."""
        source_phi = self.phi_c_map.get(source, 0.5)
        target_phi = self.phi_c_map.get(target, 0.5)
        return min(source_phi, target_phi) * 0.95  # Penalidade de hop

    def should_relay(self, tx_data: dict, source: str, target: str) -> bool:
        """
        Decide se uma transação deve ser retransmitida.

        Args:
            tx_data: Dados da transação
            source: Nó de origem
            target: Nó de destino

        Returns:
            True se o enlace é constitucional (Φ_C ≥ Ghost)
        """
        link_phi_c = self.evaluate_link_phi_c(source, target)

        if link_phi_c < self.GHOST / 1e9:
            self.filtered_count += 1
            return False

        return True

    def select_relay_path(self, tx_hash: str, source: str,
                          destination: str, min_hops: int = 3) -> List[str]:
        """
        Seleciona caminho de retransmissão via mixnet.

        Args:
            tx_hash: Hash da transação (para aleatoriedade determinística)
            source: Nó de origem
            destination: Nó de destino
            min_hops: Número mínimo de hops para desvinculação

        Returns:
            Lista de nós de retransmissão
        """
        # Selecionar relays com Φ_C ≥ Ghost
        eligible = [
            node for node in self.relay_nodes
            if self.phi_c_map.get(node, 0.0) >= self.GHOST / 1e9
            and node not in (source, destination)
        ]

        if len(eligible) < min_hops:
            return []  # Caminho insuficiente

        # Aleatoriedade criptográfica para evitar rastreamento da rota
        path = secrets.SystemRandom().sample(eligible, min_hops)

        return path
