#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collaborative_review.py — Substrato 9004: Revisão Colaborativa com Consenso
Implementa workflow de revisão ética com múltiplos revisores para decisões mais robustas:
• Atribuição inteligente baseada em expertise e carga de trabalho
• Quórum configurável por nível de risco
• Resolução de conflitos via votação ponderada por reputação
• Fallback para comitê de ética em caso de desacordo persistente
• Auditoria completa de todas as contribuições no TemporalChain
"""

import hashlib
import json
import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable, Any
from enum import Enum, auto
from collections import defaultdict

# ============================================================================
# TIPOS DE DADOS
# ============================================================================

class ReviewVote(Enum):
    """Votos possíveis em revisão colaborativa."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    ABSTAIN = "abstain"
    ESCALATE = "escalate"  # Para comitê de ética

class PublicationDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"
    QUARANTINED = "quarantined"

class ConsensusStrategy(Enum):
    """Estratégias para alcançar consenso."""
    MAJORITY = "majority"           # Maioria simples
    SUPERMAJORITY = "supermajority"  # 2/3 ou mais
    UNANIMOUS = "unanimous"         # Todos devem concordar
    WEIGHTED = "weighted"           # Ponderado por reputação QIP

@dataclass
class ReviewerContribution:
    """Contribuição individual de um revisor em uma tarefa."""
    reviewer_id: str
    vote: ReviewVote
    rationale: str
    suggested_changes: List[str]
    confidence_score: float  # 0.0-1.0, auto-avaliação do revisor
    timestamp: float
    signature: Optional[str] = None  # Assinatura criptográfica da contribuição

@dataclass
class CollaborativeReviewTask:
    """Tarefa de revisão com múltiplos revisores."""
    task_id: str
    package_name: str
    package_version: str
    author_orcid: str
    risk_score: float
    risk_breakdown: Dict[str, float]
    conrag_report: Dict
    source_files: List[Dict]
    dependencies: List[Dict]
    created_at: float
    deadline_at: float
    assigned_reviewers: List[str]  # reviewer_ids
    consensus_strategy: ConsensusStrategy
    quorum_threshold: float  # Fração mínima de concordância (0.5-1.0)
    min_reputation: float  # Reputação mínima para participar
    contributions: Dict[str, ReviewerContribution] = field(default_factory=dict)
    status: str = "pending"  # pending, in_progress, consensus_reached, escalated, expired
    final_decision: Optional[PublicationDecision] = None
    consensus_score: Optional[float] = None
    escalation_reason: Optional[str] = None

@dataclass
class ConsensusResult:
    """Resultado do processo de consenso."""
    task_id: str
    decision: PublicationDecision
    consensus_score: float
    votes_summary: Dict[str, int]  # vote_type -> count
    weighted_score: float
    dissenting_opinions: List[Dict]
    timestamp: float
    audit_seal: str  # Hash para auditoria

# ============================================================================
# MOTOR DE CONSENSO COLABORATIVO
# ============================================================================

