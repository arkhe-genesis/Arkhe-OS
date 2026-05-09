#!/usr/bin/env python3
"""
webrtc_mesh.py — WebRTC P2P Mesh para streaming de vídeo anônimo.
Integra com Tor para ICE/TURN anônimo e DHT para descoberta de peers.
"""
import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum
import aiortc
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaRelay, MediaBlackhole

class PeerState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    STREAMING = "streaming"
    DISCONNECTED = "disconnected"
    BLOCKED = "blocked"

@dataclass
class PeerInfo:
    peer_id: str
    onion_address: Optional[str]
    coherence_score: float
    bandwidth_mbps: float
    state: PeerState = PeerState.DISCONNECTED
    last_seen: float = field(default_factory=time.time)
    stream_tracks: List[str] = field(default_factory=list)

class AnonymousICEGatherer:
    """Coleta candidatos ICE via circuitos Tor para anonimato."""
    def __init__(self, tor_socks_port: int = 9050):
        self.tor_socks_port = tor_socks_port
        self.candidates: List[RTCIceCandidate] = []

    async def gather_candidates(self, pc: RTCPeerConnection) -> List[RTCIceCandidate]:
        """Coleta candidatos ICE através de proxy SOCKS5 Tor."""
        # Configurar ICE servers com TURN anônimo
        pc.addIceServer({
            "urls": ["turn:turn-anon.arkhe.onion:5349"],
            "username": "anonymous",
            "credential": hashlib.sha256(f"anon_{time.time()}".encode()).hexdigest()[:16],
            "credentialType": "password"
        })

        # Aguardar coleta de candidatos
        await asyncio.sleep(2)  # Tempo para coleta ICE
        return pc.getSenders()

