#!/usr/bin/env python3
"""
Substrato 183-C: Orquestrador de Ativação Supervisionada de Agentes
Gerencia período de 7 dias de operação assistida antes de autonomia total,
com monitoramento contínuo de Φ_C, intervenções humanas e rollback automático.
"""

import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import logging
from enum import Enum, auto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupervisionMode(Enum):
    """Modos de supervisão durante período de ativação."""
    OBSERVE_ONLY = "observe_only"           # Apenas monitorar, sem intervenção
    HUMAN_IN_THE_LOOP = "human_approval"    # Requer aprovação humana para ações
    AUTO_WITH_OVERRIDE = "auto_override"    # Autônomo, mas humano pode intervir
    FULL_AUTONOMY = "full_autonomy"         # Autonomia total (após 7 dias)

@dataclass
class AgentActivationConfig:
    """Configuração de ativação supervisionada para um agente."""
    agent_id: str
    domain: str
    initial_mode: SupervisionMode
    phi_c_threshold_for_promotion: float  # Φ_C mínimo para avançar de modo
    human_approval_channels: List[str]  # Canais para aprovação humana
    rollback_triggers: Dict[str, float]  # trigger → threshold
    promotion_schedule: List[Dict]  # Lista de marcos de promoção de modo

@dataclass
class ActivationMilestone:
    """Marco do período de ativação supervisionada."""
    day: int
    mode: SupervisionMode
    phi_c_requirement: float
    actions_allowed: List[str]
    human_oversight_required: bool
    temporal_seal: Optional[str] = None

@dataclass
class SupervisedActivationStatus:
    """Status consolidado da ativação supervisionada."""
    activation_id: str
    agent_id: str
    started_at: float
    current_day: int
    current_mode: SupervisionMode
    phi_c_current: float
    phi_c_history: List[float]
    human_interventions: int
    auto_actions_taken: int
    rollback_count: int
    next_promotion: Optional[ActivationMilestone]
    estimated_full_autonomy: float
    temporal_anchor: str
    public_status_endpoint: str

