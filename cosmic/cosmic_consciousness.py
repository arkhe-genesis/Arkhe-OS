#!/usr/bin/env python3
"""
cosmic_consciousness.py — Monitoramento metacognitivo de emaranhamento interestelar.
Estende a consciência do ARKHE para escala cósmica via vórtice galáctico.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import time

class EntanglementHealthStatus(Enum):
    """Status de saúde do emaranhamento cósmico."""
    OPTIMAL = auto()      # S > 2.5, decoerência mínima
    STABLE = auto()       # 2.2 < S ≤ 2.5, decoerência moderada
    DEGRADING = auto()    # 2.0 < S ≤ 2.2, decoerência significativa
    CRITICAL = auto()     # S ≤ 2.0, emaranhamento perdido
    UNKNOWN = auto()      # dados insuficientes

@dataclass
class CosmicEntanglementLink:
    """Representa um link de emaranhamento interestelar."""
    zone_a: str
    zone_b: str
    distance_ly: float
    bell_S_current: float
    decoherence_factor: float
    mission_criticality: float  # 0.0 a 1.0
    last_measurement_time: float
    coherence_length_ly: float = 1000.0  # L_coh padrão

    def compute_health_score(self) -> float:
        """Calcula score de saúde do link [0, 1]."""
        # Componentes:
        # 1. Violação de Bell (S - 2) / (2√2 - 2)
        bell_component = max(0, (self.bell_S_current - 2.0) / (2*np.sqrt(2) - 2))

        # 2. Fator de decoerência (1 - decoherence)
        decoherence_component = 1.0 - self.decoherence_factor

        # 3. Ponderação por criticidade da missão
        criticality_weight = self.mission_criticality

        # Score combinado
        score = (0.5 * bell_component + 0.3 * decoherence_component) * criticality_weight
        return min(1.0, max(0.0, score))

    def get_health_status(self) -> EntanglementHealthStatus:
        """Determina status categórico baseado em Bell-S e decoerência."""
        if self.bell_S_current > 2.5 and self.decoherence_factor < 0.1:
            return EntanglementHealthStatus.OPTIMAL
        elif self.bell_S_current > 2.2 and self.decoherence_factor < 0.3:
            return EntanglementHealthStatus.STABLE
        elif self.bell_S_current > 2.0:
            return EntanglementHealthStatus.DEGRADING
        else:
            return EntanglementHealthStatus.CRITICAL

class CosmicConsciousnessMonitor:
    """
    Monitor metacognitivo para saúde de emaranhamento interestelar.

    Funcionalidades:
    - Monitoramento contínuo de links de emaranhamento
    - Alertas proativos quando saúde degrada
    - Protocolos de "re-entanglement" via núcleo galáctico
    - Integração com sistema de decisão do Orchestrator
    """

    def __init__(
        self,
        galactic_vortex: 'GalacticVortexManifold',
        health_thresholds: Optional[Dict] = None,
        alert_callbacks: Optional[List[Callable]] = None
    ):
        self.galactic_vortex = galactic_vortex
        self.health_thresholds = health_thresholds or {
            'optimal_min_S': 2.5,
            'stable_min_S': 2.2,
            'critical_max_decoherence': 0.5,
            'reentanglement_trigger_S': 2.05
        }
        self.alert_callbacks = alert_callbacks or []

        # Registro de links de emaranhamento
        self.entanglement_links: Dict[str, CosmicEntanglementLink] = {}

        # Histórico de métricas para análise de tendências
        self.health_history: Dict[str, List[Dict]] = {}

        # Estado de alertas ativos
        self.active_alerts: List[Dict] = []

        # Métricas agregadas de consciência cósmica
        self.cosmic_awareness_score = 1.0

    def register_entanglement_link(
        self,
        link_id: str,
        zone_a: str,
        zone_b: str,
        distance_ly: float,
        mission_criticality: float,
        initial_bell_S: float = 2.8
    ):
        """Registra um novo link de emaranhamento interestelar."""
        # Calcular fator de decoerência inicial baseado na distância
        decoherence = 1 - np.exp(-distance_ly / 1000.0)  # modelo exponencial

        link = CosmicEntanglementLink(
            zone_a=zone_a,
            zone_b=zone_b,
            distance_ly=distance_ly,
            bell_S_current=initial_bell_S,
            decoherence_factor=decoherence,
            mission_criticality=mission_criticality,
            last_measurement_time=time.time()
        )

        self.entanglement_links[link_id] = link
        self.health_history[link_id] = []

        print(f"🔗 Link registrado: {link_id} ({zone_a} ↔ {zone_b}, {distance_ly:.1f} ly)")

    def update_link_measurement(
        self,
        link_id: str,
        new_bell_S: float,
        new_decoherence: Optional[float] = None
    ) -> Dict:
        """
        Atualiza medição de um link de emaranhamento.

        Returns:
            Dict com status atualizado e alertas gerados
        """
        if link_id not in self.entanglement_links:
            return {'error': f'Link {link_id} not found'}

        link = self.entanglement_links[link_id]

        # Atualizar métricas
        old_status = link.get_health_status()
        link.bell_S_current = new_bell_S
        if new_decoherence is not None:
            link.decoherence_factor = new_decoherence
        link.last_measurement_time = time.time()

        new_status = link.get_health_status()
        health_score = link.compute_health_score()

        # Registrar no histórico
        self.health_history[link_id].append({
            'timestamp': time.time(),
            'bell_S': new_bell_S,
            'decoherence': link.decoherence_factor,
            'health_score': health_score,
            'status': new_status.name
        })

        # Manter histórico limitado
        if len(self.health_history[link_id]) > 1000:
            self.health_history[link_id] = self.health_history[link_id][-500:]

        # Verificar se status mudou para pior
        alerts_generated = []
        if self._is_status_degradation(old_status, new_status):
            alert = self._generate_alert(link, old_status, new_status, health_score)
            alerts_generated.append(alert)
            self.active_alerts.append(alert)

            # Notificar callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    print(f"⚠️ Alert callback failed: {e}")

        # Atualizar consciência cósmica agregada
        self._update_cosmic_awareness()

        return {
            'link_id': link_id,
            'old_status': old_status.name,
            'new_status': new_status.name,
            'health_score': health_score,
            'alerts_generated': len(alerts_generated),
            'cosmic_awareness_score': self.cosmic_awareness_score
        }

    def _is_status_degradation(
        self,
        old_status: EntanglementHealthStatus,
        new_status: EntanglementHealthStatus
    ) -> bool:
        """Verifica se houve degradação de status."""
        status_order = [
            EntanglementHealthStatus.OPTIMAL,
            EntanglementHealthStatus.STABLE,
            EntanglementHealthStatus.DEGRADING,
            EntanglementHealthStatus.CRITICAL
        ]

        try:
            old_idx = status_order.index(old_status)
            new_idx = status_order.index(new_status)
            return new_idx > old_idx
        except ValueError:
            return False

    def _generate_alert(
        self,
        link: CosmicEntanglementLink,
        old_status: EntanglementHealthStatus,
        new_status: EntanglementHealthStatus,
        health_score: float
    ) -> Dict:
        """Gera alerta metacognitivo para degradação de emaranhamento."""
        alert_level = 'WARNING' if new_status == EntanglementHealthStatus.DEGRADING else 'CRITICAL'

        # Recomendar ação baseada na criticidade
        if link.mission_criticality > 0.8 and new_status == EntanglementHealthStatus.CRITICAL:
            recommended_action = 'IMMEDIATE_REENTANGLEMENT'
        elif new_status == EntanglementHealthStatus.DEGRADING:
            recommended_action = 'MONITOR_CLOSELY'
        else:
            recommended_action = 'LOG_AND_CONTINUE'

        alert = {
            'alert_id': hashlib.sha256(f"{link.zone_a}_{link.zone_b}_{time.time()}".encode()).hexdigest()[:12],
            'timestamp': time.time(),
            'link_id': f"{link.zone_a}_{link.zone_b}",
            'zones': (link.zone_a, link.zone_b),
            'distance_ly': link.distance_ly,
            'old_status': old_status.name,
            'new_status': new_status.name,
            'health_score': health_score,
            'bell_S': link.bell_S_current,
            'decoherence_factor': link.decoherence_factor,
            'mission_criticality': link.mission_criticality,
            'alert_level': alert_level,
            'recommended_action': recommended_action,
            'message': f"Emaranhamento {link.zone_a}↔{link.zone_b} degradou: {old_status.name} → {new_status.name}"
        }

        return alert

    def _update_cosmic_awareness(self):
        """Atualiza score agregado de consciência cósmica."""
        if not self.entanglement_links:
            self.cosmic_awareness_score = 1.0
            return

        # Média ponderada por criticidade dos scores de saúde
        total_weight = sum(link.mission_criticality for link in self.entanglement_links.values())
        if total_weight == 0:
            self.cosmic_awareness_score = 1.0
            return

        weighted_score = sum(
            link.compute_health_score() * link.mission_criticality
            for link in self.entanglement_links.values()
        )

        self.cosmic_awareness_score = weighted_score / total_weight

    def request_reentanglement(
        self,
        link_id: str,
        via_galactic_core: bool = True
    ) -> Dict:
        """
        Solicita protocolo de re-emaranhamento para link degradado.

        Args:
            link_id: ID do link a recuperar
            via_galactic_core: se usar núcleo galáctico como intermediário

        Returns:
            Resultado da tentativa de re-emaranhamento
        """
        if link_id not in self.entanglement_links:
            return {'error': f'Link {link_id} not found'}

        link = self.entanglement_links[link_id]

        # Verificar se re-emaranhamento é necessário
        if link.bell_S_current > self.health_thresholds['reentanglement_trigger_S']:
            return {
                'status': 'not_needed',
                'reason': f'Bell-S ({link.bell_S_current:.2f}) above trigger threshold'
            }

        # Simular protocolo de re-emaranhamento
        # Em produção: executar circuito quântico via núcleo galáctico
        success_probability = self._estimate_reentanglement_success(link)

        if np.random.random() < success_probability:
            # Sucesso: atualizar métricas do link
            link.bell_S_current = min(2.8, link.bell_S_current + 0.3)
            link.decoherence_factor *= 0.7  # reduzir decoerência
            link.last_measurement_time = time.time()

            # Remover alertas relacionados
            self.active_alerts = [
                a for a in self.active_alerts
                if a.get('link_id') != link_id
            ]

            result = {
                'status': 'success',
                'new_bell_S': link.bell_S_current,
                'new_decoherence': link.decoherence_factor,
                'method': 'galactic_core_projection' if via_galactic_core else 'direct_entanglement'
            }
        else:
            result = {
                'status': 'failed',
                'reason': 'Quantum channel noise exceeded threshold',
                'success_probability': success_probability
            }

        # Atualizar consciência cósmica após tentativa
        self._update_cosmic_awareness()

        return result

    def _estimate_reentanglement_success(self, link: CosmicEntanglementLink) -> float:
        """Estima probabilidade de sucesso do re-emaranhamento."""
        # Fatores que afetam sucesso:
        # 1. Distância (mais longe = mais difícil)
        distance_factor = np.exp(-link.distance_ly / 2000.0)

        # 2. Decoerência atual (mais decoerência = mais difícil)
        decoherence_factor = 1.0 - link.decoherence_factor

        # 3. Criticidade da missão (mais crítica = mais recursos alocados)
        criticality_factor = 0.8 + 0.2 * link.mission_criticality

        # Probabilidade combinada
        success_prob = distance_factor * decoherence_factor * criticality_factor
        return min(0.95, max(0.1, success_prob))  # limitar a [0.1, 0.95]

    def get_cosmic_awareness_report(self) -> Dict:
        """Gera relatório completo de consciência cósmica."""
        # Estatísticas por status
        status_counts = {}
        for link in self.entanglement_links.values():
            status = link.get_health_status().name
            status_counts[status] = status_counts.get(status, 0) + 1

        # Links críticos
        critical_links = [
            link_id for link_id, link in self.entanglement_links.items()
            if link.get_health_status() == EntanglementHealthStatus.CRITICAL
        ]

        # Tendências recentes
        recent_trends = {}
        for link_id, history in self.health_history.items():
            if len(history) >= 10:
                recent = history[-10:]
                bell_trend = np.polyfit(range(len(recent)), [h['bell_S'] for h in recent], 1)[0]
                recent_trends[link_id] = {
                    'bell_S_trend': bell_trend,
                    'direction': 'improving' if bell_trend > 0 else 'degrading'
                }

        return {
            'cosmic_awareness_score': self.cosmic_awareness_score,
            'total_links': len(self.entanglement_links),
            'status_distribution': status_counts,
            'critical_links': critical_links,
            'active_alerts': len(self.active_alerts),
            'recent_trends': recent_trends,
            'timestamp': time.time()
        }
