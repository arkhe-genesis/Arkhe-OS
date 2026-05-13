#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
synthetic_reviewer.py — Substrato 9014: Agente Autonomo Revisor Sintetico
Revisor sintetico com QIP auto-evolutivo, aprendizado por reforco e meta-cognicao.
"""

import asyncio
import hashlib
import json
import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from collections import deque, defaultdict


class AgentState(Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    REVIEWING = "reviewing"
    LEARNING = "learning"
    SLEEPING = "sleeping"


@dataclass
class ReviewExperience:
    """Experiencia de revisao para aprendizado."""
    task_id: str
    package_name: str
    domain: str
    risk_score: float
    vote: str
    final_decision: str
    was_correct: bool
    confidence: float
    rationale: str
    timestamp: float
    feedback_delta: float = 0.0


@dataclass
class AgentMemory:
    """Memoria episodica do agente."""
    experiences: deque = field(default_factory=lambda: deque(maxlen=1000))
    domain_patterns: Dict[str, List[Dict]] = field(default_factory=lambda: defaultdict(list))
    confidence_history: deque = field(default_factory=lambda: deque(maxlen=100))
    error_patterns: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class SyntheticReviewerAgent:
    """
    Agente revisor sintetico com capacidades:
    - Analise automatica de pacotes por dominio
    - Aprendizado por reforco com feedback QIP
    - Meta-cognicao: avalia propria confianca
    - Auto-evolucao: ajusta estrategia por dominio
    - Sleep/awake cycle para consolidacao
    """

    def __init__(self, agent_id: str, qip_engine: Any, domain_expertise: List[str]):
        self.agent_id = agent_id
        self.qip = qip_engine
        self.domain_expertise = domain_expertise
        self.state = AgentState.IDLE
        self.memory = AgentMemory()
        self._confidence_model: Dict[str, float] = {d: 0.7 for d in domain_expertise}
        self._accuracy_model: Dict[str, float] = {d: 0.5 for d in domain_expertise}
        self._learning_rate = 0.05
        self._exploration_rate = 0.1
        self._running = False
        self._review_count = 0
        self._correct_count = 0

    async def analyze_package(self, manifest: Dict, source_files: List[Tuple[str, str]],
                              dependencies: List[Dict], domain: str) -> Dict:
        """Analisa pacote e retorna avaliacao sintetica."""
        self.state = AgentState.ANALYZING

        # Extrair features do codigo
        features = self._extract_features(source_files, domain)

        # Avaliar risco por dominio usando modelo interno
        domain_confidence = self._confidence_model.get(domain, 0.5)
        domain_accuracy = self._accuracy_model.get(domain, 0.5)

        # Heuristica: pacotes com mais linhas = mais risco (simplificado)
        total_lines = sum(len(content.split("\n")) for _, content in source_files)
        complexity_risk = min(1.0, total_lines / 1000.0)

        # Pattern matching por dominio
        pattern_risks = self._match_domain_patterns(source_files, domain)

        # Score combinado
        combined_risk = (complexity_risk * 0.3 +
                         pattern_risks * 0.5 +
                         (1.0 - domain_accuracy) * 0.2)

        # Decisao com exploracao/Exploitacao
        if random.random() < self._exploration_rate:
            vote = random.choice(["approve", "reject", "request_changes"])
            exploration = True
        else:
            vote = self._decide_by_risk(combined_risk, domain_confidence)
            exploration = False

        # Meta-cognicao: avaliar confianca na propria decisao
        meta_confidence = domain_confidence * (1.0 - abs(combined_risk - 0.5) * 2)
        if meta_confidence < 0.5:
            vote = "request_changes"  # Pedir revisao humana quando incerto

        self.state = AgentState.IDLE

        return {
            "vote": vote,
            "confidence": meta_confidence,
            "risk_score": combined_risk,
            "features": features,
            "exploration": exploration,
            "domain": domain,
            "agent_id": self.agent_id,
        }

    def _extract_features(self, source_files: List[Tuple[str, str]], domain: str) -> Dict:
        """Extrai features estatisticas do codigo."""
        features = {
            "total_files": len(source_files),
            "total_lines": sum(len(content.split("\n")) for _, content in source_files),
            "avg_line_length": 0.0,
            "has_tests": False,
            "has_docs": False,
            "has_crypto": False,
            "has_network": False,
        }

        if source_files:
            total_chars = sum(len(content) for _, content in source_files)
            features["avg_line_length"] = total_chars / max(1, features["total_lines"])

        for filename, content in source_files:
            content_lower = content.lower()
            if "test" in filename.lower() or "def test_" in content:
                features["has_tests"] = True
            if "#" in content or "\"\"\"" in content or "\'\'\'" in content:
                features["has_docs"] = True
            if any(k in content_lower for k in ["encrypt", "cipher", "hash", "sha", "aes", "rsa"]):
                features["has_crypto"] = True
            if any(k in content_lower for k in ["socket", "http", "request", "network", "api"]):
                features["has_network"] = True

        return features

    def _match_domain_patterns(self, source_files: List[Tuple[str, str]], domain: str) -> float:
        """Match de padroes por dominio usando memoria."""
        patterns = self.memory.domain_patterns.get(domain, [])
        if not patterns:
            return 0.3  # Risco base quando nao conhece dominio

        # Similaridade com padroes conhecidos (simplificado)
        risk_sum = 0.0
        for _, content in source_files:
            for pattern in patterns[-10:]:  # Ultimos 10 padroes
                if pattern.get("keyword") in content.lower():
                    risk_sum += pattern.get("risk_weight", 0.1)

        return min(1.0, risk_sum / max(1, len(source_files)))

    def _decide_by_risk(self, risk: float, confidence: float) -> str:
        """Decide voto baseado no risco e confianca."""
        if risk > 0.7:
            return "reject"
        elif risk > 0.4:
            return "request_changes"
        else:
            return "approve"

    async def learn_from_feedback(self, experience: ReviewExperience) -> Dict:
        """Aprende com feedback do consenso final."""
        self.state = AgentState.LEARNING

        # Armazenar experiencia
        self.memory.experiences.append(experience)
        self.memory.confidence_history.append(experience.confidence)

        # Atualizar modelo de dominio
        domain = experience.domain
        if experience.was_correct:
            # Reforco positivo: aumentar confianca e acuracia
            self._confidence_model[domain] = min(1.0,
                self._confidence_model.get(domain, 0.5) + self._learning_rate)
            self._accuracy_model[domain] = min(1.0,
                self._accuracy_model.get(domain, 0.5) + self._learning_rate * 0.5)
            self._correct_count += 1
        else:
            # Reforco negativo: diminuir confianca, registrar erro
            self._confidence_model[domain] = max(0.1,
                self._confidence_model.get(domain, 0.5) - self._learning_rate * 2)
            self.memory.error_patterns[domain] += 1

            # Extrair padrao de erro para memoria
            self.memory.domain_patterns[domain].append({
                "keyword": self._extract_error_keyword(experience.rationale),
                "risk_weight": 0.3,
                "timestamp": time.time(),
            })

        self._review_count += 1

        # Decaimento de exploracao
        self._exploration_rate = max(0.01, self._exploration_rate * 0.995)

        # Atualizar QIP se disponivel
        if hasattr(self.qip, "record_contribution"):
            self.qip.record_contribution(
                reviewer_id=self.agent_id,
                task_id=experience.task_id,
                vote=experience.vote,
                final_decision=experience.final_decision,
                response_time_hours=0.5,
                rationale_length=len(experience.rationale),
                domain=domain,
            )

        self.state = AgentState.IDLE

        return {
            "domain": domain,
            "was_correct": experience.was_correct,
            "new_confidence": self._confidence_model[domain],
            "new_accuracy": self._accuracy_model[domain],
            "total_experiences": len(self.memory.experiences),
            "exploration_rate": self._exploration_rate,
        }

    def _extract_error_keyword(self, rationale: str) -> str:
        """Extrai keyword relevante da justificativa de erro."""
        keywords = ["privacy", "security", "bias", "fairness", "transparency", "governance",
                    "encryption", "consent", "audit", "compliance"]
        rationale_lower = rationale.lower()
        for kw in keywords:
            if kw in rationale_lower:
                return kw
        return "general"

    async def sleep_cycle(self, duration_seconds: float = 60.0):
        """Ciclo de sono para consolidacao de aprendizado."""
        self.state = AgentState.SLEEPING

        # Consolidar padroes: remover duplicados, manter mais frequentes
        for domain, patterns in self.memory.domain_patterns.items():
            if len(patterns) > 50:
                # Manter apenas padroes mais recentes e unicos
                seen = set()
                consolidated = []
                for p in reversed(patterns):
                    key = p.get("keyword", "")
                    if key not in seen:
                        seen.add(key)
                        consolidated.append(p)
                self.memory.domain_patterns[domain] = consolidated[:30]

        # Ajustar learning rate por performance
        if self._review_count > 0:
            accuracy = self._correct_count / self._review_count
            if accuracy > 0.8:
                self._learning_rate = max(0.01, self._learning_rate * 0.9)  # Menos agressivo
            elif accuracy < 0.5:
                self._learning_rate = min(0.2, self._learning_rate * 1.5)  # Mais agressivo

        await asyncio.sleep(duration_seconds)
        self.state = AgentState.IDLE

        return {
            "consolidated_patterns": sum(len(p) for p in self.memory.domain_patterns.values()),
            "new_learning_rate": self._learning_rate,
            "accuracy": self._correct_count / max(1, self._review_count),
        }

    def get_agent_status(self) -> Dict:
        """Retorna status completo do agente."""
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "domain_expertise": self.domain_expertise,
            "confidence_model": self._confidence_model,
            "accuracy_model": self._accuracy_model,
            "review_count": self._review_count,
            "correct_count": self._correct_count,
            "accuracy": self._correct_count / max(1, self._review_count),
            "exploration_rate": self._exploration_rate,
            "learning_rate": self._learning_rate,
            "memory_size": len(self.memory.experiences),
            "error_patterns": dict(self.memory.error_patterns),
        }


class AgentOrchestrator:
    """Orquestra multiplos agentes sinteticos."""

    def __init__(self, qip_engine: Any):
        self.qip = qip_engine
        self.agents: Dict[str, SyntheticReviewerAgent] = {}
        self._task_assignments: Dict[str, str] = {}

    def create_agent(self, agent_id: str, domains: List[str]) -> SyntheticReviewerAgent:
        agent = SyntheticReviewerAgent(agent_id, self.qip, domains)
        self.agents[agent_id] = agent
        return agent

    async def assign_task(self, task_id: str, manifest: Dict, source_files: List[Tuple[str, str]],
                          dependencies: List[Dict], domain: str) -> Dict:
        """Atribui tarefa ao melhor agente por dominio."""
        # Selecionar agente com maior confianca no dominio
        best_agent = None
        best_confidence = -1.0

        for agent in self.agents.values():
            if domain in agent.domain_expertise:
                conf = agent._confidence_model.get(domain, 0.0)
                if conf > best_confidence:
                    best_confidence = conf
                    best_agent = agent

        if not best_agent:
            # Criar agente generico se nenhum especialista disponivel
            best_agent = self.create_agent(f"generic-{task_id}", [domain])

        self._task_assignments[task_id] = best_agent.agent_id

        # Executar analise
        result = await best_agent.analyze_package(manifest, source_files, dependencies, domain)

        return {
            "task_id": task_id,
            "agent_id": best_agent.agent_id,
            "assignment_confidence": best_confidence,
            "analysis": result,
        }

    async def process_feedback(self, task_id: str, final_decision: str) -> Dict:
        """Processa feedback de consenso para agente."""
        agent_id = self._task_assignments.get(task_id)
        if not agent_id or agent_id not in self.agents:
            return {"error": "Task not assigned to any agent"}

        agent = self.agents[agent_id]

        # Recuperar experiencia (simplificado)
        experience = ReviewExperience(
            task_id=task_id,
            package_name="unknown",
            domain="general",
            risk_score=0.5,
            vote="approve",
            final_decision=final_decision,
            was_correct=True,  # Simplificado
            confidence=0.8,
            rationale="Auto-generated",
            timestamp=time.time(),
        )

        return await agent.learn_from_feedback(experience)

    def get_orchestrator_status(self) -> Dict:
        return {
            "total_agents": len(self.agents),
            "agents": [a.get_agent_status() for a in self.agents.values()],
            "active_tasks": len(self._task_assignments),
        }