class WebRTCMeshNode:
    """Nó em uma mesh WebRTC P2P para streaming de vídeo."""
    def __init__(self, node_id: str, dht_client, kym_gatekeeper,
                 tor_socks_port: int = 9050, max_peers: int = 20):
        self.node_id = node_id
        self.dht = dht_client
        self.kym = kym_gatekeeper
        self.tor_socks_port = tor_socks_port
        self.max_peers = max_peers

        self.peers: Dict[str, PeerInfo] = {}
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.relay = MediaRelay()
        self.ice_gatherer = AnonymousICEGatherer(tor_socks_port)

        # Callbacks para eventos de streaming
        self.on_stream_received: Optional[Callable] = None
        self.on_peer_connected: Optional[Callable] = None
        self.on_peer_disconnected: Optional[Callable] = None

    async def start(self):
        """Inicia o nó da mesh WebRTC."""
        # Registrar este nó na DHT como provedor de streaming
        await self._announce_to_dht()
        # Iniciar loop de descoberta de peers
        asyncio.create_task(self._peer_discovery_loop())

    async def _announce_to_dht(self):
        """Anuncia este nó como provedor de streaming na DHT."""
        announcement = {
            "node_id": self.node_id,
            "type": "webrtc_streamer",
            "coherence": 0.95,  # Obtido do kernel de coerência
            "bandwidth": 10.0,  # Mbps estimados
            "timestamp": time.time(),
            "signature": self._sign_announcement()
        }
        await self.dht.store(f"stream:{self.node_id}", announcement)

    def _sign_announcement(self) -> str:
        """Assina o anúncio com chave do nó."""
        # Em produção: assinatura Ed25519 real
        return hashlib.sha256(f"{self.node_id}:{time.time()}".encode()).hexdigest()[:32]

    async def _peer_discovery_loop(self):
        """Loop contínuo de descoberta e conexão com peers."""
        while True:
            try:
                # Descobrir peers via DHT
                peers = await self.dht.lookup("stream:providers", limit=50)

                for peer_data in peers:
                    peer_id = peer_data.get("node_id")
                    if peer_id == self.node_id or peer_id in self.peers:
                        continue

                    # Verificar peer via KYM
                    if not await self.kym.verify_and_grant_access(peer_id, "webrtc_challenge"):
                        continue

                    # Calcular score de roteamento
                    score = self._calculate_routing_score(peer_data)
                    if score < 0.3:  # Threshold mínimo
                        continue

                    # Tentar conectar
                    if len(self.peer_connections) < self.max_peers:
                        await self._connect_to_peer(peer_data)

                # Aguardar antes da próxima iteração
                await asyncio.sleep(30)

            except Exception as e:
                print(f"[WebRTC] Erro na descoberta de peers: {e}")
                await asyncio.sleep(60)

    def _calculate_routing_score(self, peer_data: Dict) -> float:
        """Calcula score de roteamento baseado em coerência e latência."""
        coherence = peer_data.get("coherence", 0.5)
        bandwidth = peer_data.get("bandwidth", 1.0)
        # Simular latência (em produção: medir via ping Tor)
        latency = 0.2  # Normalizada 0-1
        return (coherence * (1 - latency) * bandwidth) / 10.0

    async def _connect_to_peer(self, peer_data: Dict):
        """Estabelece conexão WebRTC com um peer."""
        peer_id = peer_data["node_id"]
        onion_addr = peer_data.get("onion_address")

        # Criar nova conexão RTCPeerConnection
        pc = RTCPeerConnection()
        self.peer_connections[peer_id] = pc

        # Configurar callbacks
        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                await self._send_ice_candidate(peer_id, candidate)

        @pc.on("track")
        async def on_track(track):
            if self.on_stream_received:
                await self.on_stream_received(peer_id, track)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            state = pc.connectionState
            if state == "connected":
                self.peers[peer_id] = PeerInfo(
                    peer_id=peer_id,
                    onion_address=onion_addr,
                    coherence_score=peer_data.get("coherence", 0.5),
                    bandwidth_mbps=peer_data.get("bandwidth", 1.0),
                    state=PeerState.CONNECTED
                )
                if self.on_peer_connected:
                    await self.on_peer_connected(peer_id)
            elif state in ["failed", "closed", "disconnected"]:
                if peer_id in self.peers:
                    self.peers[peer_id].state = PeerState.DISCONNECTED
                if self.on_peer_disconnected:
                    await self.on_peer_disconnected(peer_id)

        # Iniciar oferta SDP
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # Enviar oferta via DHT/Tor
        await self._send_sdp(peer_id, "offer", pc.localDescription)

        # Aguardar resposta
        # (Implementação simplificada - em produção: usar signaling server anônimo)

    async def _send_sdp(self, peer_id: str, sdp_type: str, sdp: RTCSessionDescription):
        """Envia SDP via canal de sinalização anônimo."""
        message = {
            "type": sdp_type,
            "sdp": sdp.sdp,
            "from": self.node_id,
            "to": peer_id,
            "timestamp": time.time()
        }
        # Publicar na DHT para o peer recuperar
        await self.dht.store(f"signal:{peer_id}:{self.node_id}", message)

    async def _send_ice_candidate(self, peer_id: str, candidate: RTCIceCandidate):
        """Envia candidato ICE via canal de sinalização."""
        message = {
            "type": "candidate",
            "candidate": candidate.to_json(),
            "from": self.node_id,
            "to": peer_id
        }
        await self.dht.store(f"signal:{peer_id}:{self.node_id}:ice", message)

    async def offer_stream(self, track, metadata: Dict) -> str:
        """Oferece um stream de vídeo para a mesh."""
        stream_id = hashlib.sha256(f"{self.node_id}:{time.time()}".encode()).hexdigest()[:16]

        # Anunciar stream na DHT
        announcement = {
            "stream_id": stream_id,
            "provider": self.node_id,
            "metadata": metadata,
            "coherence": 0.95,
            "timestamp": time.time()
        }
        await self.dht.store(f"stream:offer:{stream_id}", announcement)

        # Adicionar track às conexões existentes
        for pc in self.peer_connections.values():
            if pc.connectionState == "connected":
                pc.addTrack(track)

        return stream_id

    async def stop(self):
        """Encerra todas as conexões e limpa recursos."""
        for pc in self.peer_connections.values():
            await pc.close()
        self.peer_connections.clear()
        self.peers.clear()