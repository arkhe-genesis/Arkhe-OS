"""
rollback/emergency_controller.py
Controlador de rollback de emergência — reflexos de sobrevivência da Catedral.
"""

import asyncio
import time
import hashlib
import json
from typing import Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import logging

from cathedral_organism import CathedralOrganism, OrganismState, OrganismPulse
from transition_dual_mode import MigrationPhase, TransitionManager

logger = logging.getLogger(__name__)

class RollbackTrigger(Enum):
    """Gatilhos de rollback automático."""
    OMEGA_CRITICAL = auto()           # Ω_score abaixo do threshold
    LATENCY_SPIKE = auto()            # Latência acima do limite
    ERROR_RATE_HIGH = auto()          # Taxa de erro elevada
    CONSENSUS_TIMEOUT = auto()        # Timeout em consenso
    FALSE_POSITIVE = auto()           # Falso positivo acima do limite
    DIVERGENCE = auto()               # Divergência simulação vs produção
    MANUAL = auto()                   # Rollback manual solicitado

@dataclass
class RollbackEvent:
    """Evento de rollback para audit trail imutável."""
    event_id: str
    timestamp: float
    from_phase: MigrationPhase
    to_phase: MigrationPhase
    trigger: RollbackTrigger
    subsystem: str
    metrics_at_trigger: Dict[str, float]
    action_taken: str
    duration_ms: float
    diagnosed: bool = False

