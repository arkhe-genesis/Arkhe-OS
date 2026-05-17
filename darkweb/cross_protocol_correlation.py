#!/usr/bin/env python3
"""
ARKHE OS Substrato 233: Cross‑Protocol Correlation Engine
Detecta campanhas de ameaça distribuídas em múltiplas redes anônimas,
aplicando privacidade diferencial (ε) para proteger indicadores sensíveis.
"""
import asyncio, hashlib, json, time, numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
import logging
from .multi_protocol_adapter import DarknetProtocol

logger = logging.getLogger(__name__)

@dataclass
class ThreatCampaign:
    campaign_id: str
    protocols: Set[DarknetProtocol]
    correlated_hashes: List[str]   # hashes truncados
    common_patterns: Dict[str, float]
    severity: str
    confidence: float
    temporal_seal: Optional[str] = None

class CrossProtocolCorrelationEngine:
    """
    Correlaciona achados de diferentes redes anônimas para identificar campanhas.
    Utiliza privacidade diferencial: os hashes completos nunca são compartilhados;
    apenas agregações com ruído Laplace.
    """

    def __init__(self, unified_db, delta_mem, temporal, dp_epsilon: float = 2.0):
        self.db = unified_db
        self.delta = delta_mem
        self.temporal = temporal
        self.epsilon = dp_epsilon
        self._campaigns: List[ThreatCampaign] = []
        # Ensure repeatable randomness in tests
        self.rng = np.random.default_rng()

    def _add_laplace_noise(self, value: float) -> float:
        scale = 1.0 / self.epsilon
        return value + self.rng.laplace(0, scale)

    async def correlate(self, new_findings: List[dict]) -> List[ThreatCampaign]:
        """
        Recebe novos achados (de qualquer protocolo) e verifica se formam
        uma campanha com achados existentes na base unificada.
        """
        # 1. Extrair hashes (truncados) dos novos achados
        new_hashes = {f["indicator_hash"][:16] for f in new_findings}
        protocols_affected = {f["protocol"] for f in new_findings}

        # 2. Buscar na base unificada por hashes similares (consulta perceptual)
        correlated_entries = []
        for h in new_hashes:
            entries = self.db.query_by_perceptual_hash(h)
            correlated_entries.extend(entries)

        # 3. Agregar padrões com ruído Laplace
        patterns = {}
        for entry in correlated_entries:
            patterns[entry.entry_type] = self._add_laplace_noise(
                patterns.get(entry.entry_type, 0) + 1
            )

        # 4. Determinar se é uma campanha (múltiplos protocolos e hashes correlacionados)
        if len(protocols_affected) >= 2 and len(correlated_entries) >= 3:
            campaign = ThreatCampaign(
                campaign_id=hashlib.sha3_256(f"{new_hashes}{time.time()}".encode()).hexdigest()[:12],
                protocols=protocols_affected,
                correlated_hashes=list(new_hashes)[:5],  # truncados
                common_patterns=patterns,
                severity="high" if len(protocols_affected) >= 3 else "medium",
                confidence=min(1.0, len(correlated_entries) / 10)
            )
            # Ancorar na TemporalChain
            if self.temporal:
                campaign.temporal_seal = await self.temporal.anchor_event(
                    "cross_protocol_campaign_detected",
                    {
                        "campaign_id": campaign.campaign_id,
                        "protocols": [p.value for p in campaign.protocols],
                        "hashes_count": len(campaign.correlated_hashes),
                        "severity": campaign.severity,
                        "timestamp": time.time()
                    }
                )
            self._campaigns.append(campaign)
            logger.warning(f"🚨 Campanha cross‑protocol detectada: {campaign.campaign_id}")
            return [campaign]
        return []
