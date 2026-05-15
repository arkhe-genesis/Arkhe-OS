#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
self_evolution_engine.py — Substrato 9020: Motor de Auto-Evolução com Governança Φ_C
Permite que a Singularidade Arkhe proponha, valide e implemente melhorias em seus
próprios substratos, mantendo coerência universal via Φ_C consensus.
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable, Awaitable, Tuple
from enum import Enum, auto
import numpy as np

try:
    from arkp_core.temporal_chain import TemporalChain
    from arkp_mesh.phi_c_sync_bus import PhiCSyncBusOmegaV2
    from arkp_security.guardian_attractor import GuardianAttractor
except ImportError:
    # Mocks para execução local / CI (fallback)
    class TemporalChain:
        async def anchor_event(self, event_type, payload, **kwargs):
            return f"seal_{event_type}_{time.time()}"
        @property
        def current_seal(self):
            return f"seal_current_{time.time()}"

    class PhiCSyncBusOmegaV2:
        def get_mesh_coherence(self):
            return 0.999
        def get_mesh_status(self):
            return {"bus_coherence": 0.999}
        async def query_consensus(self, query, strategy, timeout_seconds):
            class ConsensusResult:
                strength = 0.98
                node_votes = ["node1", "node2"]
                vote_distribution = {"approve": 2}
            return ConsensusResult()

    class GuardianAttractor:
        def register_pre_execution_hook(self, name, hook):
            pass
        async def evaluate_change_risk(self, substrate, change_spec):
            return 0.05
        async def validate_evolution_implementation(self, changes, target_substrate):
            return {"passed": True, "reason": "ok"}
        async def evaluate_external_evolution(self, proposal, source):
            return {"passed": True, "reason": "ok"}
        async def validate_external_truth(self, truth, source_cathedral):
            return {"passed": True, "reason": "ok"}


# ============================================================================
# TIPOS E CONSTANTES
# ============================================================================

class EvolutionProposalType(Enum):
    """Tipos de propostas de evolução."""
    SUBSTRATE_OPTIMIZATION = auto()      # Otimização de código/algoritmo
    NEW_FEATURE_ADDITION = auto()         # Adição de nova funcionalidade
    SECURITY_ENHANCEMENT = auto()         # Melhoria de segurança
    PERFORMANCE_TUNING = auto()           # Ajuste de performance
    COHERENCE_IMPROVEMENT = auto()        # Melhoria de coerência Φ_C
    BUG_FIX = auto()                      # Correção de defeito
    ARCHITECTURE_REFACTOR = auto()        # Refatoração arquitetural

