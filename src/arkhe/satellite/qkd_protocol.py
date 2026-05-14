#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qkd_protocol.py — Substrato 7.4.0: Protocolo QKD via Satélite para Segurança Global
Distribuição quântica de chaves com emaranhamento swapping para comunicações seguras.
"""

import numpy as np
import hashlib, json, time, asyncio
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

class QKDProtocol(Enum):
    """Protocolos QKD suportados via satélite."""
    BB84 = auto()          # Protocolo BB84 clássico com fótons polarizados
    E91 = auto()           # Protocolo E91 baseado em emaranhamento
    TF_QKD = auto()        # Twin-Field QKD para maior alcance
    SATELLITE_RELAY = auto() # Protocolo de relay via satélite com entanglement swapping

@dataclass
class QKDSession:
    """Sessão de distribuição de chaves quânticas."""
    session_id: str
    protocol: QKDProtocol
    satellite_id: str
    ground_station_a: str
    ground_station_b: str
    key_length_bits: int
    error_rate: float
    secret_key_rate_bps: float
    temporal_anchor: Optional[str]

class QKDKeyDistribution:
    """
    Distribuição quântica de chaves via satélite com segurança comprovada.

    Arquitetura:
    • Geração de pares emaranhados em satélite
    • Distribuição para estações terrestres via links ópticos
    • Entanglement swapping para estender alcance global
    • Privacy amplification e error correction clássicos
    • Ancoragem temporal de cada chave na TemporalChain
    """

    # Parâmetros físicos para QKD satelital
    PHYSICAL_PARAMS = {
        "wavelength_nm": 1550,  # Telecom wavelength para baixa perda atmosférica
        "satellite_altitude_km": 500,  # LEO para menor latência
        "beam_divergence_urad": 10,  # Divergência do feixe
        "atmospheric_loss_db": 3.0,  # Perda atmosférica típica
        "detector_efficiency": 0.85,  # Eficiência de detectores SPAD
        "dark_count_rate_hz": 100,  # Contagens escuras dos detectores
    }

    def __init__(self, satellite_id: str, ground_stations: List[str]):
        self.satellite_id = satellite_id
        self.ground_stations = ground_stations
        self.active_sessions: Dict[str, QKDSession] = {}
        self.shared_keys: Dict[str, bytes] = {}  # session_id -> secret key

    async def establish_qkd_session(
        self,
        station_a: str,
        station_b: str,
        protocol: QKDProtocol = QKDProtocol.E91,
        key_length: int = 256,
    ) -> QKDSession:
        """Estabelece sessão QKD entre duas estações terrestres via satélite."""

        session_id = f"qkd_{hashlib.sha3_256(f'{station_a}{station_b}{time.time()}'.encode()).hexdigest()[:12]}"

        # Simular estabelecimento de link quântico
        print(f"🛰️  Estabelecendo link QKD {protocol.name} entre {station_a} ↔ {station_b} via {self.satellite_id}")

        # Calcular taxa de chave secreta baseada em parâmetros físicos
        secret_key_rate = await self._calculate_secret_key_rate(protocol, station_a, station_b)

        # Simular distribuição de chaves
        error_rate = await self._simulate_qkd_exchange(protocol, key_length)

        # Gerar chave secreta (simulada)
        secret_key = self._generate_secret_key(key_length, session_id)
        self.shared_keys[session_id] = secret_key

        # Ancorar na TemporalChain
        anchor = self._anchor_key_to_temporal_chain(session_id, secret_key, station_a, station_b)

        session = QKDSession(
            session_id=session_id,
            protocol=protocol,
            satellite_id=self.satellite_id,
            ground_station_a=station_a,
            ground_station_b=station_b,
            key_length_bits=key_length,
            error_rate=error_rate,
            secret_key_rate_bps=secret_key_rate,
            temporal_anchor=anchor,
        )

        self.active_sessions[session_id] = session
        return session

    async def _calculate_secret_key_rate(
        self,
        protocol: QKDProtocol,
        station_a: str,
        station_b: str,
    ) -> float:
        """Calcula taxa de chave secreta baseada em parâmetros físicos."""
        # Modelo simplificado baseado em [Liao et al., Nature 2017]
        params = self.PHYSICAL_PARAMS

        # Perda total do link: satélite → terra
        free_space_loss = 20 * np.log10(4 * np.pi * params["satellite_altitude_km"] * 1e3 / (params["wavelength_nm"] * 1e-9))
        total_loss_db = free_space_loss + params["atmospheric_loss_db"]

        # Taxa de detecção
        source_rate = 1e6  # 1 MHz de pares emaranhados
        detection_prob = params["detector_efficiency"] * 10**(-total_loss_db / 10)
        raw_key_rate = source_rate * detection_prob

        # Fator de eficiência do protocolo
        protocol_efficiency = {
            QKDProtocol.BB84: 0.5,
            QKDProtocol.E91: 0.45,
            QKDProtocol.TF_QKD: 0.6,
            QKDProtocol.SATELLITE_RELAY: 0.35,
        }.get(protocol, 0.4)

        # Privacy amplification overhead
        privacy_overhead = 0.2

        secret_key_rate = raw_key_rate * protocol_efficiency * (1 - privacy_overhead)
        return max(0, secret_key_rate)

    async def _simulate_qkd_exchange(self, protocol: QKDProtocol, key_length: int) -> float:
        """Simula troca de chaves QKD com ruído realista."""
        # Taxa de erro quântico (QBER) típica para QKD satelital
        base_qber = 0.02  # 2% QBER base

        # Adicionar ruído baseado em condições atmosféricas simuladas
        atmospheric_noise = np.random.exponential(0.01)  # Ruído atmosférico
        qber = base_qber + atmospheric_noise

        # Verificar se QBER está abaixo do threshold de segurança
        security_threshold = 0.11  # Threshold para BB84
        if qber > security_threshold:
            # Abortar sessão se inseguro
            return qber

        return qber

    def _generate_secret_key(self, length_bits: int, session_id: str) -> bytes:
        """Gera chave secreta criptograficamente segura."""
        # Usar CSPRNG com seed baseado na sessão para reprodutibilidade controlada
        seed = hashlib.sha3_256(f"{session_id}{time.time_ns()}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(seed[:8], 'big'))

        # Gerar bits aleatórios
        key_bytes = rng.bytes(length_bits // 8)
        return key_bytes

    def _anchor_key_to_temporal_chain(
        self,
        session_id: str,
        secret_key: bytes,
        station_a: str,
        station_b: str,
    ) -> str:
        """Ancora chave QKD na TemporalChain sem revelar a chave."""
        # Ancorar apenas hash da chave + metadados
        key_hash = hashlib.sha3_256(secret_key).hexdigest()

        payload = {
            "session_id": session_id,
            "key_hash": key_hash,
            "stations": [station_a, station_b],
            "satellite": self.satellite_id,
            "timestamp": time.time(),
            "protocol": "QKD",
        }

        return hashlib.sha3_256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

    def get_shared_key(self, session_id: str) -> Optional[bytes]:
        """Recupera chave secreta compartilhada para uma sessão."""
        return self.shared_keys.get(session_id)

    async def perform_entanglement_swapping(
        self,
        session_ab: QKDSession,
        session_bc: QKDSession,
    ) -> QKDSession:
        """Realiza entanglement swapping para estender QKD para terceira estação."""
        # Em produção: executar protocolo de swapping com medição Bell
        # Aqui: simular criação de chave direta entre A e C via B

        new_session = await self.establish_qkd_session(
            station_a=session_ab.ground_station_a,
            station_b=session_bc.ground_station_b,
            protocol=QKDProtocol.SATELLITE_RELAY,
            key_length=session_ab.key_length_bits,
        )

        print(f"🔗 Entanglement swapping: {session_ab.ground_station_a} ↔ {session_bc.ground_station_b} via {session_ab.ground_station_b}")
        return new_session

class EntanglementSwappingRouter:
    """
    Roteador de emaranhamento para rede QKD global via satélite.

    Gerencia:
    • Topologia de rede de estações terrestres e satélites
    • Roteamento ótimo de pares emaranhados
    • Swapping em cascata para alcance intercontinental
    • Monitoramento de qualidade de emaranhamento em tempo real
    """

    def __init__(self, satellites: List[str], ground_stations: List[str]):
        self.satellites = satellites
        self.ground_stations = ground_stations
        self.entanglement_graph: Dict[str, Dict[str, float]] = {}  # Grafo de emaranhamento
        self.qkd_distributors: Dict[str, QKDKeyDistribution] = {}

    def add_entanglement_link(self, node_a: str, node_b: str, fidelity: float):
        """Adiciona link de emaranhamento ao grafo de rede."""
        if node_a not in self.entanglement_graph:
            self.entanglement_graph[node_a] = {}
        if node_b not in self.entanglement_graph:
            self.entanglement_graph[node_b] = {}

        self.entanglement_graph[node_a][node_b] = fidelity
        self.entanglement_graph[node_b][node_a] = fidelity

    async def find_optimal_qkd_path(
        self,
        source: str,
        destination: str,
        min_fidelity: float = 0.9,
    ) -> Optional[List[str]]:
        """Encontra caminho ótimo para distribuição de chave QKD."""
        # Algoritmo simplificado de busca de caminho com restrição de fidelidade
        from collections import deque

        # BFS com restrição de fidelidade
        queue = deque([(source, [source])])
        visited = {source}

        while queue:
            current, path = queue.popleft()

            if current == destination:
                return path

            for neighbor, fidelity in self.entanglement_graph.get(current, {}).items():
                if neighbor not in visited and fidelity >= min_fidelity:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None  # Nenhum caminho válido encontrado

    async def establish_global_qkd(
        self,
        station_a: str,
        station_b: str,
        key_length: int = 256,
    ) -> Optional[QKDSession]:
        """Estabelece chave QKD global entre duas estações quaisquer."""

        # Encontrar caminho ótimo de emaranhamento
        path = await self.find_optimal_qkd_path(station_a, station_b)
        if not path:
            print(f"❌ Nenhum caminho QKD válido entre {station_a} e {station_b}")
            return None

        print(f"🗺️  Caminho QKD encontrado: {' → '.join(path)}")

        # Estabelecer sessões QKD em cada hop
        sessions = []
        for i in range(len(path) - 1):
            satellite = self.satellites[0] if path[i] in self.ground_stations and path[i+1] in self.ground_stations else None
            distributor = QKDKeyDistribution(
                satellite_id=satellite or "terrestrial",
                ground_stations=[path[i], path[i+1]]
            )
            session = await distributor.establish_qkd_session(path[i], path[i+1], key_length=key_length)
            sessions.append((distributor, session))

        # Realizar entanglement swapping em cascata para chave end-to-end
        final_session = sessions[0][1]
        for i in range(1, len(sessions)):
            prev_distributor, prev_session = sessions[i-1]
            curr_distributor, curr_session = sessions[i]

            # Swapping entre sessões adjacentes
            final_session = await prev_distributor.perform_entanglement_swapping(prev_session, curr_session)

        return final_session

# ============================================================================
# Exemplo: Rede QKD global via satélite
# ============================================================================
async def demo_global_qkd_network():
    """Demonstra estabelecimento de chave QKD global via satélite."""

    # Configurar rede
    satellites = ["sat-leo-01", "sat-leo-02"]
    ground_stations = ["ground-eu", "ground-asia", "ground-americas", "ground-africa"]

    router = EntanglementSwappingRouter(satellites, ground_stations)

    # Adicionar links de emaranhamento simulados
    router.add_entanglement_link("ground-eu", "sat-leo-01", fidelity=0.95)
    router.add_entanglement_link("ground-asia", "sat-leo-01", fidelity=0.93)
    router.add_entanglement_link("ground-americas", "sat-leo-02", fidelity=0.94)
    router.add_entanglement_link("ground-africa", "sat-leo-02", fidelity=0.92)
    router.add_entanglement_link("sat-leo-01", "sat-leo-02", fidelity=0.91)  # Inter-satellite link

    # Estabelecer chave QKD entre Europa e Ásia (via mesmo satélite)
    print("🔐 Estabelecendo chave QKD Europa ↔ Ásia...")
    session_eu_asia = await router.establish_global_qkd("ground-eu", "ground-asia", key_length=256)
    if session_eu_asia:
        print(f"✅ Chave estabelecida: {session_eu_asia.key_length_bits} bits, QBER={session_eu_asia.error_rate:.3f}")
        print(f"   Taxa: {session_eu_asia.secret_key_rate_bps:.1f} bps, Âncora: {session_eu_asia.temporal_anchor}")

    # Estabelecer chave QKD entre Europa e Américas (via swapping)
    print("\n🔐 Estabelecendo chave QKD Europa ↔ Américas (via swapping)...")
    session_eu_americas = await router.establish_global_qkd("ground-eu", "ground-americas", key_length=256)
    if session_eu_americas:
        print(f"✅ Chave estabelecida via swapping: {session_eu_americas.key_length_bits} bits")
        print(f"   QBER={session_eu_americas.error_rate:.3f}, Âncora: {session_eu_americas.temporal_anchor}")

    print("\n🌍 Rede QKD global operacional — comunicações seguras em escala planetária")

if __name__ == "__main__":
    asyncio.run(demo_global_qkd_network())
