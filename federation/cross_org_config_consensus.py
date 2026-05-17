#!/usr/bin/env python3
"""
ARKHE OS Substrato ∞: Cross‑Org Config Consensus Integration
Canon: ∞.Ω.∇+++.federation.cross_org_config_consensus
Função: Integrar ConfigFederationService com CrossOrgConsensusValidator,
exigindo consenso Φ_C para validação de configurações federadas.
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import logging

# Assuming these are imported from their respective modules in a real system
# We define stubs here so the script can parse. In actual deployment, these
# should be imported from the relevant locations.
class ConfigVisibility(Enum):
    PRIVATE = "private"
    FEDERATED = "federated"
    GLOBAL = "global"

class ConsensusDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass
class FederatedConfig:
    config_id: str
    content: dict
    visibility: ConfigVisibility
    allowed_organizations: Set[str]
    phi_c_score: float
    updated_at: float

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrossOrgConfigConsensus:
    """
    Camada de consenso para configurações federadas.
    """

    def __init__(
        self,
        config_service,          # ConfigFederationService instance
        consensus_validator,     # CrossOrgConsensusValidator instance
        temporal_chain=None,
        phi_bus=None,
        hsm_signer=None
    ):
        self.config_service = config_service
        self.consensus_validator = consensus_validator
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.hsm = hsm_signer

    async def propose_config_for_consensus(
        self,
        config_content: Dict,
        proposing_org: str,
        allowed_orgs: Set[str],
        required_quorum: float = 2/3
    ) -> Dict:
        """
        Propõe uma nova configuração federada que requer consenso cross‑org.
        Pipeline:
        1. Criar a configuração no ConfigFederationService (privada por enquanto)
        2. Registrar a proposta no CrossOrgConsensusValidator
        3. Aguardar votos das organizações participantes
        4. Se consenso atingido, tornar a configuração FEDERATED
        5. Se rejeitado, arquivar a configuração como rejeitada
        """
        # 1. Criar config privada inicialmente
        config = self.config_service.create_federated_config(
            config_content=config_content,
            visibility=ConfigVisibility.PRIVATE,
            allowed_orgs=set()
        )

        # 2. Registrar proposta no validador de consenso
        self.consensus_validator.participating_orgs = allowed_orgs | {proposing_org}

        # 3. Simular votação (em produção, aguardar votos reais)
        await self._collect_votes_and_decide(config, proposing_org, required_quorum)

        return {
            "config_id": config.config_id,
            "status": "consensus_process_started"
        }

    async def _collect_votes_and_decide(
        self,
        config: FederatedConfig,
        proposing_org: str,
        required_quorum: float
    ):
        """
        Coleta votos das organizações (mock: simula votação unânime).
        Em produção, escutar eventos de voto ou orquestrar via protocolo de consenso.
        """
        # Mock: todas as organizações aprovam após um delay
        await asyncio.sleep(2)

        # Registrar votos simulados
        for org in self.consensus_validator.participating_orgs:
            if org != proposing_org:
                await self.consensus_validator.submit_vote(
                    config_id=config.config_id,
                    proposing_org=proposing_org,
                    vote=True,
                    phi_c_at_vote=config.phi_c_score,
                    justification="Config validada pelos critérios canônicos"
                )

        # Obter resultado do consenso
        result = self.consensus_validator._validation_history[-1] if self.consensus_validator._validation_history else None

        if result and result.decision == ConsensusDecision.APPROVED:
            # Tornar a config FEDERATED e adicionar organizações permitidas
            config.visibility = ConfigVisibility.FEDERATED
            config.allowed_organizations = self.consensus_validator.participating_orgs.copy()
            config.updated_at = time.time()
            # Ancorar aprovação na TemporalChain
            if self.temporal:
                await self.temporal.anchor_event("cross_org_config_approved", {
                    "config_id": config.config_id,
                    "proposing_org": proposing_org,
                    "approved_by": len(self.consensus_validator.participating_orgs),
                    "timestamp": time.time()
                })
            logger.info(f"✅ Config {config.config_id} aprovada via consenso cross‑org")
        else:
            logger.warning(f"⛔ Config {config.config_id} rejeitada ou sem quórum")