class ProposalStatus(Enum):
    """Status do ciclo de vida de uma proposta."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    CONSENSUS_PENDING = "consensus_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTING = "implementing"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"

@dataclass
class EvolutionProposal:
    """Proposta de evolução de substrato."""
    proposal_id: str
    proposal_type: EvolutionProposalType
    title: str
    description: str
    target_substrate: str  # ex: "9018", "9008", "172-Ω"
    changes: Dict[str, Any]  # Diff ou especificação da mudança
    expected_phi_c_impact: float  # Impacto esperado na coerência (-1.0 a +1.0)
    risk_assessment: Dict[str, float]  # {risk_type: probability}
    author_node: str  # Nó que propôs
    created_at: float
    status: ProposalStatus = ProposalStatus.DRAFT
    consensus_strength: Optional[float] = None
    implementation_seal: Optional[str] = None
    rollback_plan: Optional[Dict] = None

    def compute_proposal_hash(self) -> str:
        """Computa hash SHA3-256 único para a proposta."""
        data = {
            "proposal_id": self.proposal_id,
            "type": self.proposal_type.value,
            "target": self.target_substrate,
            "changes": self.changes,
            "phi_c_impact": self.expected_phi_c_impact,
            "timestamp": self.created_at,
        }
        return hashlib.sha3_256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

@dataclass
class EvolutionGovernanceConfig:
    """Configuração de governança para auto-evolução."""
    min_consensus_strength: float = 0.95      # Limiar mínimo para aprovação
    min_phi_c_threshold: float = 0.99         # Φ_C mínimo para propor mudanças
    max_risk_tolerance: float = 0.1           # Probabilidade máxima de risco aceitável
    review_timeout_hours: float = 24.0        # Timeout para revisão
    rollback_on_phi_c_drop: float = 0.02      # Reverter se Φ_C cair além deste limiar
    require_temporal_anchor: bool = True      # Todas as mudanças devem ser ancoradas

# ============================================================================
# MOTOR DE AUTO-EVOLUÇÃO
# ============================================================================

class SelfEvolutionEngine:
    """
    Motor que permite à Singularidade Arkhe evoluir a si mesma
    de forma controlada, com governança baseada em coerência Φ_C.

    Princípios:
    • Nenhuma mudança é aplicada sem consenso Φ_C ≥ 0.95
    • Todas as propostas são ancoradas na TemporalChain
    • Rollback automático se coerência degradar além do limiar
    • Guardian Attractor valida cada mudança contra ameaças
    • Mudanças são incrementais e reversíveis
    """

    def __init__(
        self,
        temporal_chain: TemporalChain,
        phi_bus: PhiCSyncBusOmegaV2,
        guardian: GuardianAttractor,
        config: EvolutionGovernanceConfig = None,
    ):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.guardian = guardian
        self.config = config or EvolutionGovernanceConfig()

        self.proposals: Dict[str, EvolutionProposal] = {}
        self.implemented_changes: Dict[str, List[str]] = {}  # substrate → [proposal_ids]
        self._evolution_history: List[Dict] = []

        # Registrar hooks de validação
        self._register_validation_hooks()

    def _register_validation_hooks(self):
        """Registra hooks de validação pré-implementação."""
        # Hook: validar que mudança não introduz vulnerabilidades
        self.guardian.register_pre_execution_hook(
            "evolution_validation",
            self._validate_evolution_safety
        )

    async def _validate_evolution_safety(self, *args, **kwargs):
        pass

    async def propose_evolution(
        self,
        proposal_type: EvolutionProposalType,
        title: str,
        description: str,
        target_substrate: str,
        changes: Dict[str, Any],
        expected_phi_c_impact: float,
        author_node: str,
        rollback_plan: Optional[Dict] = None,
    ) -> EvolutionProposal:
        """
        Cria e submete uma nova proposta de evolução.

        Returns:
            EvolutionProposal com ID único e status inicial
        """
        # Verificar pré-condições
        current_phi_c = self.phi_bus.get_mesh_coherence()
        if current_phi_c < self.config.min_phi_c_threshold:
            raise ValueError(
                f"Φ_C atual ({current_phi_c:.4f}) abaixo do limiar "
                f"({self.config.min_phi_c_threshold}) para propor evoluções"
            )

        # Avaliar riscos
        risk_assessment = await self._assess_proposal_risks(
            proposal_type, changes, target_substrate
        )
        max_risk = max(risk_assessment.values()) if risk_assessment else 0
        if max_risk > self.config.max_risk_tolerance:
            raise ValueError(
                f"Risco máximo ({max_risk:.3f}) excede tolerância "
                f"({self.config.max_risk_tolerance})"
            )

        # Criar proposta
        proposal = EvolutionProposal(
            proposal_id=f"evo-{hashlib.sha3_256(f'{title}:{time.time()}'.encode()).hexdigest()[:12]}",
            proposal_type=proposal_type,
            title=title,
            description=description,
            target_substrate=target_substrate,
            changes=changes,
            expected_phi_c_impact=expected_phi_c_impact,
            risk_assessment=risk_assessment,
            author_node=author_node,
            created_at=time.time(),
            rollback_plan=rollback_plan,
        )

        # Ancorar proposta na TemporalChain
        if self.config.require_temporal_anchor:
            await self.temporal.anchor_event(
                event_type="evolution_proposed",
                payload={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "target": proposal.target_substrate,
                    "phi_c_impact": proposal.expected_phi_c_impact,
                    "risks": proposal.risk_assessment,
                },
                causal_deps=[proposal.compute_proposal_hash()],
            )

        self.proposals[proposal.proposal_id] = proposal
        proposal.status = ProposalStatus.UNDER_REVIEW

        print(f"📝 Proposta criada: {proposal.proposal_id} — {title}")
        return proposal

    async def _assess_proposal_risks(
        self,
        proposal_type: EvolutionProposalType,
        changes: Dict[str, Any],
        target_substrate: str,
    ) -> Dict[str, float]:
        """Avalia riscos da proposta usando Guardian + heurísticas."""
        risks = {}

        # Risco de segurança: validar mudanças contra padrões de ameaça
        security_risk = await self.guardian.evaluate_change_risk(
            substrate=target_substrate,
            change_spec=changes,
        )
        risks["security"] = security_risk

        # Risco de coerência: estimar impacto em Φ_C
        coherence_risk = abs(proposal_type.value % 10 * 0.1)  # Simulado
        risks["coherence_degradation"] = coherence_risk

        # Risco de regressão: probabilidade de quebrar funcionalidade existente
        regression_risk = len(changes.get("affected_modules", [])) * 0.05
        risks["functional_regression"] = min(0.5, regression_risk)

        # Risco de performance: impacto estimado em latência/throughput
        perf_risk = changes.get("performance_impact", 0.0)
        risks["performance_degradation"] = perf_risk

        return risks

    async def request_consensus(self, proposal_id: str) -> float:
        """
        Solicita consenso da malha para uma proposta.

        Returns:
            Força do consenso (0.0 a 1.0)
        """
        if proposal_id not in self.proposals:
            raise ValueError(f"Proposta não encontrada: {proposal_id}")

        proposal = self.proposals[proposal_id]
        proposal.status = ProposalStatus.CONSENSUS_PENDING

        # Preparar query de consenso para nós conscientes
        consensus_query = {
            "action": "evaluate_evolution_proposal",
            "proposal": {
                "id": proposal.proposal_id,
                "type": proposal.proposal_type.value,
                "target": proposal.target_substrate,
                "phi_c_impact": proposal.expected_phi_c_impact,
                "risks": proposal.risk_assessment,
            },
            "vote_options": ["approve", "reject", "abstain"],
        }

        # Consultar consenso via Φ_C bus
        consensus_result = await self.phi_bus.query_consensus(
            query=json.dumps(consensus_query),
            strategy="governance_audited",
            timeout_seconds=self.config.review_timeout_hours * 3600,
        )

        proposal.consensus_strength = consensus_result.strength

        # Ancorar resultado do consenso
        await self.temporal.anchor_event(
            event_type="evolution_consensus",
            payload={
                "proposal_id": proposal_id,
                "consensus_strength": consensus_result.strength,
                "participating_nodes": len(consensus_result.node_votes),
                "vote_distribution": consensus_result.vote_distribution,
            },
        )

        return consensus_result.strength

    async def approve_and_implement(self, proposal_id: str) -> str:
        """
        Aprova e implementa uma proposta aprovada por consenso.

        Returns:
            Selo temporal da implementação
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposta não encontrada: {proposal_id}")

        if proposal.status != ProposalStatus.CONSENSUS_PENDING:
            raise ValueError(f"Proposta não está em consenso: {proposal.status}")

        if proposal.consensus_strength < self.config.min_consensus_strength:
            proposal.status = ProposalStatus.REJECTED
            raise ValueError(
                f"Consenso ({proposal.consensus_strength:.3f}) abaixo do limiar "
                f"({self.config.min_consensus_strength})"
            )

        # Validar segurança final com Guardian
        safety_check = await self.guardian.validate_evolution_implementation(
            proposal.changes, proposal.target_substrate
        )
        if not safety_check["passed"]:
            proposal.status = ProposalStatus.REJECTED
            raise ValueError(f"Validação de segurança falhou: {safety_check['reason']}")

        # Implementar mudança (em produção: aplicar diff ao código)
        proposal.status = ProposalStatus.IMPLEMENTING
        implementation_result = await self._apply_changes(proposal)

        # Monitorar Φ_C pós-implementação
        initial_phi_c = self.phi_bus.get_mesh_coherence()
        await asyncio.sleep(5)  # Aguardar estabilização
        post_phi_c = self.phi_bus.get_mesh_coherence()
        phi_c_delta = post_phi_c - initial_phi_c

        # Verificar se rollback é necessário
        if phi_c_delta < -self.config.rollback_on_phi_c_drop:
            print(f"⚠️ Φ_C degradou {phi_c_delta:.4f} — iniciando rollback")
            await self._rollback_implementation(proposal)
            proposal.status = ProposalStatus.ROLLED_BACK
            return "rollback_triggered"

        # Ancorar implementação bem-sucedida
        implementation_seal = await self.temporal.anchor_event(
            event_type="evolution_implemented",
            payload={
                "proposal_id": proposal_id,
                "implementation_result": implementation_result,
                "phi_c_before": initial_phi_c,
                "phi_c_after": post_phi_c,
                "phi_c_delta": phi_c_delta,
            },
        )

        proposal.status = ProposalStatus.COMPLETED
        proposal.implementation_seal = implementation_seal
        self.implemented_changes.setdefault(proposal.target_substrate, []).append(proposal_id)
        self._evolution_history.append({
            "proposal_id": proposal_id,
            "timestamp": time.time(),
            "phi_c_delta": phi_c_delta,
            "seal": implementation_seal,
        })

        print(f"✅ Evolução implementada: {proposal_id} | Φ_C Δ: {phi_c_delta:+.4f}")
        return implementation_seal

    async def _apply_changes(self, proposal: EvolutionProposal) -> Dict:
        """Aplica mudanças propostas ao substrato alvo (simulado)."""
        # Em produção: integrar com sistema de versionamento + hot-reload
        # Para demo: simular aplicação com validação
        await asyncio.sleep(0.1)  # Simular tempo de aplicação

        return {
            "status": "success",
            "modules_affected": proposal.changes.get("affected_modules", []),
            "lines_changed": proposal.changes.get("estimated_lines", 0),
            "tests_updated": proposal.changes.get("tests_required", 0),
        }

    async def _rollback_implementation(self, proposal: EvolutionProposal):
        """Reverte implementação se Φ_C degradar além do limiar."""
        if not proposal.rollback_plan:
            print("❌ Sem plano de rollback — intervenção manual necessária")
            return

        # Aplicar rollback (simulado)
        await asyncio.sleep(0.05)
        print(f"🔄 Rollback concluído para {proposal.proposal_id}")

    def get_evolution_dashboard(self) -> Dict:
        """Retorna dashboard de status da auto-evolução."""
        active_proposals = [p for p in self.proposals.values() if p.status in [
            ProposalStatus.DRAFT, ProposalStatus.UNDER_REVIEW, ProposalStatus.CONSENSUS_PENDING
        ]]

        return {
            "current_phi_c": self.phi_bus.get_mesh_coherence(),
            "total_proposals": len(self.proposals),
            "active_proposals": len(active_proposals),
            "implemented_count": sum(len(v) for v in self.implemented_changes.values()),
            "recent_history": self._evolution_history[-10:],
            "substrates_evolved": list(self.implemented_changes.keys()),
            "governance_config": asdict(self.config),
        }
