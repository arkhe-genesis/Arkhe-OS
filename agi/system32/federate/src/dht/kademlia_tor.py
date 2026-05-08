"""
kademlia_tor.py — Implementação de Kademlia sobre sockets SOCKS5 (Tor).
Cada nó é identificado pelo hash do seu endereço .onion.
"""
import asyncio
import hashlib
import random
import struct
import socket
import socks  # PySocks
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Peer:
    node_id: str       # hash
    onion: str         # endereço .onion
    last_seen: float
    coherence: float = 0.0

class TorKademliaNode:
    K = 20               # tamanho do bucket
    ALPHA = 3            # paralelismo

    def __init__(self, node_id: str, port: int, bootstrap_nodes: List[str]):
        self.node_id = hashlib.sha256(node_id.encode()).hexdigest()[:20]
        self.port = port
        self.buckets = [list() for _ in range(160)]  # K buckets
        self.peers: Dict[str, Peer] = {}
        self._server = None

    async def listen(self):
        """Inicia escuta na porta local (acessível apenas via localhost, mapeada pelo Tor)."""
        self._server = await asyncio.start_server(
            self._handle_connection, '127.0.0.1', self.port)

    async def _handle_connection(self, reader, writer):
        # Processa pedidos RPC: PING, STORE, FIND_NODE, FIND_VALUE
        pass

    async def bootstrap(self) -> bool:
        """Tenta juntar‑se à rede contactando os nós de bootstrap."""
        for addr in self.bootstrap_nodes:
            if await self._ping(addr):
                # consultar vizinhança e preencher buckets
                await self._lookup(self.node_id)
                return True
        return False

    async def _rpc(self, onion: str, method: str, params: dict) -> Optional[dict]:
        """Executa uma chamada RPC sobre Tor."""
        try:
            # Configurar proxy SOCKS5 para o endereço .onion
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            sock.connect((onion, self.port))
            # enviar request e ler resposta (simplificado)
            return {"status": "ok"}
        except Exception:
            return None

    async def add_peer(self, onion: str):
        self.bootstrap_nodes.append(onion)

    async def store(self, key: str, value: dict):
        """Armazena valor nos k nós mais próximos da chave."""
        closest = self._closest_nodes(key, self.K)
        for peer in closest:
            await self._rpc(peer.onion, "store", {"key": key, "value": value})

    def _closest_nodes(self, key: str, k: int) -> List[Peer]:
        # ordena pelo XOR da distância
        sorted_peers = sorted(self.peers.values(),
                              key=lambda p: self._distance(key, p.node_id))
        return sorted_peers[:k]

    @staticmethod
    def _distance(a: str, b: str) -> int:
        return int(a, 16) ^ int(b, 16)

    async def stop(self):
        if self._server:
            self._server.close()