class ConsensusReviewEngine:
    """
    Motor para alcançar consenso em revisões éticas colaborativas.
    Características:
    • Votação ponderada por reputação QIP
    • Estratégias de consenso configuráveis
    • Detecção de conflitos e fallback para escalonamento
    • Geração de selo de auditoria para cada decisão
    """

    # Configurações padrão por nível de risco
    RISK_CONFIGS = {
        "low": {"quorum": 0.5, "strategy": ConsensusStrategy.MAJORITY, "min_reviewers": 2},
        "medium": {"quorum": 0.66, "strategy": ConsensusStrategy.SUPERMAJORITY, "min_reviewers": 3},
        "high": {"quorum": 0.8, "strategy": ConsensusStrategy.WEIGHTED, "min_reviewers": 5},
        "critical": {"quorum": 1.0, "strategy": ConsensusStrategy.UNANIMOUS, "min_reviewers": 7},
    }

    def __init__(
        self,
        qip_engine: Optional[Any] = None,
        temporal_client: Optional[Any] = None,
        ledger: Optional[Any] = None,
    ):
        self.qip_engine = qip_engine
        self.temporal_client = temporal_client
        self.ledger = ledger
        self._tasks: Dict[str, CollaborativeReviewTask] = {}
        self._consensus_results: Dict[str, ConsensusResult] = {}

    def create_review_task(
        self,
        package_name: str,
        package_version: str,
        author_orcid: str,
        risk_score: float,
        risk_breakdown: Dict,
        conrag_report: Dict,
        source_files: List[Dict],
        dependencies: List[Dict],
        assigned_reviewers: List[str],
        deadline_hours: float = 72.0,
    ) -> CollaborativeReviewTask:
        """Cria nova tarefa de revisão colaborativa."""
        # Determinar configuração baseada no risco
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        config = self.RISK_CONFIGS[risk_level]

        task = CollaborativeReviewTask(
            task_id=hashlib.sha3_256(
                f"{package_name}:{package_version}:{time.time()}".encode()
            ).hexdigest()[:16],
            package_name=package_name,
            package_version=package_version,
            author_orcid=author_orcid,
            risk_score=risk_score,
            risk_breakdown=risk_breakdown,
            conrag_report=conrag_report,
            source_files=source_files,
            dependencies=dependencies,
            created_at=time.time(),
            deadline_at=time.time() + deadline_hours * 3600,
            assigned_reviewers=assigned_reviewers[:config["min_reviewers"]],
            consensus_strategy=config["strategy"],
            quorum_threshold=config["quorum"],
            min_reputation=0.7 if risk_level in ["high", "critical"] else 0.5,
        )

        self._tasks[task.task_id] = task

        # Registrar no ledger se disponível
        if self.ledger:
            self.ledger.record("collaborative_review_created", {
                "task_id": task.task_id,
                "package": f"{package_name}@{package_version}",
                "risk_level": risk_level,
                "reviewers": task.assigned_reviewers,
                "deadline_hours": deadline_hours,
            })

        return task

    async def submit_vote(
        self,
        task_id: str,
        reviewer_id: str,
        vote: ReviewVote,
        rationale: str,
        suggested_changes: Optional[List[str]] = None,
        confidence: float = 0.8,
    ) -> Dict:
        """
        Submete voto de um revisor em uma tarefa.
        Retorna status da submissão e se consenso foi alcançado.
        """
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        if reviewer_id not in task.assigned_reviewers:
            return {"error": "Reviewer not assigned to this task"}

        if task.status != "pending" and task.status != "in_progress":
            return {"error": f"Task already {task.status}"}

        # Verificar reputação mínima
        if self.qip_engine:
            reputation = self.qip_engine.get_reputation_score(reviewer_id)
            if reputation < task.min_reputation:
                return {"error": f"Reputation {reputation:.2f} below minimum {task.min_reputation}"}
        else:
            reputation = 0.8  # Default

        # Criar contribuição
        contribution = ReviewerContribution(
            reviewer_id=reviewer_id,
            vote=vote,
            rationale=rationale,
            suggested_changes=suggested_changes or [],
            confidence_score=confidence,
            timestamp=time.time(),
        )

        # Assinar contribuição criptograficamente (simulado)
        contribution.signature = hashlib.sha3_256(
            f"{task_id}:{reviewer_id}:{vote.value}:{rationale}".encode()
        ).hexdigest()

        # Registrar contribuição
        task.contributions[reviewer_id] = contribution
        task.status = "in_progress"

        # Verificar se atingiu quórum de votos
        if len(task.contributions) >= len(task.assigned_reviewers) * 0.8:
            # Tentar alcançar consenso
            result = await self._compute_consensus(task)
            if result:
                task.status = "consensus_reached"
                task.final_decision = result.decision
                task.consensus_score = result.consensus_score
                self._consensus_results[task_id] = result

                # Registrar decisão no ledger
                if self.ledger:
                    self.ledger.record("collaborative_consensus_reached", {
                        "task_id": task_id,
                        "decision": result.decision.value,
                        "consensus_score": result.consensus_score,
                        "votes": result.votes_summary,
                        "audit_seal": result.audit_seal,
                    })

                return {
                    "success": True,
                    "consensus_reached": True,
                    "decision": result.decision.value,
                    "consensus_score": result.consensus_score,
                }

        return {
            "success": True,
            "consensus_reached": False,
            "votes_received": len(task.contributions),
            "votes_required": int(len(task.assigned_reviewers) * task.quorum_threshold),
        }

    async def _compute_consensus(self, task: CollaborativeReviewTask) -> Optional[ConsensusResult]:
        """Computa consenso baseado na estratégia configurada."""
        if not task.contributions:
            return None

        votes = [c.vote for c in task.contributions.values()]
        reviewers = list(task.contributions.keys())

        # Contar votos
        vote_counts = defaultdict(int)
        for vote in votes:
            vote_counts[vote.value] += 1

        # Obter reputações para ponderação
        weights = {}
        if self.qip_engine:
            for rid in reviewers:
                weights[rid] = self.qip_engine.get_reputation_score(rid)
        else:
            weights = {rid: 0.8 for rid in reviewers}  # Default

        # Aplicar estratégia de consenso
        if task.consensus_strategy == ConsensusStrategy.MAJORITY:
            winner = max(vote_counts, key=vote_counts.get)
            consensus_reached = vote_counts[winner] / len(votes) >= task.quorum_threshold

        elif task.consensus_strategy == ConsensusStrategy.SUPERMAJORITY:
            winner = max(vote_counts, key=vote_counts.get)
            consensus_reached = vote_counts[winner] / len(votes) >= task.quorum_threshold

        elif task.consensus_strategy == ConsensusStrategy.UNANIMOUS:
            consensus_reached = len(set(votes)) == 1
            winner = votes[0] if consensus_reached else None

        elif task.consensus_strategy == ConsensusStrategy.WEIGHTED:
            # Calcular score ponderado por voto
            vote_scores = {v.value: 0.0 for v in ReviewVote}
            for rid, contribution in task.contributions.items():
                weight = weights.get(rid, 0.5) * contribution.confidence_score
                vote_scores[contribution.vote.value] += weight

            winner = max(vote_scores, key=vote_scores.get)
            total_weight = sum(weights.get(rid, 0.5) * task.contributions[rid].confidence_score
                              for rid in reviewers)
            consensus_reached = vote_scores[winner] / max(0.001, total_weight) >= task.quorum_threshold
        else:
            return None

        if not consensus_reached:
            # Verificar se deve escalar para comitê de ética
            if task.risk_score >= 0.7 or len(set(votes)) >= 3:
                task.status = "escalated"
                task.escalation_reason = "No consensus reached; escalating to ethics committee"
                return None
            return None

        # Mapear voto vencedor para decisão final
        decision_map = {
            ReviewVote.APPROVE.value: PublicationDecision.APPROVED,
            ReviewVote.REJECT.value: PublicationDecision.REJECTED,
            ReviewVote.REQUEST_CHANGES.value: PublicationDecision.REQUIRES_REVIEW,
            ReviewVote.ESCALATE.value: PublicationDecision.QUARANTINED,
        }
        final_decision = decision_map.get(winner, PublicationDecision.REQUIRES_REVIEW)

        # Calcular score de consenso ponderado
        weighted_score = sum(
            weights.get(rid, 0.5) * (1.0 if c.vote.value == winner else 0.0)
            for rid, c in task.contributions.items()
        ) / max(0.001, sum(weights.get(rid, 0.5) for rid in reviewers))

        # Coletar opiniões dissidentes
        dissenting = [
            {
                "reviewer_id": rid,
                "vote": c.vote.value,
                "rationale": c.rationale,
            }
            for rid, c in task.contributions.items()
            if c.vote.value != winner
        ]

        # Gerar selo de auditoria
        audit_data = {
            "task_id": task.task_id,
            "decision": final_decision.value,
            "votes": {k: v for k, v in vote_counts.items()},
            "weighted_score": weighted_score,
            "timestamp": time.time(),
        }
        audit_seal = hashlib.sha3_256(json.dumps(audit_data, sort_keys=True).encode()).hexdigest()

        return ConsensusResult(
            task_id=task.task_id,
            decision=final_decision,
            consensus_score=weighted_score,
            votes_summary=dict(vote_counts),
            weighted_score=weighted_score,
            dissenting_opinions=dissenting,
            timestamp=time.time(),
            audit_seal=audit_seal,
        )

    def get_task_status(self, task_id: str) -> Dict:
        """Retorna status detalhado de uma tarefa de revisão."""
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        # Contar votos por tipo
        vote_counts = defaultdict(int)
        for c in task.contributions.values():
            vote_counts[c.vote.value] += 1

        return {
            "task_id": task.task_id,
            "package": f"{task.package_name}@{task.package_version}",
            "status": task.status,
            "risk_score": task.risk_score,
            "assigned_reviewers": task.assigned_reviewers,
            "contributions_count": len(task.contributions),
            "quorum_threshold": task.quorum_threshold,
            "votes_summary": dict(vote_counts),
            "deadline_hours": max(0, (task.deadline_at - time.time()) / 3600),
            "final_decision": task.final_decision.value if task.final_decision else None,
            "consensus_score": task.consensus_score,
        }

    def get_pending_tasks_for_reviewer(self, reviewer_id: str) -> List[CollaborativeReviewTask]:
        """Retorna tarefas pendentes atribuídas a um revisor."""
        return [
            task for task in self._tasks.values()
            if reviewer_id in task.assigned_reviewers
            and task.status in ["pending", "in_progress"]
            and time.time() < task.deadline_at
        ]

