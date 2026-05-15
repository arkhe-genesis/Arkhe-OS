#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
siem_correlation_engine.py — Substrato 9040-D: Motor de Correlação Unificada de Alertas
Correlaciona alertas de GatesAir Maxiva, Microsoft Sentinel e Splunk para visão unificada
de segurança e operação do broadcast.
"""

import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Set
from enum import Enum, auto
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# TIPOS E CONSTANTES
# ============================================================================

class AlertSource(Enum):
    """Fontes de alerta suportadas para correlação."""
    GATESAIR_MAXIVA = "gatesair_maxiva"
    MICROSOFT_SENTINEL = "microsoft_sentinel"
    SPLUNK = "splunk"
    ARKHE_INTERNAL = "arkhe_internal"

class CorrelationRuleType(Enum):
    """Tipos de regras de correlação suportadas."""
    TEMPORAL_WINDOW = "temporal_window"      # Alertas dentro de janela de tempo
    ENTITY_MATCH = "entity_match"           # Alertas sobre mesma entidade
    PATTERN_SEQUENCE = "pattern_sequence"    # Sequência específica de eventos
    THRESHOLD_AGGREGATION = "threshold_agg"  # Agregação ultrapassa threshold
    CROSS_SOURCE_CORRELATION = "cross_source"  # Correlação entre fontes diferentes

@dataclass
class CorrelatedAlert:
    """Alerta correlacionado com contexto enriquecido."""
    correlation_id: str
    source_alerts: List[Dict]  # Alertas originais de múltiplas fontes
    correlation_rule: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_entities: List[str]
    recommended_actions: List[str]
    created_at: float
    temporal_seal: Optional[str] = None
    confidence_score: float = 0.0

@dataclass
class CorrelationRule:
    """Definição de regra de correlação."""
    rule_id: str
    name: str
    description: str
    rule_type: CorrelationRuleType
    source_filters: Dict[AlertSource, Dict]  # Filtros por fonte
    conditions: Dict  # Condições para disparo
    actions: List[Dict]  # Ações a executar ao disparar
    enabled: bool = True
    priority: int = 5  # 1-10, onde 1 é mais crítico

# ============================================================================
# MOTOR DE CORRELAÇÃO
# ============================================================================

class SIEMCorrelationEngine:
    """
    Motor de correlação unificada para alertas de múltiplas fontes SIEM.

    Funcionalidades:
    • Ingestão de alertas de GatesAir Maxiva, Sentinel, Splunk e ARKHE
    • Correlação baseada em regras configuráveis (temporal, entidade, padrão)
    • Enriquecimento de alertas com contexto Φ_C e métricas de broadcast
    • Geração de alertas correlacionados com ações recomendadas
    • Ancoragem de correlações na TemporalChain para auditoria
    • Exportação para dashboards operacionais e sistemas de ticket
    """

    # Regras de correlação pré-definidas para broadcast
    DEFAULT_CORRELATION_RULES = [
        CorrelationRule(
            rule_id="broadcast_integrity_degradation",
            name="Degradação de Integridade de Broadcast",
            description="Correlaciona queda de Φ_C com alertas de sinal RF e assinaturas PQC",
            rule_type=CorrelationRuleType.CROSS_SOURCE_CORRELATION,
            source_filters={
                AlertSource.GATESAIR_MAXIVA: {"alert_type": {"$in": ["cnr_low", "mer_low", "ldm_drift"]}},
                AlertSource.ARKHE_INTERNAL: {"alert_type": {"$in": ["phi_c_drop", "pqc_verification_failed"]}},
            },
            conditions={
                "time_window_minutes": 5,
                "min_sources": 2,
                "phi_c_threshold": 0.95,
            },
            actions=[
                {"type": "notify", "channel": "ops_team", "severity": "high"},
                {"type": "auto_remediate", "action": "adjust_ldm_injection"},
                {"type": "create_ticket", "system": "jira", "priority": "P2"},
            ],
            enabled=True,
            priority=2,
        ),
        CorrelationRule(
            rule_id="security_broadcast_threat",
            name="Ameaça de Segurança em Broadcast",
            description="Correlaciona tentativas de acesso não autorizado com anomalias de sinal",
            rule_type=CorrelationRuleType.PATTERN_SEQUENCE,
            source_filters={
                AlertSource.MICROSOFT_SENTINEL: {"tactic": {"$in": ["Initial Access", "Defense Evasion"]}},
                AlertSource.GATESAIR_MAXIVA: {"alert_type": {"$in": ["unauthorized_config_change", "snmp_trap_auth_fail"]}},
            },
            conditions={
                "sequence": ["sentinel_auth_alert", "maxiva_config_change"],
                "max_time_between_minutes": 10,
            },
            actions=[
                {"type": "notify", "channel": "security_team", "severity": "critical"},
                {"type": "isolate", "target": "affected_channel"},
                {"type": "create_ticket", "system": "servicenow", "priority": "P1"},
            ],
            enabled=True,
            priority=1,
        ),
        CorrelationRule(
            rule_id="pqc_signature_anomaly",
            name="Anomalia em Assinatura PQC",
            description="Correlaciona falhas de verificação PQC com métricas de integridade",
            rule_type=CorrelationRuleType.ENTITY_MATCH,
            source_filters={
                AlertSource.ARKHE_INTERNAL: {"alert_type": "pqc_verification_failed"},
                AlertSource.SPLUNK: {"event_type": "integrity_check_failed"},
            },
            conditions={
                "entity_field": "segment_id",
                "min_occurrences": 3,
                "time_window_minutes": 15,
            },
            actions=[
                {"type": "notify", "channel": "crypto_team", "severity": "high"},
                {"type": "revoke_key", "if_confidence": 0.9},
                {"type": "create_ticket", "system": "jira", "priority": "P2"},
            ],
            enabled=True,
            priority=3,
        ),
    ]

    def __init__(
        self,
        rules: Optional[List[CorrelationRule]] = None,
        temporal_chain=None,
    ):
        self.rules = {r.rule_id: r for r in (rules or self.DEFAULT_CORRELATION_RULES)}
        self.temporal = temporal_chain
        self.alert_buffer: Dict[AlertSource, List[Dict]] = defaultdict(list)
        self.correlated_alerts: List[CorrelatedAlert] = []
        self.entity_index: Dict[str, List[Dict]] = defaultdict(list)  # Para correlação por entidade

    async def ingest_alert(self, source: AlertSource, alert: Dict):
        """
        Ingere alerta de uma fonte para processamento de correlação.

        Args:
            source: Fonte do alerta (Maxiva, Sentinel, Splunk, ARKHE)
            alert: Dados do alerta no formato nativo da fonte
        """
        # Adicionar metadados de ingestão
        alert["_ingested_at"] = time.time()
        alert["_source"] = source.value
        alert["_source_enum"] = source

        # Bufferizar alerta
        self.alert_buffer[source].append(alert)

        # Indexar por entidade para correlação futura
        if "entity_id" in alert or "segment_id" in alert or "channel_id" in alert:
            entity = alert.get("entity_id") or alert.get("segment_id") or alert.get("channel_id")
            self.entity_index[entity].append(alert)

        # Executar regras de correlação em background
        asyncio.create_task(self._evaluate_rules(source, alert))

    async def _evaluate_rules(self, source: AlertSource, new_alert: Dict):
        """Avalia regras de correlação contra novo alerta."""
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue

            # Verificar se alerta corresponde aos filtros da regra
            if not self._matches_source_filter(new_alert, rule, source):
                continue

            # Avaliar condições da regra
            if await self._evaluate_rule_conditions(rule, new_alert):
                # Disparar ações e gerar alerta correlacionado
                correlated = await self._generate_correlated_alert(rule, new_alert)
                if correlated:
                    self.correlated_alerts.append(correlated)
                    await self._execute_actions(correlated, rule.actions)

    def _matches_source_filter(self, alert: Dict, rule: CorrelationRule, source: AlertSource) -> bool:
        """Verifica se alerta corresponde aos filtros de fonte da regra."""
        if source not in rule.source_filters:
            return False

        filters = rule.source_filters[source]
        for field, condition in filters.items():
            alert_value = alert.get(field)
            if alert_value is None:
                return False

            # Suporte a operadores simples: $in, $eq, $gt, $lt
            if isinstance(condition, dict):
                if "$in" in condition and alert_value not in condition["$in"]:
                    return False
                elif "$eq" in condition and alert_value != condition["$eq"]:
                    return False
                elif "$gt" in condition and alert_value <= condition["$gt"]:
                    return False
                elif "$lt" in condition and alert_value >= condition["$lt"]:
                    return False
            elif alert_value != condition:
                return False

        return True

    async def _evaluate_rule_conditions(self, rule: CorrelationRule, new_alert: Dict) -> bool:
        """Avalia condições da regra para determinar se deve disparar."""
        conditions = rule.conditions

        if rule.rule_type == CorrelationRuleType.TEMPORAL_WINDOW:
            # Verificar alertas dentro da janela de tempo
            window_minutes = conditions.get("time_window_minutes", 5)
            cutoff = time.time() - (window_minutes * 60)

            related_alerts = [
                a for source_alerts in self.alert_buffer.values()
                for a in source_alerts
                if a.get("_ingested_at", 0) >= cutoff and a != new_alert
            ]

            min_sources = conditions.get("min_sources", 2)
            unique_sources = len(set(a["_source"] for a in related_alerts))
            return unique_sources >= min_sources

        elif rule.rule_type == CorrelationRuleType.ENTITY_MATCH:
            # Verificar múltiplos alertas sobre mesma entidade
            entity = new_alert.get("entity_id") or new_alert.get("segment_id")
            if not entity:
                return False

            entity_alerts = self.entity_index.get(entity, [])
            min_occurrences = conditions.get("min_occurrences", 2)
            return len(entity_alerts) >= min_occurrences

        elif rule.rule_type == CorrelationRuleType.PATTERN_SEQUENCE:
            # Verificar sequência específica de eventos
            sequence = conditions.get("sequence", [])
            max_time = conditions.get("max_time_between_minutes", 10) * 60

            # Simplificado: verificar se alertas da sequência existem dentro da janela
            found_sequence = True
            last_time = new_alert.get("_ingested_at", time.time())

            for expected_type in reversed(sequence[1:]):  # Novo alerta é o último
                matching = [
                    a for source_alerts in self.alert_buffer.values()
                    for a in source_alerts
                    if a.get("alert_type") == expected_type
                    and last_time - a.get("_ingested_at", 0) <= max_time
                ]
                if not matching:
                    found_sequence = False
                    break
                last_time = matching[0].get("_ingested_at", last_time)

            return found_sequence

        elif rule.rule_type == CorrelationRuleType.THRESHOLD_AGGREGATION:
            # Verificar se agregação ultrapassa threshold
            # Implementação específica por métrica
            pass

        elif rule.rule_type == CorrelationRuleType.CROSS_SOURCE_CORRELATION:
            # Correlação cruzada entre fontes diferentes
            window_minutes = conditions.get("time_window_minutes", 5)
            cutoff = time.time() - (window_minutes * 60)

            source = new_alert.get("_source_enum")
            # Verificar alertas de outras fontes dentro da janela
            other_sources = [s for s in rule.source_filters.keys() if s != source]
            for other_source in other_sources:
                related = [
                    a for a in self.alert_buffer[other_source]
                    if a.get("_ingested_at", 0) >= cutoff
                ]
                if related:
                    # Verificar condição adicional (ex: Φ_C threshold)
                    if "phi_c_threshold" in conditions:
                        phi_c = new_alert.get("phi_c_value") or next(
                            (a.get("phi_c_value") for a in related if a.get("phi_c_value")),
                            1.0
                        )
                        if phi_c < conditions["phi_c_threshold"]:
                            return True
                    else:
                        return True

        return False

    async def _generate_correlated_alert(
        self,
        rule: CorrelationRule,
        triggering_alert: Dict,
    ) -> Optional[CorrelatedAlert]:
        """Gera alerta correlacionado baseado em regra e alerta disparador."""
        # Coletar alertas relacionados
        related_alerts = [triggering_alert]

        if rule.rule_type == CorrelationRuleType.ENTITY_MATCH:
            entity = triggering_alert.get("entity_id") or triggering_alert.get("segment_id")
            if entity:
                related_alerts.extend(
                    a for a in self.entity_index.get(entity, [])
                    if a != triggering_alert
                )
        else:
            # Adicionar alertas recentes de outras fontes
            for source in rule.source_filters.keys():
                related_alerts.extend(
                    a for a in self.alert_buffer[source][-10:]  # Últimos 10
                    if a != triggering_alert
                )

        # Determinar severidade baseada em prioridade da regra e alertas
        base_severity = {"1": "critical", "2": "high", "3": "medium", "4": "low"}.get(
            str(rule.priority), "medium"
        )

        # Calcular score de confiança
        confidence = min(1.0, len(related_alerts) * 0.2 + (10 - rule.priority) * 0.05)

        # Gerar descrição enriquecida
        description = f"{rule.name}: {len(related_alerts)} alertas correlacionados"

        # Identificar entidades afetadas
        affected_entities = list(set(
            a.get("entity_id") or a.get("segment_id") or a.get("channel_id")
            for a in related_alerts
            if a.get("entity_id") or a.get("segment_id") or a.get("channel_id")
        ))

        # Gerar ID único para correlação
        correlation_id = hashlib.sha3_256(
            f"{rule.rule_id}:{triggering_alert.get('_ingested_at', time.time())}".encode()
        ).hexdigest()[:12]

        correlated = CorrelatedAlert(
            correlation_id=correlation_id,
            source_alerts=[{"source": a["_source"], "alert_type": a.get("alert_type"), "id": a.get("id")} for a in related_alerts],
            correlation_rule=rule.name,
            severity=base_severity,
            description=description,
            affected_entities=affected_entities,
            recommended_actions=[a["action"] for a in rule.actions if a["type"] == "auto_remediate"],
            created_at=time.time(),
            confidence_score=confidence,
        )

        # Ancorar na TemporalChain se disponível
        if self.temporal:
            correlated.temporal_seal = await self.temporal.anchor_event(
                "alert_correlated",
                {
                    "correlation_id": correlation_id,
                    "rule_id": rule.rule_id,
                    "severity": base_severity,
                    "entity_count": len(affected_entities),
                    "confidence": confidence,
                    "timestamp": time.time(),
                }
            )

        return correlated

    async def _execute_actions(self, correlated: CorrelatedAlert, actions: List[Dict]):
        """Executa ações definidas na regra de correlação."""
        for action in actions:
            action_type = action.get("type")

            if action_type == "notify":
                # Enviar notificação para canal especificado
                channel = action.get("channel")
                severity = action.get("severity", correlated.severity)
                logger.info(f"📧 Notificando {channel}: {correlated.description} [{severity}]")

            elif action_type == "auto_remediate":
                # Executar ação corretiva automática
                remediation = action.get("action")
                logger.info(f"🔧 Executando correção automática: {remediation}")
                # Em produção: chamar API de remediação

            elif action_type == "create_ticket":
                # Criar ticket em sistema externo
                system = action.get("system")
                priority = action.get("priority")
                logger.info(f"🎫 Criando ticket {system} [{priority}]: {correlated.correlation_id}")

            elif action_type == "isolate":
                # Isolar entidade afetada
                target = action.get("target")
                logger.info(f"🔒 Isolando {target}: {correlated.affected_entities}")

            elif action_type == "revoke_key":
                # Revogar chave criptográfica se confiança alta
                if correlated.confidence_score >= action.get("if_confidence", 0.9):
                    logger.info(f"🔑 Revogando chave criptográfica devido a anomalia PQC")

    def get_correlated_alerts(
        self,
        severity_filter: Optional[str] = None,
        time_window_hours: int = 24,
    ) -> List[CorrelatedAlert]:
        """
        Obtém alertas correlacionados com filtros opcionais.

        Args:
            severity_filter: Filtrar por severidade ("low", "medium", "high", "critical")
            time_window_hours: Janela de tempo para buscar alertas

        Returns:
            Lista de CorrelatedAlert ordenada por criação (mais recente primeiro)
        """
        cutoff = time.time() - (time_window_hours * 3600)

        filtered = [
            a for a in self.correlated_alerts
            if a.created_at >= cutoff
            and (severity_filter is None or a.severity == severity_filter)
        ]

        return sorted(filtered, key=lambda a: a.created_at, reverse=True)

    def export_for_dashboard(self, correlated: CorrelatedAlert) -> Dict:
        """Exporta alerta correlacionado para formato de dashboard."""
        return {
            "correlation_id": correlated.correlation_id,
            "rule_name": correlated.correlation_rule,
            "severity": correlated.severity,
            "description": correlated.description,
            "entities": correlated.affected_entities,
            "confidence": correlated.confidence_score,
            "created_at": datetime.fromtimestamp(correlated.created_at).isoformat(),
            "temporal_seal": correlated.temporal_seal,
            "source_summary": f"{len(correlated.source_alerts)} alertas de {len(set(a['source'] for a in correlated.source_alerts))} fontes",
            "actions_available": len(correlated.recommended_actions),
        }
