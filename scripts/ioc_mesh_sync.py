#!/usr/bin/env python3
"""
SUBSTRATO 43 — IOC MESH SYNC
Protocolo de Sincronização de IOCs via Merkle-Gossip e CRDT
Garante consistência distribuída sem ponto único de falha.
Autor: Ferreiro da Catedral Arkhe(N)
"""

import hashlib
import json
import time
import uuid
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class IOCUpdate:
    """Uma atualização de IOC (adição ou remoção)."""
    update_id: str
    ioc_type: str
    value: str
    action: str  # "ADD", "REMOVE"
    timestamp: float
    origin_node: str
    signature: str

    def hash(self) -> str:
        content = f"{self.ioc_type}:{self.value}:{self.action}:{self.timestamp}:{self.origin_node}"
        return hashlib.sha256(content.encode()).hexdigest()

class MerkleNode:
    def __init__(self, left=None, right=None, content=None):
        self.left = left
        self.right = right
        if content:
            self.hash = hashlib.sha256(content.encode()).hexdigest()
        elif left and right:
            self.hash = hashlib.sha256((left.hash + right.hash).encode()).hexdigest()
        else:
            self.hash = "0" * 64

class IOCMeshSync:
    """
    Motor de sincronização distribuída para o Guardião das Torres.
    Utiliza Gossip para propagação e Merkle Trees para verificação de estado.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.active_iocs: Dict[str, Dict] = {}  # key -> ioc_data
        self.lww_set: Dict[str, float] = {}    # key -> timestamp (Last-Write-Wins)
        self.peers: Set[str] = set()
        self.merkle_root: str = ""
        self.sync_log: List[IOCUpdate] = []

    def add_ioc(self, ioc_type: str, value: str, confidence: float = 1.0):
        """Adiciona um IOC localmente e gera atualização."""
        key = f"{ioc_type}:{value}"
        timestamp = time.time()

        update = IOCUpdate(
            update_id=str(uuid.uuid4()),
            ioc_type=ioc_type,
            value=value,
            action="ADD",
            timestamp=timestamp,
            origin_node=self.node_id,
            signature=self._sign_update(key, timestamp)
        )

        self._apply_update(update)
        return update

    def remove_ioc(self, ioc_type: str, value: str):
        """Remove um IOC localmente e gera atualização."""
        key = f"{ioc_type}:{value}"
        timestamp = time.time()

        update = IOCUpdate(
            update_id=str(uuid.uuid4()),
            ioc_type=ioc_type,
            value=value,
            action="REMOVE",
            timestamp=timestamp,
            origin_node=self.node_id,
            signature=self._sign_update(key, timestamp)
        )

        self._apply_update(update)
        return update

    def _apply_update(self, update: IOCUpdate):
        """Aplica atualização usando lógica LWW-Set (Last-Write-Wins)."""
        key = f"{update.ioc_type}:{update.value}"

        # Só aplica se o timestamp for maior que o existente
        if key not in self.lww_set or update.timestamp > self.lww_set[key]:
            self.lww_set[key] = update.timestamp
            if update.action == "ADD":
                self.active_iocs[key] = {
                    "type": update.ioc_type,
                    "value": update.value,
                    "timestamp": update.timestamp,
                    "origin": update.origin_node
                }
            else:
                self.active_iocs.pop(key, None)

            self.sync_log.append(update)
            self._rebuild_merkle_tree()
            return True
        return False

    def _rebuild_merkle_tree(self):
        """Reconstrói a Merkle Tree do estado atual dos IOCs."""
        sorted_keys = sorted(self.active_iocs.keys())
        if not sorted_keys:
            self.merkle_root = "0" * 64
            return

        leaves = [MerkleNode(content=f"{k}:{self.lww_set[k]}") for k in sorted_keys]

        while len(leaves) > 1:
            if len(leaves) % 2 != 0:
                leaves.append(leaves[-1])

            new_level = []
            for i in range(0, len(leaves), 2):
                new_level.append(MerkleNode(left=leaves[i], right=leaves[i+1]))
            leaves = new_level

        self.merkle_root = leaves[0].hash

    def gossip_sync(self, peer_root: str, peer_id: str) -> List[IOCUpdate]:
        """
        Compara o Merkle Root local com o do par.
        Se houver divergência, retorna as atualizações necessárias.
        """
        if peer_root == self.merkle_root:
            return []  # Em sincronia

        # Em produção: Implementar busca binária na árvore para encontrar deltas
        # Aqui: Retornar todo o log para simplificação da demo
        return self.sync_log

    def receive_updates(self, updates: List[IOCUpdate]):
        """Recebe e aplica uma lista de atualizações de pares."""
        applied_count = 0
        for update in updates:
            if self._apply_update(update):
                applied_count += 1
        return applied_count

    def _sign_update(self, key: str, timestamp: float) -> str:
        """Gera um selo de invariância para a atualização."""
        # Em produção: Assinatura ECDSA
        content = f"{self.node_id}:{key}:{timestamp}"
        return hashlib.sha3_256(content.encode()).hexdigest()

    def get_status(self) -> Dict:
        return {
            "node_id": self.node_id,
            "merkle_root": self.merkle_root,
            "active_iocs_count": len(self.active_iocs),
            "log_size": len(self.sync_log),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# ============================================================
# SIMULAÇÃO DE SINCRONIZAÇÃO DISTRIBUÍDA
# ============================================================
if __name__ == "__main__":
    print("\n=== SIMULAÇÃO: PROTOCOLO PCI-IOC (Substrato 43) ===")

    # Inicializa dois nós da malha
    node_sol = IOCMeshSync("NODE_SOL")
    node_proxima = IOCMeshSync("NODE_PROXIMA")

    print(f"\n[1] Estado Inicial:")
    print(f"  SOL: {node_sol.merkle_root[:16]}... ({len(node_sol.active_iocs)} IOCs)")
    print(f"  PROXIMA: {node_proxima.merkle_root[:16]}... ({len(node_proxima.active_iocs)} IOCs)")

    # Nó SOL detecta um novo Ghost Operator
    print(f"\n[2] Nó SOL detecta ameaça e adiciona IOC...")
    update1 = node_sol.add_ioc("GT", "467647531812", confidence=0.95)
    print(f"  Root SOL: {node_sol.merkle_root[:16]}...")

    # Nó PROXIMA detecta outro
    print(f"\n[3] Nó PROXIMA detecta outra ameaça...")
    update2 = node_proxima.add_ioc("GT", "855183901014", confidence=0.9)
    print(f"  Root PROXIMA: {node_proxima.merkle_root[:16]}...")

    # Sincronização Gossip
    print(f"\n[4] Iniciando Sincronização Gossip (Divergência detectada)...")

    # PROXIMA envia seu root para SOL
    updates_for_sol = node_proxima.gossip_sync(node_sol.merkle_root, node_sol.node_id)
    # SOL envia seu root para PROXIMA
    updates_for_proxima = node_sol.gossip_sync(node_proxima.merkle_root, node_proxima.node_id)

    # Aplicando deltas
    applied_sol = node_sol.receive_updates(updates_for_sol)
    applied_proxima = node_proxima.receive_updates(updates_for_proxima)

    print(f"  SOL recebeu {applied_sol} atualizações.")
    print(f"  PROXIMA recebeu {applied_proxima} atualizações.")

    print(f"\n[5] Estado Final:")
    print(f"  SOL: {node_sol.merkle_root[:16]}... ({len(node_sol.active_iocs)} IOCs)")
    print(f"  PROXIMA: {node_proxima.merkle_root[:16]}... ({len(node_proxima.active_iocs)} IOCs)")

    if node_sol.merkle_root == node_proxima.merkle_root:
        print("\n✅ CONSENSO ALCANÇADO: A malha está em sincronia invariante.")
    else:
        print("\n❌ ERRO: Divergência de estado persistente.")

    # Detalhes do consenso
    print("\nIOCs Ativos na Malha:")
    for key, data in node_sol.active_iocs.items():
        print(f"  - {key} (Origem: {data['origin']})")
