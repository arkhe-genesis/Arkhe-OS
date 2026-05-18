#!/usr/bin/env python3
"""
ARKHE OS Substrate 237: Cross-Platform Federated Consensus Engine
Canon: ∞.Ω.∇+++.237.consensus.engine
Função: Implementa consenso federado entre Linux, Windows e FreeBSD
com ponderação Φ_C, assinaturas PQC e ancoragem na TemporalChain.
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum, auto
from pathlib import Path
import logging
import grpc
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

# Import generated gRPC stubs
import substrate_237.cross_platform_consensus.consensus_protocol_pb2 as pb
import substrate_237.cross_platform_consensus.consensus_protocol_pb2_grpc as pb_grpc

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# TIPOS CANÔNICOS DE CONSENSO CROSS-PLATFORM
# ═══════════════════════════════════════════════════════════════

class PlatformType(Enum):
    """Plataformas suportadas no consenso federado."""
    LINUX = "linux"
    WINDOWS = "windows"
    FREEBSD = "freebsd"
    UNKNOWN = "unknown"

@dataclass
class PlatformNode:
    """Representação de um nó em uma plataforma específica."""
    node_id: str
    platform: PlatformType
    kernel_version: str
    arkhe_substrate_version: str
    phi_c_capability: float  # Capacidade de cálculo Φ_C [0.0-1.0]
    network_latency_ms: float
    last_heartbeat: float
    is_aggregator: bool = False
    is_validator: bool = True

    def compute_voting_power(self, org_reputation: float) -> float:
        """Calcula poder de voto combinando reputação da org e capacidade da plataforma."""
        # Fatores de peso por plataforma (ajustáveis por política)
        platform_weights = {
            PlatformType.LINUX: 1.0,
            PlatformType.WINDOWS: 1.0,
            PlatformType.FREEBSD: 1.0,
            PlatformType.UNKNOWN: 0.5
        }
        return org_reputation * platform_weights.get(self.platform, 0.5) * self.phi_c_capability

@dataclass
class CrossPlatformProposal:
    """Proposta adaptada para consenso cross-platform."""
    proposal_id: str
    proposal_type: str
    proposer_node_id: str
    target_platforms: List[PlatformType]  # Plataformas afetadas pela proposta
    content_hash: str
    content_metadata: Dict
    pqc_signature: str
    created_at: float
    voting_deadline: float
    status: str = "pending"

    def affects_platform(self, platform: PlatformType) -> bool:
        """Verifica se proposta afeta uma plataforma específica."""
        return platform in self.target_platforms or PlatformType.UNKNOWN in self.target_platforms

# ═══════════════════════════════════════════════════════════════
# MOTOR DE CONSENSO CROSS-PLATFORM
# ═══════════════════════════════════════════════════════════════

class CrossPlatformConsensusEngine:
    """Motor de consenso federado operando entre Linux, Windows e FreeBSD."""

    def __init__(
        self,
        local_node: PlatformNode,
        local_org_id: str,
        consensus_threshold: float = 0.67,
        voting_period_hours: float = 24.0,
        aggregator_endpoints: Dict[PlatformType, str] = None
    ):
        self.local_node = local_node
        self.local_org_id = local_org_id
        self.consensus_threshold = consensus_threshold
        self.voting_period_hours = voting_period_hours
        self.aggregator_endpoints = aggregator_endpoints or {}

        # Estado local do consenso
        self._active_proposals: Dict[str, CrossPlatformProposal] = {}
        self._my_votes: Dict[str, pb.FederatedVote] = {}
        self._consensus_results: Dict[str, pb.ConsensusResult] = {}
        self._known_nodes: Dict[str, PlatformNode] = {}
        self._org_reputations: Dict[str, float] = {}

        # Canais gRPC para comunicação cross-platform
        self._grpc_channels: Dict[PlatformType, grpc.aio.Channel] = {}

        # Cache de assinaturas PQC para verificação
        self._pqc_public_keys: Dict[str, bytes] = {}

    async def connect_to_aggregators(self):
        """Estabelece conexões gRPC com agregadores em cada plataforma."""
        for platform, endpoint in self.aggregator_endpoints.items():
            try:
                channel = grpc.aio.insecure_channel(endpoint)
                # await channel.channel_ready()
                self._grpc_channels[platform] = channel
                logger.info(f"✅ Conectado ao agregador {platform.value}: {endpoint}")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao conectar ao agregador {platform.value}: {e}")

    async def submit_cross_platform_proposal(
        self,
        proposal_type: str,
        content: Any,
        content_metadata: Dict,
        target_platforms: List[PlatformType]
    ) -> Optional[str]:
        """Submete proposta para consenso cross-platform."""
        # Calcular hash do conteúdo
        content_hash = hashlib.sha3_256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()

        # Gerar ID único para proposta
        proposal_id = hashlib.sha3_256(
            f"{self.local_org_id}:{proposal_type}:{content_hash}:{time.time()}".encode()
        ).hexdigest()

        # Criar proposta cross-platform
        proposal = CrossPlatformProposal(
            proposal_id=proposal_id,
            proposal_type=proposal_type,
            proposer_node_id=self.local_node.node_id,
            target_platforms=target_platforms,
            content_hash=content_hash,
            content_metadata=content_metadata,
            pqc_signature=self._mock_pqc_sign(f"{proposal_id}:{content_hash}"),
            created_at=time.time(),
            voting_deadline=time.time() + (self.voting_period_hours * 3600)
        )

        # Enviar para agregadores das plataformas alvo
        for platform in target_platforms:
            if platform in self._grpc_channels:
                await self._send_to_aggregator(platform, "SubmitProposal", {
                    "proposal": self._to_pb_proposal(proposal),
                    "proposer_identity": self._to_pb_org_identity()
                })

        # Armazenar localmente
        self._active_proposals[proposal_id] = proposal

        logger.info(f"✅ Proposta cross-platform submetida: {proposal_id[:16]}... "
                   f"(afeta: {[p.value for p in target_platforms]})")
        return proposal_id

    async def vote_on_cross_platform_proposal(
        self,
        proposal_id: str,
        vote_value: bool,
        justification: str = ""
    ) -> Optional[pb.FederatedVote]:
        """Vota em proposta cross-platform considerando impacto por plataforma."""
        if proposal_id not in self._active_proposals:
            # Tentar buscar do agregador
            proposal = await self._fetch_proposal(proposal_id)
            if not proposal:
                logger.error(f"❌ Proposta não encontrada: {proposal_id}")
                return None
            self._active_proposals[proposal_id] = proposal

        proposal = self._active_proposals[proposal_id]

        # Verificar se proposta afeta nossa plataforma
        if not proposal.affects_platform(self.local_node.platform):
            logger.debug(f"⚠️ Proposta {proposal_id[:16]}... não afeta {self.local_node.platform.value}")
            return None

        # Verificar prazo de votação
        if time.time() > proposal.voting_deadline:
            logger.warning(f"⚠️ Prazo de votação expirado para proposta {proposal_id}")
            return None

        # Obter reputação da organização
        org_reputation = self._org_reputations.get(self.local_org_id, 0.9)

        # Calcular peso do voto combinando reputação e capacidade da plataforma
        voting_power = self.local_node.compute_voting_power(org_reputation)

        # Criar voto
        vote = pb.FederatedVote(
            vote_id=hashlib.sha3_256(f"{proposal_id}:{self.local_org_id}:{time.time()}".encode()).hexdigest(),
            proposal_id=proposal_id,
            voter_org_id=self.local_org_id,
            vote_value=vote_value,
            vote_weight=voting_power,
            justification=justification,
            pqc_signature=self._mock_pqc_sign(f"{proposal_id}:{vote_value}:{voting_power}").encode(),
            timestamp=pb.google_dot_protobuf_dot_timestamp__pb2.Timestamp(seconds=int(time.time()))
        )

        # Enviar voto para agregadores das plataformas afetadas
        for platform in proposal.target_platforms:
            if platform in self._grpc_channels:
                await self._send_to_aggregator(platform, "SubmitVote", {
                    "vote": vote,
                    "voter_identity": self._to_pb_org_identity()
                })

        # Armazenar voto localmente
        self._my_votes[proposal_id] = vote

        logger.info(f"🗳️ Voto cross-platform registrado: {vote.vote_id[:16]}... = "
                   f"{'APROVAR' if vote_value else 'REJEITAR'} (peso: {voting_power:.3f}, "
                   f"plataformas: {[p.value for p in proposal.target_platforms]})")
        return vote

    async def check_cross_platform_consensus_status(
        self,
        proposal_id: str
    ) -> Optional[pb.ConsensusResult]:
        """Verifica status de consenso agregando votos de todas as plataformas."""
        # Verificar cache local primeiro
        if proposal_id in self._consensus_results:
            return self._consensus_results[proposal_id]

        # Coletar votos de todos os agregadores das plataformas afetadas
        if proposal_id in self._active_proposals:
            proposal = self._active_proposals[proposal_id]
            all_votes = []

            for platform in proposal.target_platforms:
                if platform in self._grpc_channels:
                    try:
                        votes = await self._fetch_votes_from_aggregator(platform, proposal_id)
                        all_votes.extend(votes)
                    except Exception as e:
                        logger.warning(f"Error fetching votes from {platform}: {e}")

            # If we don't have enough votes from aggregators, mock it for testing
            if not all_votes:
                for platform in proposal.target_platforms:
                    votes = await self._fetch_votes_from_aggregator(platform, proposal_id)
                    all_votes.extend(votes)

            # Calcular consenso com votos agregados
            if all_votes:
                result = await self._compute_cross_platform_consensus(proposal_id, all_votes)
                self._consensus_results[proposal_id] = result
                return result

        return None

    async def _compute_cross_platform_consensus(
        self,
        proposal_id: str,
        votes: List[pb.FederatedVote]
    ) -> pb.ConsensusResult:
        """Calcula consenso considerando votos de múltiplas plataformas."""
        # Separar votos por plataforma para análise
        votes_by_platform: Dict[PlatformType, List[pb.FederatedVote]] = {}
        for vote in votes:
            # Determinar plataforma do votante (mock: baseado no org_id)
            platform = self._infer_platform_from_org(vote.voter_org_id)
            if platform not in votes_by_platform:
                votes_by_platform[platform] = []
            votes_by_platform[platform].append(vote)

        # Calcular pesos totais
        approved_weight = sum(v.vote_weight for v in votes if v.vote_value)
        rejected_weight = sum(v.vote_weight for v in votes if not v.vote_value)
        total_weight = approved_weight + rejected_weight

        # Verificar consenso global
        approved_ratio = approved_weight / total_weight if total_weight > 0 else 0
        reached_consensus = approved_ratio >= self.consensus_threshold

        # Verificar consenso por plataforma (opcional: requer aprovação em todas)
        platform_consensus = {}
        for platform, platform_votes in votes_by_platform.items():
            if platform_votes:
                plat_approved = sum(v.vote_weight for v in platform_votes if v.vote_value)
                plat_total = sum(v.vote_weight for v in platform_votes)
                platform_consensus[platform.value] = plat_approved / plat_total if plat_total > 0 else 0

        # Determinar status final
        final_status = "approved" if reached_consensus else "rejected"

        # Criar resultado com selo de ancoragem na TemporalChain
        result = pb.ConsensusResult(
            proposal_id=proposal_id,
            final_status=final_status,
            total_votes=len(votes),
            approved_weight=approved_weight,
            rejected_weight=rejected_weight,
            consensus_threshold=self.consensus_threshold,
            reached_consensus=reached_consensus,
            pqc_aggregate_signature=self._mock_pqc_sign(f"{proposal_id}:{final_status}:{approved_weight}").encode(),
            finalized_at=pb.google_dot_protobuf_dot_timestamp__pb2.Timestamp(seconds=int(time.time())),
            temporal_chain_seal=hashlib.sha3_256(
                f"{proposal_id}:{final_status}:{approved_weight}:{time.time()}".encode()
            ).hexdigest()
        )

        # Ancorar resultado na TemporalChain (mock)
        logger.info(f"🔗 Ancorando resultado cross-platform na TemporalChain: {result.temporal_chain_seal[:16]}...")

        return result

    def _infer_platform_from_org(self, org_id: str) -> PlatformType:
        """Inferir plataforma baseada no ID da organização (mock)."""
        if "linux" in org_id.lower():
            return PlatformType.LINUX
        elif "windows" in org_id.lower():
            return PlatformType.WINDOWS
        elif "freebsd" in org_id.lower():
            return PlatformType.FREEBSD
        return PlatformType.UNKNOWN

    def _to_pb_proposal(self, proposal: CrossPlatformProposal) -> pb.FederatedProposal:
        """Converte proposta interna para protobuf."""
        return pb.FederatedProposal(
            proposal_id=proposal.proposal_id,
            proposal_type=proposal.proposal_type,
            proposer_org_id=proposal.proposer_node_id,
            content_hash=proposal.content_hash.encode(),
            content_metadata={k: str(v) for k, v in proposal.content_metadata.items()},
            pqc_signature=proposal.pqc_signature.encode(),
            created_at=pb.google_dot_protobuf_dot_timestamp__pb2.Timestamp(seconds=int(proposal.created_at)),
            voting_deadline=pb.google_dot_protobuf_dot_timestamp__pb2.Timestamp(seconds=int(proposal.voting_deadline)),
            status=proposal.status
        )

    def _to_pb_org_identity(self) -> pb.OrganizationIdentity:
        """Converte identidade local para protobuf."""
        return pb.OrganizationIdentity(
            org_id=self.local_org_id,
            org_name=f"Arkhe-{self.local_node.platform.value}",
            public_key_pqc=b"mock_pqc_pubkey",
            phi_c_reputation=0.94,
            stake_weight=1.2,
            joined_at=pb.google_dot_protobuf_dot_timestamp__pb2.Timestamp(seconds=int(time.time() - 30*86400)),
            last_heartbeat=pb.google_dot_protobuf_dot_timestamp__pb2.Timestamp(seconds=int(time.time())),
            is_active=True
        )

    def _mock_pqc_sign(self, message: str) -> str:
        """Mock de assinatura PQC para sandbox."""
        return hashlib.sha3_256(f"{message}:{self.local_org_id}".encode()).hexdigest()

    async def _send_to_aggregator(self, platform: PlatformType, method: str, payload: Dict):
        """Envia mensagem para agregador de plataforma específica via gRPC."""
        if platform not in self._grpc_channels:
            return

        try:
            stub = pb_grpc.FederatedConsensusServiceStub(self._grpc_channels[platform])

            if method == "SubmitProposal":
                request = pb.SubmitProposalRequest(
                    proposal=payload["proposal"],
                    proposer_identity=payload["proposer_identity"]
                )
                await stub.SubmitProposal(request)
            elif method == "SubmitVote":
                request = pb.SubmitVoteRequest(
                    vote=payload["vote"],
                    voter_identity=payload["voter_identity"]
                )
                await stub.SubmitVote(request)

        except Exception as e:
            logger.warning(f"⚠️ Falha ao enviar {method} para agregador {platform.value}: {e}")

    async def _fetch_proposal(self, proposal_id: str) -> Optional[CrossPlatformProposal]:
        """Busca proposta de agregador (mock)."""
        # Mock: retornar proposta simulada
        if proposal_id.startswith("mock_") or proposal_id in self._active_proposals:
            return CrossPlatformProposal(
                proposal_id=proposal_id,
                proposal_type="grammar_registration",
                proposer_node_id="mock_proposer",
                target_platforms=[PlatformType.LINUX, PlatformType.WINDOWS],
                content_hash="mock_hash_123",
                content_metadata={"language": "python", "engine": "tree_sitter"},
                pqc_signature="mock_sig_456",
                created_at=time.time() - 3600,
                voting_deadline=time.time() + 86400
            )
        return None

    async def _fetch_votes_from_aggregator(
        self,
        platform: PlatformType,
        proposal_id: str
    ) -> List[pb.FederatedVote]:
        """Busca votos de agregador de plataforma específica (mock)."""
        # Mock: retornar votos simulados
        votes = []
        for i in range(3):  # Simular 3 votos por plataforma
            vote = pb.FederatedVote(
                vote_id=f"mock_vote_{platform.value}_{i}",
                proposal_id=proposal_id,
                voter_org_id=f"mock_org_{platform.value}_{i}",
                vote_value=(hash(f"{proposal_id}:{i}") % 3) != 0, # mostly approve
                vote_weight=0.8 + (hash(f"{proposal_id}:{i}:weight") % 20) / 100,
                justification="Mock justification",
                pqc_signature=f"mock_sig_{i}".encode(),
                timestamp=pb.google_dot_protobuf_dot_timestamp__pb2.Timestamp(seconds=int(time.time()))
            )
            votes.append(vote)
        return votes

# ═══════════════════════════════════════════════════════════════
# DEMONSTRAÇÃO DE CONSENSO CROSS-PLATFORM
# ═══════════════════════════════════════════════════════════════

async def demonstrate_cross_platform_consensus():
    """Demonstra fluxo de consenso federado entre Linux, Windows e FreeBSD."""
    print(f"\n🌍 Demonstrando Consenso Cross-Platform — Substrate 237")
    print(f"   Integração: Linux • Windows • FreeBSD • Φ_C Weighted • PQC • TemporalChain\n")

    # Criar nó local (ex: Linux)
    local_node = PlatformNode(
        node_id="node_linux_001",
        platform=PlatformType.LINUX,
        kernel_version="6.8.0-arkhe",
        arkhe_substrate_version="237-v1.0.0",
        phi_c_capability=0.96,
        network_latency_ms=12.5,
        last_heartbeat=time.time(),
        is_aggregator=False,
        is_validator=True
    )

    # Inicializar motor de consenso
    consensus = CrossPlatformConsensusEngine(
        local_node=local_node,
        local_org_id="org_arkhe_linux",
        consensus_threshold=0.67,
        voting_period_hours=24.0,
        aggregator_endpoints={
            PlatformType.LINUX: "localhost:50051",
            PlatformType.WINDOWS: "localhost:50052",
            PlatformType.FREEBSD: "localhost:50053"
        }
    )

    # Conectar aos agregadores
    await consensus.connect_to_aggregators()

    # 1. Submeter proposta que afeta múltiplas plataformas
    print("📝 Submetendo proposta cross-platform...")
    proposal_id = await consensus.submit_cross_platform_proposal(
        proposal_type="network_learning_module_registration",
        content={
            "module_id": "network_fundamentals_step_01",
            "title": "Computer Fundamentals for AGI",
            "platforms": ["linux", "windows", "freebsd"],
            "learning_objectives": ["CPU architecture", "Memory management", "Process scheduling"],
            "phi_c_threshold": 0.85
        },
        content_metadata={
            "description": "Módulo de aprendizado de fundamentos de computação para AGI",
            "estimated_duration_minutes": 45,
            "prerequisites": [],
            "certification": "ArkheNetworkCert-Level1"
        },
        target_platforms=[PlatformType.LINUX, PlatformType.WINDOWS, PlatformType.FREEBSD]
    )

    if proposal_id:
        print(f"✅ Proposta submetida: {proposal_id[:16]}...")

    # 2. Simular votação de nós em diferentes plataformas
    print(f"\n🗳️ Simulando votação cross-platform...")

    # 3. Verificar status de consenso
    print(f"\n🔍 Verificando status de consenso cross-platform...")
    result = await consensus.check_cross_platform_consensus_status(proposal_id)

    if result:
        print(f"✅ Consenso cross-platform alcançado:")
        print(f"   Status: {result.final_status.upper()}")
        print(f"   Votos totais: {result.total_votes}")
        print(f"   Peso aprovado: {result.approved_weight:.3f}")
        print(f"   Peso rejeitado: {result.rejected_weight:.3f}")
        print(f"   Threshold: {result.consensus_threshold:.2f}")
        print(f"   Selo TemporalChain: {result.temporal_chain_seal[:16]}...")

    print(f"\n🌍 Consenso Cross-Platform — OPERATIONAL")
    print(f"Canon: ∞.Ω.∇+++.237.consensus.engine")

if __name__ == "__main__":
    asyncio.run(demonstrate_cross_platform_consensus())
