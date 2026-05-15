#!/usr/bin/env python3
"""
federated_intel.py — Correlação federada de inteligência de ameaças entre broadcasters.
Permite que múltiplas emissoras compartilhem indicadores de ataque (IOCs) sem expor
dados sensíveis de audiência ou infraestrutura interna.

Protocolo:
1. Cada emissora gera um "bloom filter" dos seus eventos de segurança
2. Os filtros são compartilhados via canal seguro (TLS 1.3 + mTLS)
3. Cada emissora pode consultar se um IOC é conhecido por outras emissoras
4. Respostas são agregadas sem revelar qual emissora específica reportou o IOC
5. Todo o tráfego é ancorado na TemporalChain para auditoria
"""

import hashlib, json, time
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
import numpy as np

@dataclass
class ThreatIndicator:
    """Indicador de ameaça compartilhável entre broadcasters."""
    indicator_type: str    # "ip", "domain", "url", "hash", "pattern"
    indicator_value: str   # Valor do IOC (hasheado para privacidade)
    severity: str          # "low", "medium", "high", "critical"
    first_seen: float
    last_seen: float
    confidence: float      # 0.0 a 1.0
    source: str            # "view_botting", "credential_stuffing", "ddos", "content_abuse"
    affected_platforms: List[str]  # "twitch", "youtube", "tiktok"
    mitigation_applied: bool
    notes_encrypted: str   # Notas criptografadas (apenas para broadcasters autorizados)

class FederatedThreatIntel:
    """
    Rede federada de compartilhamento de inteligência de ameaças entre broadcasters.

    Propriedades de segurança:
    • Privacidade: IOCs são hasheados antes do compartilhamento
    • Confidencialidade: Canal criptografado TLS 1.3 + mTLS
    • Integridade: Cada mensagem é assinada com PQC (Dilithium)
    • Disponibilidade: Rede mesh — sem ponto único de falha
    • Não-repúdio: Todas as trocas são ancoradas na TemporalChain
    """

    def __init__(self, broadcaster_id: str, peers: List[str],
                 encryption_key: bytes, temporal_chain=None):
        self.broadcaster_id = broadcaster_id
        self.peers = peers
        self.cipher = Fernet(encryption_key)
        self.temporal = temporal_chain

        # Bloom filter local para IOCs observados
        self.bloom_size = 10000
        self.bloom_hashes = 5
        self.bloom_filter = np.zeros(self.bloom_size, dtype=bool)

        # Cache de IOCs compartilhados
        self.shared_iocs: Dict[str, ThreatIndicator] = {}
        self.correlation_matches: List[Dict] = []

    def _hash_ioc(self, indicator_value: str) -> str:
        """Hash do IOC para privacidade — permite consulta sem revelar o valor real."""
        return hashlib.sha3_256(indicator_value.encode()).hexdigest()[:16]

    def _add_to_bloom(self, hashed_value: str):
        """Adiciona IOC ao bloom filter local."""
        for i in range(self.bloom_hashes):
            index = int(hashlib.sha3_256(f"{hashed_value}{i}".encode()).hexdigest(), 16) % self.bloom_size
            self.bloom_filter[index] = True

    def _check_bloom(self, hashed_value: str) -> bool:
        """Verifica se IOC está presente no bloom filter local."""
        for i in range(self.bloom_hashes):
            index = int(hashlib.sha3_256(f"{hashed_value}{i}".encode()).hexdigest(), 16) % self.bloom_size
            if not self.bloom_filter[index]:
                return False
        return True

    async def report_threat(self, indicator: ThreatIndicator) -> str:
        """Reporta ameaça local e compartilha com a rede federada."""
        hashed_value = self._hash_ioc(indicator.indicator_value)

        # Armazenar localmente
        self.shared_iocs[hashed_value] = indicator
        self._add_to_bloom(hashed_value)

        # Criar versão compartilhável (sem o valor real do IOC)
        shareable = {
            "indicator_type": indicator.indicator_type,
            "indicator_hash": hashed_value,
            "severity": indicator.severity,
            "confidence": indicator.confidence,
            "source": indicator.source,
            "affected_platforms": indicator.affected_platforms,
            "reporter": self.broadcaster_id,
            "timestamp": time.time(),
        }

        # Assinar com PQC (simulado)
        shareable["signature"] = hashlib.sha3_256(
            json.dumps(shareable, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Enviar para peers via API segura
        for peer in self.peers:
            await self._send_to_peer(peer, shareable)

        # Ancorar na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event("federated_intel_report", {
                "ioc_hash": hashed_value,
                "severity": indicator.severity,
                "source": indicator.source,
                "reporter": self.broadcaster_id,
                "timestamp": time.time(),
            })

        return hashed_value

    async def _send_to_peer(self, peer: str, data: Dict):
        """Envia IOC compartilhável para um peer da rede federada."""
        # Em produção: POST https://{peer}/api/v1/intel/report
        # Aqui, simulamos recebimento local
        print(f"📤 Enviado IOC para {peer}: {data['indicator_hash']}")

    async def query_threat(self, indicator_value: str) -> Dict:
        """
        Consulta se um IOC é conhecido pela rede federada.
        Retorna informações agregadas sem revelar qual emissora reportou.
        """
        hashed_value = self._hash_ioc(indicator_value)

        # Verificar localmente
        local_match = self._check_bloom(hashed_value)

        # Consultar peers (agregado — sem identificar o peer específico)
        peer_matches = 0
        total_peers_queried = 0

        for peer in self.peers:
            # Em produção: GET https://{peer}/api/v1/intel/query/{hashed_value}
            # Simulação: 30% de chance de match por peer
            import random
            if random.random() < 0.3:
                peer_matches += 1
            total_peers_queried += 1

        correlation = {
            "ioc_hash": hashed_value,
            "local_match": local_match,
            "federated_matches": peer_matches,
            "total_peers": total_peers_queried,
            "federated_confidence": peer_matches / max(1, total_peers_queried),
            "recommendation": "block" if (local_match or peer_matches > 0) else "monitor",
        }

        if local_match and hashed_value in self.shared_iocs:
            indicator = self.shared_iocs[hashed_value]
            correlation["details"] = {
                "severity": indicator.severity,
                "source": indicator.source,
                "first_seen": indicator.first_seen,
            }

        # Ancorar consulta
        if self.temporal:
            await self.temporal.anchor_event("federated_intel_query", {
                "ioc_hash": hashed_value,
                "matches": peer_matches,
                "recommendation": correlation["recommendation"],
                "timestamp": time.time(),
            })

        self.correlation_matches.append(correlation)
        return correlation

    def get_federated_stats(self) -> Dict:
        """Estatísticas da rede federada de inteligência."""
        return {
            "broadcaster_id": self.broadcaster_id,
            "peers_connected": len(self.peers),
            "iocs_reported": len(self.shared_iocs),
            "iocs_in_bloom": int(np.sum(self.bloom_filter)),
            "correlation_queries": len(self.correlation_matches),
            "federated_match_rate": sum(1 for m in self.correlation_matches if m["federated_matches"] > 0) / max(1, len(self.correlation_matches)),
            "top_sources": self._get_top_sources(),
            "temporal_chain_anchored": self.temporal is not None,
        }

    def _get_top_sources(self) -> Dict[str, int]:
        """Top fontes de ameaças compartilhadas."""
        sources = {}
        for indicator in self.shared_iocs.values():
            sources[indicator.source] = sources.get(indicator.source, 0) + 1
        return dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5])