class EmergencyRollbackController:
    """
    Controlador de rollback de emergência.
    Monitora métricas em tempo real e executa reversão automática em <100ms.
    """

    # Thresholds por fase de transição
    PHASE_THRESHOLDS: Dict[MigrationPhase, Dict[str, Union[float, int]]] = {
        MigrationPhase.PLANETARY: {
            "omega_min": 0.95,
            "latency_max_ms": 500,
            "error_rate_max": 0.01,
            "duration_trigger_s": 60,
        },
        MigrationPhase.FEDERATED: {
            "omega_min": 0.90,
            "latency_max_ms": 400,
            "error_rate_max": 0.02,
            "duration_trigger_s": 60,
        },
        MigrationPhase.AUTONOMOUS: {
            "omega_min": 0.85,
            "latency_max_ms": 200,
            "error_rate_max": 0.03,
            "duration_trigger_s": 60,
        },
        MigrationPhase.ACTIVE: {
            "omega_min": 0.80,
            "latency_max_ms": 150,
            "error_rate_max": 0.05,
            "duration_trigger_s": 60,
        },
        MigrationPhase.HYBRID: {
            "omega_min": 0.90,
            "latency_max_ms": 100,
            "error_rate_max": 0.01,  # Falso positivo
            "duration_trigger_s": 3600,  # 1h para FP
        },
        MigrationPhase.SHADOW: {
            "omega_min": 0.95,
            "latency_max_ms": 50,
            "error_rate_max": 0.10,  # Acurácia
            "duration_trigger_s": 7200,  # 2h para acurácia
        },
    }

    # Ações de rollback por subsistema
    SUBSYSTEM_ACTIONS: Dict[str, Callable[[], bool]] = {}

    def __init__(
        self,
        organism: CathedralOrganism,
        transition_manager: TransitionManager,
        codex_client=None,
    ):
        self.organism = organism
        self.transition = transition_manager
        self.codex = codex_client

        # Estado de monitoramento
        self._monitoring_task: Optional[asyncio.Task] = None
        self._violation_start: Dict[str, float] = {}
        self._last_healthy_metrics: Dict[str, Dict] = {}

        # Histórico de rollbacks para auditoria
        self.rollback_log: List[RollbackEvent] = []

        # Flag de emergência
        self._emergency_mode = False

        # Callbacks de rollback por subsistema
        self._rollback_actions: Dict[str, Callable[[], bool]] = {}

    def register_rollback_action(self, subsystem: str, action: Callable[[], bool]):
        """Registra ação de rollback para um subsistema."""
        self._rollback_actions[subsystem] = action
        logger.info(f"[Rollback] Ação registrada para {subsystem}")

    async def start_monitoring(self, check_interval_s: float = 5.0):
        """Inicia monitoramento contínuo de triggers de rollback."""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("[Rollback] Monitoramento já está ativo")
            return

        self._monitoring_task = asyncio.create_task(
            self._monitor_loop(check_interval_s)
        )
        logger.info("[Rollback] Monitoramento de emergência iniciado")

    async def stop_monitoring(self):
        """Para o monitoramento de rollback."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("[Rollback] Monitoramento de emergência parado")

    async def _monitor_loop(self, check_interval_s: float):
        """Loop principal de monitoramento de triggers."""
        while True:
            try:
                if not self.organism.is_alive:
                    await asyncio.sleep(check_interval_s)
                    continue

                current_phase = self.transition.current_phase
                if current_phase == MigrationPhase.SANDBOX:
                    await asyncio.sleep(check_interval_s)
                    continue

                # Coleta métricas atuais
                pulse = self.organism.last_pulse
                if not pulse:
                    await asyncio.sleep(check_interval_s)
                    continue

                metrics = {
                    "omega": pulse.global_omega,
                    "latency_ms": pulse.cross_region_latency_ms,
                    "error_rate": 1 - pulse.subsystem_health.get("consensus", 1.0),
                    "false_positive_rate": pulse.subsystem_health.get("security_fp_rate", 0.0),
                }

                # Verifica thresholds da fase atual
                thresholds = self.PHASE_THRESHOLDS.get(current_phase)
                if thresholds:
                    violation = self._check_violation(metrics, thresholds)
                    if violation:
                        await self._handle_violation(
                            violation, metrics, current_phase, thresholds
                        )
                    else:
                        # Reset timer se métricas recuperaram
                        for key in list(self._violation_start.keys()):
                            if key.startswith(f"{current_phase.name}_"):
                                del self._violation_start[key]

                await asyncio.sleep(check_interval_s)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Rollback] Erro no monitoramento: {e}")
                await asyncio.sleep(5.0)  # Backoff em caso de erro

    def _check_violation(
        self,
        metrics: Dict[str, float],
        thresholds: Dict[str, Union[float, int]]
    ) -> Optional[RollbackTrigger]:
        """Verifica se métricas violam thresholds. Retorna trigger ou None."""
        if metrics["omega"] < thresholds["omega_min"]:
            return RollbackTrigger.OMEGA_CRITICAL
        if metrics["latency_ms"] > thresholds["latency_max_ms"]:
            return RollbackTrigger.LATENCY_SPIKE
        if metrics["error_rate"] > thresholds["error_rate_max"]:
            return RollbackTrigger.ERROR_RATE_HIGH
        if metrics.get("false_positive_rate", 0) > thresholds.get("error_rate_max", 1.0):
            return RollbackTrigger.FALSE_POSITIVE
        return None

    async def _handle_violation(
        self,
        trigger: RollbackTrigger,
        metrics: Dict[str, float],
        phase: MigrationPhase,
        thresholds: Dict[str, Union[float, int]]
    ):
        """Lida com violação de threshold — decide se executa rollback."""
        trigger_key = f"{phase.name}_{trigger.name}"
        now = time.time()

        # Inicia ou atualiza timer de violação
        if trigger_key not in self._violation_start:
            self._violation_start[trigger_key] = now
            self._last_healthy_metrics[trigger_key] = metrics.copy()
            logger.warning(f"[Rollback] Violação detectada: {trigger_key}")
            return

        # Verifica persistência da violação
        duration = now - self._violation_start[trigger_key]
        if duration >= thresholds["duration_trigger_s"]:
            # Violação persistente — executa rollback
            await self._execute_rollback(phase, trigger, metrics)
            # Reset timer após execução
            del self._violation_start[trigger_key]
        else:
            logger.debug(f"[Rollback] Violação persistente por {duration:.1f}s/{thresholds['duration_trigger_s']}s")

    async def _execute_rollback(
        self,
        from_phase: MigrationPhase,
        trigger: RollbackTrigger,
        metrics: Dict[str, float]
    ):
        """Executa rollback para fase anterior."""
        start_time = time.time()

        # Determina fase anterior
        previous_phase = self._get_previous_phase(from_phase)
        if previous_phase is None:
            logger.critical("[Rollback] Não há fase anterior. Rollback total necessário.")
            await self._full_shutdown_to_simulation()
            return

        logger.critical(
            f"[Rollback] 🚨 EMERGÊNCIA: {from_phase.name} → {previous_phase.name} "
            f"(trigger: {trigger.name}, Ω={metrics['omega']:.2f})"
        )

        # 1. Entra em modo de emergência
        self._emergency_mode = True
        old_state = self.organism.state
        self.organism.state = OrganismState.RECOVERING

        # 2. Executa rollback actions por subsistema
        actions_executed = []
        for subsystem, action in self._rollback_actions.items():
            try:
                start = time.time()
                success = action()
                elapsed = (time.time() - start) * 1000
                if success:
                    actions_executed.append(f"{subsystem} ({elapsed:.1f}ms)")
                    logger.info(f"[Rollback] ✓ {subsystem}")
                else:
                    logger.error(f"[Rollback] ✗ {subsystem} falhou")
            except Exception as e:
                logger.error(f"[Rollback] ✗ {subsystem} exceção: {e}")

        # 3. Atualiza fase no TransitionManager
        self.transition.current_phase = previous_phase

        # 4. Reabilita simulação para subsistemas afetados
        await self._re_enable_simulation_for_phase(previous_phase)

        # 5. Registra evento de rollback
        elapsed_ms = (time.time() - start_time) * 1000
        event = RollbackEvent(
            event_id=f"rb_{hashlib.sha256(f'{time.time()}{trigger.name}'.encode()).hexdigest()[:12]}",
            timestamp=time.time(),
            from_phase=from_phase,
            to_phase=previous_phase,
            trigger=trigger,
            subsystem="global",
            metrics_at_trigger=metrics,
            action_taken=f"Rollback automático: {', '.join(actions_executed)}",
            duration_ms=elapsed_ms,
            diagnosed=False,
        )
        self.rollback_log.append(event)

        # 6. Ancora no Códice para auditoria
        if self.codex:
            await self._anchor_rollback_event(event)

        # 7. Notifica equipe
        await self._notify_rollback(event)

        # 8. Inicia diagnóstico automático
        diagnosis = await self._auto_diagnose()
        event.diagnosed = True

        # 9. Sai do modo emergência (mas mantém recovering até Ω recuperar)
        self._emergency_mode = False
        self.organism.state = old_state

        logger.critical(f"[Rollback] Rollback concluído em {elapsed_ms:.1f}ms")

    def _get_previous_phase(self, phase: MigrationPhase) -> Optional[MigrationPhase]:
        """Retorna fase anterior na sequência de transição."""
        sequence = [
            MigrationPhase.SANDBOX,
            MigrationPhase.SHADOW,
            MigrationPhase.HYBRID,
            MigrationPhase.ACTIVE,
            MigrationPhase.AUTONOMOUS,
            MigrationPhase.FEDERATED,
            MigrationPhase.PLANETARY,
        ]
        try:
            idx = sequence.index(phase)
            return sequence[idx - 1] if idx > 0 else None
        except ValueError:
            return None

    async def _re_enable_simulation_for_phase(self, phase: MigrationPhase):
        """Reabilita simulação conforme necessário para a fase."""
        if phase in [MigrationPhase.SHADOW, MigrationPhase.HYBRID]:
            logger.info("[Rollback] Simulação reabilitada para validação dual-mode")
            # Em produção: ativar shadow mode nos subsistemas afetados
        elif phase == MigrationPhase.PREPARATION:
            logger.info("[Rollback] Modo preparação: apenas health checks ativos")

    async def _full_shutdown_to_simulation(self):
        """Rollback total: desliga produção, retorna à simulação."""
        logger.critical("[Rollback] ☠️ ROLLBACK TOTAL: Desligando produção...")

        # Para todos os subsistemas
        await self.organism.stop()

        # Limpa estado de produção
        self.transition.current_phase = MigrationPhase.SANDBOX

        # Notifica equipe
        await self._notify_rollback(
            RollbackEvent(
                event_id=f"rb_total_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:12]}",
                timestamp=time.time(),
                from_phase=MigrationPhase.PLANETARY,
                to_phase=MigrationPhase.SANDBOX,
                trigger=RollbackTrigger.OMEGA_CRITICAL,
                subsystem="global",
                metrics_at_trigger={"omega": 0.0},
                action_taken="SHUTDOWN TOTAL para simulação",
                duration_ms=0.0,
                diagnosed=False,
            )
        )

    async def _anchor_rollback_event(self, event: RollbackEvent):
        """Ancora evento de rollback no Códice para auditoria imutável."""
        event_data = asdict(event)
        event_hash = hashlib.sha256(
            json.dumps(event_data, sort_keys=True, default=str).encode()
        ).hexdigest()

        await self.codex.store_artifact(
            artifact_id=f"rollback_{event.event_id}",
            content_hash=event_hash,
            metadata={
                "type": "rollback_event",
                "from_phase": event.from_phase.name,
                "to_phase": event.to_phase.name,
                "trigger": event.trigger.name,
                "duration_ms": event.duration_ms,
                "diagnosed": event.diagnosed,
            }
        )

    async def _notify_rollback(self, event: RollbackEvent):
        """Notifica equipe sobre rollback via canais configurados."""
        message = f"""