# ============================================================================
# WORKFLOW DE REVISÃO COLABORATIVA
# ============================================================================

class CollaborativeReviewWorkflow:
    """
    Orquestra o workflow completo de revisão colaborativa:
    1. Criar tarefa com atribuição inteligente
    2. Notificar revisores
    3. Coletar votos e computar consenso
    4. Executar decisão ou escalar se necessário
    5. Registrar auditoria completa
    """

    def __init__(
        self,
        consensus_engine: ConsensusReviewEngine,
        notification_fn: Optional[Callable] = None,
    ):
        self.consensus_engine = consensus_engine
        self.notify = notification_fn or (lambda **k: None)

    async def initiate_collaborative_review(
        self,
        package_name: str,
        package_version: str,
        author_orcid: str,
        risk_score: float,
        risk_breakdown: Dict,
        conrag_report: Dict,
        source_files: List[Dict],
        dependencies: List[Dict],
        available_reviewers: List[Dict],  # [{reviewer_id, expertise, reputation, load}]
    ) -> CollaborativeReviewTask:
        """
        Inicia revisão colaborativa com atribuição inteligente de revisores.
        """
        # Selecionar revisores baseado em:
        # 1. Expertise relevante ao domínio do pacote
        # 2. Reputação QIP suficiente
        # 3. Carga de trabalho atual (evitar sobrecarga)
        # 4. Diversidade de perspectivas

        # Filtrar por reputação mínima
        qualified = [r for r in available_reviewers if r.get("reputation", 0) >= 0.7]

        # Ordenar por: expertise match > reputação > carga baixa
        def score_reviewer(r):
            expertise_match = any(e in risk_breakdown for e in r.get("expertise", []))
            rep = r.get("reputation", 0.5)
            load = r.get("active_tasks", 0)
            return (expertise_match * 10) + (rep * 5) - (load * 0.5)

        qualified.sort(key=score_reviewer, reverse=True)

        # Selecionar top N baseado no nível de risco
        min_reviewers = 3 if risk_score >= 0.6 else 2
        selected = [r["reviewer_id"] for r in qualified[:min_reviewers + 2]]  # +2 para redundância

        # Criar tarefa
        task = self.consensus_engine.create_review_task(
            package_name=package_name,
            package_version=package_version,
            author_orcid=author_orcid,
            risk_score=risk_score,
            risk_breakdown=risk_breakdown,
            conrag_report=conrag_report,
            source_files=source_files,
            dependencies=dependencies,
            assigned_reviewers=selected,
            deadline_hours=72.0 if risk_score < 0.6 else 24.0,
        )

        # Notificar revisores selecionados
        for reviewer_id in selected:
            if asyncio.iscoroutinefunction(self.notify):
                await self.notify(
                    reviewer_id=reviewer_id,
                    task_id=task.task_id,
                    package=f"{package_name}@{package_version}",
                    risk_score=risk_score,
                    deadline_hours=task.deadline_at - time.time(),
                )
            else:
                self.notify(
                    reviewer_id=reviewer_id,
                    task_id=task.task_id,
                    package=f"{package_name}@{package_version}",
                    risk_score=risk_score,
                    deadline_hours=task.deadline_at - time.time(),
                )

        return task

    async def process_collaborative_decision(self, task: CollaborativeReviewTask) -> Dict:
        """
        Processa decisão final após consenso ou escalonamento.
        """
        if task.status == "consensus_reached" and task.final_decision:
            # Decisão por consenso
            return {
                "decision": task.final_decision.value,
                "method": "consensus",
                "consensus_score": task.consensus_score,
                "audit_seal": self._get_audit_seal(task.task_id),
            }

        elif task.status == "escalated":
            # Escalonar para comitê de ética (simulado)
            committee_decision = await self._escalate_to_ethics_committee(task)
            return {
                "decision": committee_decision.value,
                "method": "ethics_committee",
                "escalation_reason": task.escalation_reason,
                "audit_seal": self._generate_committee_seal(task, committee_decision),
            }

        elif task.status == "expired":
            # Timeout: decisão conservadora
            return {
                "decision": PublicationDecision.REQUIRES_REVIEW.value,
                "method": "timeout_fallback",
                "reason": "Deadline exceeded without consensus",
                "audit_seal": self._generate_timeout_seal(task),
            }

        return {"error": f"Task not resolved: {task.status}"}

    async def _escalate_to_ethics_committee(self, task: CollaborativeReviewTask) -> PublicationDecision:
        """Simula escalonamento para comitê de ética."""
        # Em produção: notificar comitê humano, aguardar decisão
        # Aqui: decisão baseada em regras conservadoras
        if task.risk_score >= 0.8:
            return PublicationDecision.REJECTED
        elif any(c.vote == ReviewVote.REJECT for c in task.contributions.values()):
            return PublicationDecision.REQUIRES_REVIEW
        else:
            return PublicationDecision.APPROVED

    def _get_audit_seal(self, task_id: str) -> str:
        """Retorna selo de auditoria para tarefa."""
        result = self.consensus_engine._consensus_results.get(task_id)
        return result.audit_seal if result else ""

    def _generate_committee_seal(self, task: CollaborativeReviewTask,
                                  decision: PublicationDecision) -> str:
        """Gera selo de auditoria para decisão do comitê."""
        data = {
            "task_id": task.task_id,
            "decision": decision.value,
            "method": "ethics_committee",
            "timestamp": time.time(),
        }
        return hashlib.sha3_256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def _generate_timeout_seal(self, task: CollaborativeReviewTask) -> str:
        """Gera selo de auditoria para decisão por timeout."""
        data = {
            "task_id": task.task_id,
            "decision": PublicationDecision.REQUIRES_REVIEW.value,
            "method": "timeout_fallback",
            "timestamp": time.time(),
        }
        return hashlib.sha3_256(json.dumps(data, sort_keys=True).encode()).hexdigest()