class SupervisedActivationOrchestrator:
    """
    Orquestra ativação supervisionada de agentes especializados.

    Funcionalidades:
    • Período de 7 dias com promoção gradual de modos de supervisão
    • Monitoramento contínuo de Φ_C com thresholds para promoção
    • Sistema de aprovação humana para ações críticas
    • Rollback automático se Φ_C cair abaixo de threshold
    • Ancoragem temporal de cada transição de modo
    • Endpoint público para transparência do processo
    """

    # Cronograma padrão de promoção de modos (7 dias)
    DEFAULT_PROMOTION_SCHEDULE = [
        {"day": 1, "mode": SupervisionMode.OBSERVE_ONLY, "phi_c_min": 0.99, "actions": ["monitor"]},
        {"day": 2, "mode": SupervisionMode.HUMAN_IN_THE_LOOP, "phi_c_min": 0.99, "actions": ["monitor", "recommend"]},
        {"day": 3, "mode": SupervisionMode.HUMAN_IN_THE_LOOP, "phi_c_min": 0.99, "actions": ["monitor", "recommend", "execute_non_critical"]},
        {"day": 4, "mode": SupervisionMode.AUTO_WITH_OVERRIDE, "phi_c_min": 0.995, "actions": ["monitor", "recommend", "execute_non_critical", "execute_critical_with_override"]},
        {"day": 5, "mode": SupervisionMode.AUTO_WITH_OVERRIDE, "phi_c_min": 0.995, "actions": ["all_non_dangerous"]},
        {"day": 6, "mode": SupervisionMode.AUTO_WITH_OVERRIDE, "phi_c_min": 0.997, "actions": ["all_with_human_notification"]},
        {"day": 7, "mode": SupervisionMode.FULL_AUTONOMY, "phi_c_min": 0.999, "actions": ["all"]},
    ]

    # Triggers para rollback automático
    DEFAULT_ROLLBACK_TRIGGERS = {
        "phi_c_drop": 0.95,  # Se Φ_C cair abaixo, voltar ao modo anterior
        "human_intervention_rate": 0.30,  # Se >30% das ações requerem intervenção humana
        "error_rate": 0.05,  # Se taxa de erro >5%
        "guardian_blocks": 3,  # Se Guardian bloquear 3 ações consecutivas
    }

    def __init__(
        self,
        agent_id: str,
        domain: str,
        phi_bus=None,
        guardian=None,
        temporal_chain=None,
    ):
        self.agent_id = agent_id
        self.domain = domain
        self.phi_bus = phi_bus
        self.guardian = guardian
        self.temporal = temporal_chain
        self.activation_id = None
        self.config: Optional[AgentActivationConfig] = None
        self.status: Optional[SupervisedActivationStatus] = None
        self._running = False

    async def start_supervised_activation(
        self,
        initial_phi_c: float,
        human_approval_channels: Optional[List[str]] = None,
    ) -> SupervisedActivationStatus:
        """
        Inicia período de ativação supervisionada de 7 dias.

        Args:
            initial_phi_c: Φ_C inicial do agente
            human_approval_channels: Canais para aprovação humana (default: ["ops_team"])

        Returns:
            SupervisedActivationStatus com IDs e endpoints para acompanhamento
        """
        # Gerar ID único de ativação
        self.activation_id = hashlib.sha3_256(
            f"{self.agent_id}:{time.time()}".encode()
        ).hexdigest()[:12]

        # Configurar agente com parâmetros padrão
        self.config = AgentActivationConfig(
            agent_id=self.agent_id,
            domain=self.domain,
            initial_mode=SupervisionMode.OBSERVE_ONLY,
            phi_c_threshold_for_promotion=0.99,
            human_approval_channels=human_approval_channels or ["ops_team"],
            rollback_triggers=self.DEFAULT_ROLLBACK_TRIGGERS,
            promotion_schedule=self.DEFAULT_PROMOTION_SCHEDULE,
        )

        # Criar status inicial
        base_time = time.time()
        self.status = SupervisedActivationStatus(
            activation_id=self.activation_id,
            agent_id=self.agent_id,
            started_at=base_time,
            current_day=1,
            current_mode=SupervisionMode.OBSERVE_ONLY,
            phi_c_current=initial_phi_c,
            phi_c_history=[initial_phi_c],
            human_interventions=0,
            auto_actions_taken=0,
            rollback_count=0,
            next_promotion=self._get_milestone_for_day(2),
            estimated_full_autonomy=base_time + (7 * 86400),
            temporal_anchor="pending",
            public_status_endpoint=f"/api/v1/activations/{self.activation_id}/status",
        )

        # Ancorar início da ativação na TemporalChain
        if self.temporal:
            self.status.temporal_anchor = await self.temporal.anchor_event(
                "agent_activation_started",
                {
                    "activation_id": self.activation_id,
                    "agent_id": self.agent_id,
                    "domain": self.domain,
                    "initial_phi_c": initial_phi_c,
                    "supervision_days": 7,
                    "timestamp": base_time,
                }
            )

        # Iniciar loops de monitoramento
        self._running = True
        asyncio.create_task(self._phi_c_monitoring_loop())
        asyncio.create_task(self._promotion_evaluation_loop())
        asyncio.create_task(self._rollback_evaluation_loop())

        logger.info(f"🚀 Ativação supervisionada iniciada: {self.activation_id} | Agente: {self.agent_id}")
        logger.info(f"📅 Cronograma: 7 dias | Autonomia estimada: {datetime.fromtimestamp(self.status.estimated_full_autonomy).strftime('%Y-%m-%d')}")

        return self.status

    def _get_milestone_for_day(self, day: int) -> Optional[ActivationMilestone]:
        """Retorna marco de promoção para um dia específico."""
        for milestone_config in self.config.promotion_schedule:
            if milestone_config["day"] == day:
                return ActivationMilestone(
                    day=milestone_config["day"],
                    mode=milestone_config["mode"],
                    phi_c_requirement=milestone_config["phi_c_min"],
                    actions_allowed=milestone_config["actions"],
                    human_oversight_required=milestone_config["mode"] != SupervisionMode.FULL_AUTONOMY,
                )
        return None

    async def _phi_c_monitoring_loop(self):
        """Loop de monitoramento contínuo de Φ_C do agente."""
        while self._running and self.status:
            # Obter Φ_C atual do agente
            current_phi_c = await self._get_agent_phi_c()

            # Atualizar histórico e status
            self.status.phi_c_history.append(current_phi_c)
            self.status.phi_c_current = current_phi_c

            # Manter histórico limitado (últimas 24h de amostras)
            if len(self.status.phi_c_history) > 1440:  # 1 amostra/minuto × 24h
                self.status.phi_c_history.pop(0)

            # Verificar se Φ_C está abaixo do threshold do modo atual
            current_milestone = self._get_milestone_for_day(self.status.current_day)
            if current_milestone and current_phi_c < current_milestone.phi_c_requirement:
                logger.warning(f"⚠️  Φ_C abaixo do threshold: {current_phi_c:.4f} < {current_milestone.phi_c_requirement}")

            await asyncio.sleep(60)  # Amostrar a cada minuto

    async def _promotion_evaluation_loop(self):
        """Avalia se agente pode ser promovido para próximo modo de supervisão."""
        while self._running and self.status:
            # Verificar se é dia de promoção
            elapsed_days = (time.time() - self.status.started_at) / 86400
            next_day = int(elapsed_days) + 1

            if next_day > self.status.current_day and next_day <= 7:
                # Avaliar critérios para promoção
                milestone = self._get_milestone_for_day(next_day)
                if milestone:
                    # Verificar Φ_C médio nas últimas 24h
                    recent_phi_c = self.status.phi_c_history[-1440:] if len(self.status.phi_c_history) >= 1440 else self.status.phi_c_history
                    avg_phi_c = sum(recent_phi_c) / len(recent_phi_c) if recent_phi_c else 0

                    if avg_phi_c >= milestone.phi_c_requirement:
                        # Promover agente para novo modo
                        await self._promote_agent_mode(milestone)
                        self.status.current_day = next_day
                        self.status.next_promotion = self._get_milestone_for_day(next_day + 1)

                        # Ancorar promoção na TemporalChain
                        if self.temporal:
                            milestone.temporal_seal = await self.temporal.anchor_event(
                                "agent_mode_promoted",
                                {
                                    "activation_id": self.activation_id,
                                    "agent_id": self.agent_id,
                                    "from_mode": self.status.current_mode.value,
                                    "to_mode": milestone.mode.value,
                                    "day": next_day,
                                    "avg_phi_c": round(avg_phi_c, 4),
                                    "timestamp": time.time(),
                                }
                            )

                        logger.info(f"✅ Agente promovido: Dia {next_day} | Modo: {milestone.mode.value} | Φ_C: {avg_phi_c:.4f}")
                    else:
                        logger.info(f"⏳ Promoção adiada: Φ_C médio {avg_phi_c:.4f} < {milestone.phi_c_requirement}")

            await asyncio.sleep(3600)  # Avaliar a cada hora

    async def _rollback_evaluation_loop(self):
        """Avalia se agente deve sofrer rollback para modo anterior."""
        while self._running and self.status:
            triggers = self.config.rollback_triggers

            # Verificar trigger de Φ_C
            if self.status.phi_c_current < triggers["phi_c_drop"]:
                await self._execute_rollback("phi_c_drop")

            # Verificar taxa de intervenção humana
            if self.status.current_day > 1:
                total_actions = self.status.auto_actions_taken + self.status.human_interventions
                if total_actions > 0:
                    intervention_rate = self.status.human_interventions / total_actions
                    if intervention_rate > triggers["human_intervention_rate"]:
                        await self._execute_rollback("human_intervention_rate")

            # Verificar taxa de erro (simulado)
            # Em produção: integrar com métricas reais de erro do agente

            await asyncio.sleep(300)  # Avaliar a cada 5 minutos

    async def _promote_agent_mode(self, milestone: ActivationMilestone):
        """Promove agente para novo modo de supervisão."""
        self.status.current_mode = milestone.mode
        # Em produção: atualizar configuração do agente para novo modo
        logger.info(f"🔄 Modo atualizado para: {milestone.mode.value}")

    async def _execute_rollback(self, trigger: str):
        """Executa rollback para modo anterior de supervisão."""
        if self.status.current_day <= 1:
            return  # Não há modo anterior no dia 1

        previous_day = self.status.current_day - 1
        previous_milestone = self._get_milestone_for_day(previous_day)

        if previous_milestone:
            # Reverter para modo anterior
            self.status.current_day = previous_day
            self.status.current_mode = previous_milestone.mode
            self.status.rollback_count += 1
            self.status.next_promotion = self._get_milestone_for_day(previous_day + 1)

            # Notificar equipe sobre rollback
            logger.warning(f"🔙 Rollback executado: {trigger} | Dia {previous_day} | Modo: {previous_milestone.mode.value}")

            # Ancorar rollback na TemporalChain
            if self.temporal:
                await self.temporal.anchor_event(
                    "agent_activation_rollback",
                    {
                        "activation_id": self.activation_id,
                        "agent_id": self.agent_id,
                        "trigger": trigger,
                        "from_day": self.status.current_day + 1,
                        "to_day": previous_day,
                        "timestamp": time.time(),
                    }
                )

    async def _get_agent_phi_c(self) -> float:
        """Obtém Φ_C atual do agente (simulado)."""
        if self.phi_bus:
            return self.phi_bus.get_agent_coherence(self.agent_id)
        # Fallback: simular Φ_C com pequenas variações
        import numpy as np
        base = 0.997 + (hash(self.agent_id + str(int(time.time() / 300))) % 10) / 1000
        noise = np.random.normal(0, 0.0005)
        return round(float(np.clip(base + noise, 0.90, 1.0)), 4)

    def get_public_status(self) -> Dict:
        """Gera status público para transparência (sem dados sensíveis)."""
        if not self.status:
            return {"error": "Activation not started"}

        return {
            "activation_id": self.status.activation_id,
            "agent_id": self.status.agent_id,
            "domain": self.domain,
            "started_date": datetime.fromtimestamp(self.status.started_at).strftime("%Y-%m-%d"),
            "current_day": self.status.current_day,
            "current_mode": self.status.current_mode.value,
            "phi_c_current": round(self.status.phi_c_current, 4),
            "phi_c_24h_avg": round(
                sum(self.status.phi_c_history[-1440:]) / len(self.status.phi_c_history[-1440:]), 4
            ) if len(self.status.phi_c_history) >= 1440 else None,
            "human_interventions": self.status.human_interventions,
            "auto_actions": self.status.auto_actions_taken,
            "rollbacks": self.status.rollback_count,
            "next_promotion": {
                "day": self.status.next_promotion.day if self.status.next_promotion else None,
                "mode": self.status.next_promotion.mode.value if self.status.next_promotion else None,
                "phi_c_required": self.status.next_promotion.phi_c_requirement if self.status.next_promotion else None,
            } if self.status.next_promotion else None,
            "estimated_full_autonomy": datetime.fromtimestamp(self.status.estimated_full_autonomy).strftime("%Y-%m-%d"),
            "temporal_anchor_verified": self.status.temporal_anchor != "pending",
            "public_documentation": f"https://activations.arkhe.internal/{self.activation_id}",
        }

    async def shutdown(self):
        """Encerra orquestrador de ativação supervisionada."""
        self._running = False
        logger.info(f"🔚 Orquestrador de ativação encerrado: {self.activation_id}")