🚨 ROLLBACK DE EMERGÊNCIA EXECUTADO 🚨

Fase: {event.from_phase.name} → {event.to_phase.name}
Trigger: {event.trigger.name}
Timestamp: {event.timestamp}
Ω no momento: {event.metrics_at_trigger.get('omega', 'N/A')}
Duração: {event.duration_ms:.1f}ms
Ação: {event.action_taken}
Diagnóstico: {'Concluído' if event.diagnosed else 'Pendente'}

Próxima tentativa de avanço BLOQUEADA até correção manual.
Consulte o Códice para detalhes: rollback_{event.event_id}
"""
        # Em produção: envia para PagerDuty + Slack + Email
        logger.critical(message)

    async def _auto_diagnose(self) -> Dict[str, str]:
        """Executa diagnóstico automático pós-rollback."""
        issues = self.organism.diagnose()

        if issues:
            logger.info("[Rollback] Diagnóstico automático encontrou problemas:")
            for system, issue in issues.items():
                logger.info(f"  • {system}: {issue}")
        else:
            logger.info("[Rollback] Diagnóstico: nenhum problema crítico detectado")

        # Coleta logs dos últimos 5 minutos para análise forense
        # Em produção: consulta Loki/ELK
        logger.info("[Rollback] Logs coletados para análise forense")

        return issues

    async def manual_rollback(
        self,
        target_phase: MigrationPhase,
        reason: str,
        subsystem: Optional[str] = None
    ) -> bool:
        """Rollback manual (para uso humano em emergência)."""
        current = self.transition.current_phase

        if target_phase.value >= current.value:
            logger.error(f"[Rollback] Manual: target {target_phase.name} não é anterior a {current.name}")
            return False

        logger.warning(f"[Rollback] Manual solicitado: {current.name} → {target_phase.name}")
        logger.warning(f"[Rollback] Razão: {reason}")
        if subsystem:
            logger.warning(f"[Rollback] Subsistema afetado: {subsystem}")

        # Força rollback múltiplas fases se necessário
        while self.transition.current_phase != target_phase:
            prev = self._get_previous_phase(self.transition.current_phase)
            if prev is None:
                break

            await self._execute_rollback(
                self.transition.current_phase,
                RollbackTrigger.MANUAL,
                {"omega": self.organism.last_pulse.global_omega if self.organism.last_pulse else 0.5}
            )

        return True

    def get_rollback_report(self) -> Dict:
        """Gera relatório de rollbacks executados para auditoria."""
        if not self.rollback_log:
            return {"total_rollbacks": 0, "recent_rollbacks": []}

        return {
            "total_rollbacks": len(self.rollback_log),
            "by_severity": {
                trigger.name: len([r for r in self.rollback_log if r.trigger == trigger])
                for trigger in RollbackTrigger
            },
            "by_phase": {
                phase.name: len([r for r in self.rollback_log if r.from_phase == phase])
                for phase in MigrationPhase
            },
            "avg_duration_ms": sum(r.duration_ms for r in self.rollback_log) / len(self.rollback_log),
            "recent_rollbacks": [asdict(r) for r in self.rollback_log[-10:]],
            "last_rollback": asdict(self.rollback_log[-1]) if self.rollback_log else None,
        }
