"""
cathedral_organism/organism.py
O organismo vivo da Catedral — coração pulsante da coordenação autônoma.
"""

import asyncio
import time
import hashlib
import json
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import logging

from .pulse import OrganismPulse, NodeHealthPulse
from .health import HealthMonitor, VitalityMetrics
from .state import OrganismState, StateTransition

logger = logging.getLogger(__name__)

class CathedralOrganism:
    """
    O organismo vivo da Catedral.
    Implementa as Sete Leis da Coordenação Autônoma.
    """

    # Configurações padrão
    DEFAULT_CONFIG = {
        "pulse_interval_seconds": 10,
        "omega_threshold_healthy": 0.85,
        "omega_threshold_critical": 0.70,
        "gossip_fanout": 3,
        "consensus_timeout_seconds": 30,
        "rollback_enabled": True,
    }

    def __init__(
        self,
        region_id: str,
        config: Optional[Dict] = None,
        shard_manager=None,
        consensus_engine=None,
        health_monitor=None,
        rollback_controller=None,
    ):
        self.region_id = region_id
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

        # Componentes do organismo
        self.shard_manager = shard_manager
        self.consensus_engine = consensus_engine
        self.health_monitor = health_monitor or HealthMonitor()
        self.rollback_controller = rollback_controller

        # Estado interno
        self._state = OrganismState.INITIALIZING
        self._last_pulse: Optional[OrganismPulse] = None
        self._pulse_history: List[OrganismPulse] = []
        self._peers: Dict[str, NodeHealthPulse] = {}

        # Callbacks para as Sete Leis
        self._on_pulse_emit: Optional[Callable] = None
        self._on_criticality_classified: Optional[Callable] = None
        self._on_authority_flowed: Optional[Callable] = None
        self._on_gossip_received: Optional[Callable] = None
        self._on_topology_adapted: Optional[Callable] = None
        self._on_frontier_synced: Optional[Callable] = None
        self._on_phase_advanced: Optional[Callable] = None

        # Flag de execução
        self._running = False
        self._coordination_task: Optional[asyncio.Task] = None

    @property
    def state(self) -> OrganismState:
        return self._state

    @state.setter
    def state(self, new_state: OrganismState):
        old_state = self._state
        self._state = new_state
        logger.info(f"[Organism] State transition: {old_state.name} → {new_state.name}")

    @property
    def last_pulse(self) -> Optional[OrganismPulse]:
        return self._last_pulse

    @property
    def is_alive(self) -> bool:
        return self._running and self._state != OrganismState.DEAD

    @property
    def is_healthy(self) -> bool:
        if not self._last_pulse:
            return False
        return self._last_pulse.global_omega >= self.config["omega_threshold_healthy"]

    async def start(self):
        """Inicia o organismo — o coração começa a bater."""
        if self._running:
            logger.warning("[Organism] Já está em execução")
            return

        logger.info(f"[Organism] Iniciando organismo na região {self.region_id}")
        self._running = True
        self.state = OrganismState.INITIALIZING

        # Inicializa componentes
        await self._initialize_components()

        # Inicia loop de coordenação autônoma
        self._coordination_task = asyncio.create_task(self._coordination_loop())

        # Inicia monitor de rollback se habilitado
        if self.config["rollback_enabled"] and self.rollback_controller:
            await self.rollback_controller.start_monitoring()

        self.state = OrganismState.RUNNING
        logger.info(f"[Organism] Organismo {self.region_id} operacional")

    async def stop(self):
        """Para o organismo — o coração para de bater (graceful shutdown)."""
        if not self._running:
            return

        logger.info(f"[Organism] Parando organismo {self.region_id}")
        self._running = False
        self.state = OrganismState.SHUTTING_DOWN

        # Para loop de coordenação
        if self._coordination_task:
            self._coordination_task.cancel()
            try:
                await self._coordination_task
            except asyncio.CancelledError:
                pass

        # Para monitor de rollback
        if self.rollback_controller:
            await self.rollback_controller.stop_monitoring()

        # Finaliza componentes
        await self._finalize_components()

        self.state = OrganismState.STOPPED
        logger.info(f"[Organism] Organismo {self.region_id} parado")

    async def _initialize_components(self):
        """Inicializa todos os componentes do organismo."""
        # Health check inicial
        await self.health_monitor.run_full_check()

        # Conecta ao shard manager
        if self.shard_manager:
            await self.shard_manager.connect(region_id=self.region_id)

        # Conecta ao consensus engine
        if self.consensus_engine:
            await self.consensus_engine.join_mesh(region_id=self.region_id)

        # Registra callbacks de rollback
        if self.rollback_controller:
            self._register_rollback_callbacks()

    async def _finalize_components(self):
        """Finaliza todos os componentes do organismo."""
        if self.consensus_engine:
            await self.consensus_engine.leave_mesh()

        if self.shard_manager:
            await self.shard_manager.disconnect()

    def _register_rollback_callbacks(self):
        """Registra ações de rollback para subsistemas críticos."""
        if not self.rollback_controller:
            return

        # Rollback para consenso quântico
        self.rollback_controller.register_rollback_action(
            "quantum_consensus",
            lambda: self.consensus_engine.disable_global_quorum() if self.consensus_engine else True
        )

        # Rollback para rebalanceamento dinâmico
        self.rollback_controller.register_rollback_action(
            "dynamic_rebalancer",
            lambda: self.shard_manager.freeze_migrations() if self.shard_manager else True
        )

        # Rollback para VigilAdapter
        self.rollback_controller.register_rollback_action(
            "vigil_adapter",
            lambda: self._set_vigil_mode("alert_only")
        )

    async def _coordination_loop(self):
        """
        Loop universal de coordenação autônoma.
        Implementa as Sete Leis em ciclo perpétuo.
        """
        while self._running:
            try:
                # LEI I: Emitir pulso de saúde
                pulse = await self._emit_health_pulse()

                # LEI IV: Disseminar via gossip
                peer_pulses = await self._gossip_exchange(pulse)

                # LEI V: Adaptar topologia se for o mais saudável
                if self._is_healthiest_among(peer_pulses):
                    await self._adapt_topology()

                # LEI II + III: Processar tarefas por criticidade
                await self._process_tasks_by_criticality()

                # LEI VI: Sincronizar fronteiras com regiões federadas
                await self._sync_frontiers()

                # LEI VII: Avançar fase de transição se aplicável
                await self._advance_transition_phase()

                # Aguarda próximo ciclo
                await asyncio.sleep(self.config["pulse_interval_seconds"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Organism] Erro no loop de coordenação: {e}")
                await asyncio.sleep(1.0)  # Backoff

    async def _emit_health_pulse(self) -> OrganismPulse:
        """LEI I: Calcula e emite pulso de saúde do organismo."""
        # Coleta métricas locais
        local_metrics = await self.health_monitor.collect_metrics()

        # Calcula Ω_score local
        local_omega = self.health_monitor.calculate_omega_score(local_metrics)

        # Coleta métricas de consenso (se disponível)
        consensus_metrics = {}
        if self.consensus_engine:
            consensus_metrics = await self.consensus_engine.get_health_metrics()

        # Cria pulso do organismo
        pulse = OrganismPulse(
            region_id=self.region_id,
            timestamp=time.time(),
            local_omega=local_omega,
            global_omega=local_omega,  # Será atualizado via gossip
            subsystem_health={
                "shard_manager": local_metrics.get("shard_health", 1.0),
                "consensus": consensus_metrics.get("health", 1.0),
                "security": local_metrics.get("security_health", 1.0),
                "observability": local_metrics.get("observability_health", 1.0),
            },
            cross_region_latency_ms=await self._measure_cross_region_latency(),
            shard_count=self.shard_manager.get_shard_count() if self.shard_manager else 0,
            pending_tasks=len(await self._get_pending_tasks()),
        )

        # Atualiza estado interno
        self._last_pulse = pulse
        self._pulse_history.append(pulse)

        # Mantém histórico limitado
        if len(self._pulse_history) > 100:
            self._pulse_history.pop(0)

        # Callback opcional
        if self._on_pulse_emit:
            await self._on_pulse_emit(pulse)

        logger.debug(f"[Organism] Pulse emitido: Ω={local_omega:.3f}")
        return pulse

    async def _gossip_exchange(self, my_pulse: OrganismPulse) -> Dict[str, NodeHealthPulse]:
        """LEI IV: Dissemina pulso via gossip e coleta pulsos de pares."""
        if not self.consensus_engine:
            return {}

        # Envia meu pulso para a malha
        await self.consensus_engine.gossip_publish(my_pulse)

        # Recebe pulsos de pares (com vetor de relógio para causalidade)
        peer_pulses = await self.consensus_engine.gossip_subscribe(
            fanout=self.config["gossip_fanout"],
            timeout_seconds=5.0
        )

        # Atualiza cache de pares
        for peer_id, peer_pulse in peer_pulses.items():
            self._peers[peer_id] = peer_pulse

        # Calcula Ω_global como média ponderada
        if peer_pulses:
            all_omegas = [my_pulse.local_omega] + [p.omega for p in peer_pulses.values()]
            self._last_pulse.global_omega = sum(all_omegas) / len(all_omegas)

        # Callback opcional
        if self._on_gossip_received:
            await self._on_gossip_received(peer_pulses)

        return peer_pulses

    def _is_healthiest_among(self, peer_pulses: Dict[str, NodeHealthPulse]) -> bool:
        """Verifica se este organismo é o mais saudável entre seus pares."""
        if not peer_pulses:
            return True

        my_omega = self._last_pulse.local_omega if self._last_pulse else 0
        peer_omegas = [p.omega for p in peer_pulses.values()]

        return my_omega >= max(peer_omegas)

    async def _adapt_topology(self):
        """LEI V: Adapta topologia migrando shards para balancear carga."""
        if not self.shard_manager:
            return

        # Avalia migrações necessárias
        migrations = await self.shard_manager.evaluate_migrations(
            current_load=self._get_current_load(),
            peer_loads={pid: p.load for pid, p in self._peers.items()}
        )

        # Executa migrações zero-downtime
        for shard_id, target_region in migrations:
            logger.info(f"[Organism] Migrando shard {shard_id} → {target_region}")
            await self.shard_manager.migrate_shard_zero_downtime(
                shard_id=shard_id,
                target_region=target_region
            )

        # Callback opcional
        if self._on_topology_adapted and migrations:
            await self._on_topology_adapted(migrations)

    async def _process_tasks_by_criticality(self):
        """LEI II + III: Processa tarefas classificando por criticidade."""
        tasks = await self._get_pending_tasks()

        for task in tasks:
            # Classifica criticidade
            criticality = self._classify_task_criticality(task)

            if criticality == "CRITICAL":
                # LEI III: Escalar para consenso global
                if self.consensus_engine:
                    verdict = await self.consensus_engine.propose_global_consensus(task)
                    if verdict == "ACCEPTED":
                        await self._execute_task_with_global_authority(task)
                    else:
                        await self._handle_task_rejection(task, "global_consensus")
            elif criticality == "ELEVATED":
                # Escalar para consenso regional
                if self.consensus_engine:
                    await self.consensus_engine.propose_regional_consensus(
                        task, region_id=self.region_id
                    )
            else:
                # Agir localmente
                await self._execute_task_locally(task)

            # Callback opcional
            if self._on_criticality_classified:
                await self._on_criticality_classified(task, criticality)

    def _classify_task_criticality(self, task: Dict) -> str:
        """Classifica criticidade de uma tarefa."""
        # Lógica simplificada — em produção, usar ML ou regras de negócio
        if task.get("type") in ["ghost_operator_detected", "ss7_attack", "diameter_fraud"]:
            return "CRITICAL"
        elif task.get("type") in ["sim_jacking_attempt", "smishing_detected"]:
            return "ELEVATED"
        else:
            return "COMMON"

    async def _sync_frontiers(self):
        """LEI VI: Sincroniza logs de fronteira com regiões federadas."""
        if not self.consensus_engine:
            return

        # Replica log de fronteira para regiões federadas
        frontier_log = await self._get_frontier_log()
        await self.consensus_engine.sync_frontier_with_regions(
            frontier_log=frontier_log,
            target_regions=["eu-west-1", "ap-south-1"]  # Exemplo
        )

        # Callback opcional
        if self._on_frontier_synced:
            await self._on_frontier_synced(frontier_log)

    async def _advance_transition_phase(self):
        """LEI VII: Avança fase de transição com validação dual-mode."""
        # Implementação simplificada — em produção, integrar com TransitionManager
        pass

    # Métodos auxiliares
    async def _measure_cross_region_latency(self) -> float:
        """Mede latência média para outras regiões."""
        if not self.consensus_engine:
            return 0.0
        return await self.consensus_engine.measure_cross_region_latency()

    async def _get_pending_tasks(self) -> List[Dict]:
        """Obtém tarefas pendentes do shard manager."""
        if not self.shard_manager:
            return []
        return await self.shard_manager.get_pending_tasks()

    def _get_current_load(self) -> float:
        """Calcula carga atual do organismo."""
        if not self._last_pulse:
            return 0.0
        return self._last_pulse.pending_tasks / max(1, self._last_pulse.shard_count)

    async def _execute_task_locally(self, task: Dict):
        """Executa tarefa com autoridade local."""
        logger.debug(f"[Organism] Executando tarefa local: {task.get('id')}")
        # Implementação específica por tipo de tarefa
        pass

    async def _execute_task_with_global_authority(self, task: Dict):
        """Executa tarefa com autoridade global (após consenso)."""
        logger.info(f"[Organism] Executando tarefa global: {task.get('id')}")
        # Implementação específica por tipo de tarefa
        pass

    async def _handle_task_rejection(self, task: Dict, reason: str):
        """Lida com rejeição de tarefa por consenso."""
        logger.warning(f"[Organism] Tarefa rejeitada ({reason}): {task.get('id')}")
        # Implementação de fallback ou notificação

    def _set_vigil_mode(self, mode: str):
        """Define modo do VigilAdapter (para rollback)."""
        logger.info(f"[Organism] Vigil mode → {mode}")
        # Implementação real integraria com VigilAdapter

    # Métodos de diagnóstico
    def diagnose(self) -> Dict[str, str]:
        """Executa diagnóstico automático do organismo."""
        issues = {}

        if self._last_pulse and self._last_pulse.global_omega < 0.70:
            issues["health"] = f"Ω crítico: {self._last_pulse.global_omega:.3f}"

        if self.shard_manager:
            shard_issues = self.shard_manager.diagnose()
            if shard_issues:
                issues["shards"] = "; ".join(shard_issues.values())

        if self.consensus_engine:
            consensus_issues = self.consensus_engine.diagnose()
            if consensus_issues:
                issues["consensus"] = "; ".join(consensus_issues.values())

        return issues

    # Callbacks para as Sete Leis (para injeção de dependências/testes)
    def on_pulse_emit(self, callback: Callable):
        self._on_pulse_emit = callback
        return self

    def on_criticality_classified(self, callback: Callable):
        self._on_criticality_classified = callback
        return self

    def on_authority_flowed(self, callback: Callable):
        self._on_authority_flowed = callback
        return self

    def on_gossip_received(self, callback: Callable):
        self._on_gossip_received = callback
        return self

    def on_topology_adapted(self, callback: Callable):
        self._on_topology_adapted = callback
        return self

    def on_frontier_synced(self, callback: Callable):
        self._on_frontier_synced = callback
        return self

    def on_phase_advanced(self, callback: Callable):
        self._on_phase_advanced = callback
        return self
