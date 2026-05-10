# arkhe_network/wheeler_mesh.py
import hashlib
import asyncio
import time
from typing import Dict, List
from arkhe_network.rtd_mesh_sync import RTDMeshHandshake, ArkheNodeProfile
from arkhe_network.cosmic_merkle import CosmicMerkleTree

class WheelerMeshNetwork:
    """Rede P2P de Nós Arkhe com sincronização RTD"""

    def __init__(self, local_node: ArkheNodeProfile):
        self.local = local_node
        self.peers: Dict[str, ArkheNodeProfile] = {}
        self.handshake_protocol = RTDMeshHandshake()
        self.sagnac_cache: Dict[str, float] = {}

    async def join_network(self, bootstrap_nodes: List[ArkheNodeProfile]):
        """Entrada na malha com bootstrap relativístico"""
        for peer in bootstrap_nodes:
            self.peers[peer.node_id] = peer
            success = await self.handshake_protocol.perform_handshake(self.local, peer)
            if success:
                vector = self.handshake_protocol.compute_pairwise_sagnac(self.local, peer)
                self.sagnac_cache[peer.node_id] = vector.delta_t_ns

    async def execute_global_emission_slice(self, local_signal_merkle: str) -> str:
        """Executa uma fatia de emissão global"""
        simulated_peer_states = [
            (self.local.node_id, local_signal_merkle, self._get_current_tdb()),
        ]

        for peer_id, peer_profile in self.peers.items():
            fake_peer_root = hashlib.sha256(f"SIGNAL_{peer_id}".encode()).hexdigest()
            simulated_peer_states.append((peer_id, fake_peer_root, self._get_current_tdb()))

        global_root = CosmicMerkleTree.compute_global_root(simulated_peer_states)
        return global_root

    def _get_current_tdb(self) -> float:
        return time.time()
