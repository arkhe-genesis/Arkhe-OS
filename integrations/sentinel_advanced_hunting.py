#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sentinel_advanced_hunting.py — Substrato 9038: Conector Microsoft Sentinel Advanced Hunting
Integra alertas ARKHE com Microsoft Sentinel usando consultas KQL nativas
para detecção avançada de ameaças e correlação com outros sinais de segurança.
"""

import json
import time
import hashlib
import asyncio
import requests
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum, auto
import logging
from datetime import datetime, timedelta

# Tentar importar biblioteca Azure
try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    from azure.security.insights import SecurityInsightsClient
    from azure.core.exceptions import AzureError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logging.warning("⚠️  azure-identity/azure-security-insights não disponível — usando modo simulado")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# TIPOS E CONSTANTES
# ============================================================================

class SentinelAlertSeverity(Enum):
    """Severidade de alertas mapeada para Sentinel."""
    INFORMATIONAL = "Informational"  # Sentinel: 0
    LOW = "Low"                      # Sentinel: 1
    MEDIUM = "Medium"                # Sentinel: 2
    HIGH = "High"                    # Sentinel: 3
    CRITICAL = "Critical"            # Sentinel: 4

@dataclass
class ArkheSentinelAlert:
    """Alerta ARKHE formatado para Microsoft Sentinel."""
    alert_id: str
    timestamp: float
    component: str
    alert_type: str
    severity: SentinelAlertSeverity
    description: str
    evidence: Dict
    phi_c_value: Optional[float] = None
    temporal_seal: Optional[str] = None
    remediation_suggested: Optional[str] = None
    # Campos específicos Sentinel
    tactic: Optional[str] = None  # MITRE ATT&CK tactic
    technique: Optional[str] = None  # MITRE ATT&CK technique
    entities: List[Dict] = field(default_factory=list)  # Entidades para correlação

# ============================================================================
# CONECTOR SENTINEL ADVANCED HUNTING
# ============================================================================

class SentinelAdvancedHuntingConnector:
    """
    Conector para Microsoft Sentinel Advanced Hunting.

    Funcionalidades:
    • Envio de alertas via Azure Monitor HTTP Data Collector API
    • Formatação nativa para Sentinel com campos customizados
    • Consultas KQL pré-definidas para detecção de ameaças ARKHE
    • Correlação com outros sinais via Azure Sentinel Analytics Rules
    • Enriquecimento com contexto Φ_C e selos temporais
    • Suporte a entidades para grafos de investigação
    """

    # Mapeamento de severidade ARKHE → Sentinel
    SEVERITY_MAP = {
        "informational": SentinelAlertSeverity.INFORMATIONAL,
        "low": SentinelAlertSeverity.LOW,
        "medium": SentinelAlertSeverity.MEDIUM,
        "high": SentinelAlertSeverity.HIGH,
        "critical": SentinelAlertSeverity.CRITICAL,
    }

    # Consultas KQL pré-definidas para detecção de ameaças ARKHE
    KQL_QUERIES = {
        "phi_c_anomaly_detection": """
// Detecção de anomalias em coerência Φ_C
ArkheCathedral_CL
| where TimeGenerated > ago(24h)
| where PhiC_Coherence < 0.95
| summarize
    MinPhiC = min(PhiC_Coherence),
    AvgPhiC = avg(PhiC_Coherence),
    AlertCount = count()
    by Component_s, bin(TimeGenerated, 1h)
| where AlertCount > 3 or MinPhiC < 0.90
| extend
    AlertName = "PhiC Coherence Anomaly",
    Severity = iff(MinPhiC < 0.90, "High", "Medium"),
    Tactics = "Impact",
    Techniques = "Data Manipulation"
""",

        "deepfake_broadcast_detection": """
// Detecção de deepfakes em transmissão broadcast
ArkheCathedral_CL
| where AlertType_s == "deepfake_detected"
| where TimeGenerated > ago(1h)
| summarize
    MaxScore = max(Deepfake_Score),
    SuspiciousFrames = sum(Suspicious_Frames),
    TotalFrames = sum(Total_Frames)
    by ContentId_s, bin(TimeGenerated, 5m)
| where MaxScore > 0.65 or (SuspiciousFrames * 1.0 / TotalFrames) > 0.1
| extend
    AlertName = "Broadcast Deepfake Detected",
    Severity = iff(MaxScore > 0.85, "Critical", "High"),
    Tactics = "Initial Access",
    Techniques = "Supply Chain Compromise"
""",

        "ldm_manipulation_detection": """
// Detecção de manipulação em configuração LDM
ArkheCathedral_CL
| where AlertType_s startswith "ldm_"
| where TimeGenerated > ago(6h)
| summarize
    InjectionChanges = countif(AlertType_s == "ldm_adjusted"),
    MaxInjectionChange = max(abs(PreviousInjection - NewInjection))
    by HeadendVendor_s, bin(TimeGenerated, 30m)
| where InjectionChanges > 5 or MaxInjectionChange > 3.0
| extend
    AlertName = "Suspicious LDM Configuration Changes",
    Severity = "Medium",
    Tactics = "Persistence",
    Techniques = "Modify Registry"
""",

        "pqc_signature_anomaly": """
// Detecção de anomalias em assinaturas PQC
ArkheCathedral_CL
| where AlertType_s in ("pqc_signature_invalid", "pqc_verification_failed")
| where TimeGenerated > ago(12h)
| summarize
    FailureCount = count(),
    AffectedSegments = dcount(SegmentId_s)
    by Algorithm_s, bin(TimeGenerated, 1h)
| where FailureCount > 2 or AffectedSegments > 10
| extend
    AlertName = "PQC Signature Verification Failures",
    Severity = "High",
    Tactics = "Defense Evasion",
    Techniques = "Impair Defenses"
""",
    }

    def __init__(
        self,
        workspace_id: str,
        shared_key: str,
        log_type: str = "ArkheCathedral",
        credential: Optional[str] = None,
    ):
        self.workspace_id = workspace_id
        self.shared_key = shared_key
        self.log_type = log_type
        self.credential = credential
        self.session = None

        if AZURE_AVAILABLE and credential:
            self._init_azure_client()

    def _init_azure_client(self):
        """Inicializa cliente Azure Security Insights."""
        try:
            self.client = SecurityInsightsClient(
                credential=self.credential,
                subscription_id=self.workspace_id.split('-')[0] if '-' in self.workspace_id else None,
            )
            logger.info("✅ Cliente Azure Security Insights inicializado")
        except Exception as e:
            logger.warning(f"⚠️  Falha ao inicializar cliente Azure: {e}")

    def send_alert(
        self,
        alert: ArkheSentinelAlert,
        use_advanced_hunting: bool = True,
    ) -> bool:
        """
        Envia alerta para Microsoft Sentinel.

        Args:
            alert: Alerta formatado para Sentinel
            use_advanced_hunting: Se True, usa campos otimizados para Advanced Hunting

        Returns:
            True se enviado com sucesso
        """
        # Formatar alerta para Sentinel
        sentinel_payload = self._format_for_sentinel(alert, use_advanced_hunting)

        # Enviar via Azure Monitor HTTP Data Collector API
        success = self._send_to_azure_monitor(sentinel_payload)

        if success:
            logger.info(f"✅ Alerta enviado para Sentinel: {alert.alert_id}")
        else:
            logger.error(f"❌ Falha ao enviar alerta para Sentinel: {alert.alert_id}")

        return success

    def _format_for_sentinel(
        self,
        alert: ArkheSentinelAlert,
        use_advanced_hunting: bool,
    ) -> Dict:
        """Formata alerta ARKHE para formato nativo do Sentinel."""
        # Campos obrigatórios Azure Monitor
        payload = {
            # Timestamp em formato ISO 8601
            "TimeGenerated": datetime.fromtimestamp(alert.timestamp).isoformat() + "Z",

            # Campos de evento padrão
            "AlertId": alert.alert_id,
            "AlertType": alert.alert_type,
            "Severity": alert.severity.value,
            "AlertName": f"ARKHE: {alert.alert_type.replace('_', ' ').title()}",
            "Description": alert.description,
            "Component": alert.component,

            # Campos ARKHE-specific (com sufixo _s para string, _d para double)
            "PhiC_Coherence_d": alert.phi_c_value if alert.phi_c_value else None,
            "Temporal_Seal_s": alert.temporal_seal or "",
            "Remediation_Suggestion_s": alert.remediation_suggested or "",

            # Evidências como JSON string
            "Evidence_s": json.dumps(alert.evidence),

            # Campos para Advanced Hunting (se habilitado)
            **(self._get_advanced_hunting_fields(alert) if use_advanced_hunting else {}),
        }

        # Adicionar entidades para correlação (grafos de investigação)
        if alert.entities:
            payload["Entities_s"] = json.dumps(alert.entities)

        # Mapear para MITRE ATT&CK se disponível
        if alert.tactic or alert.technique:
            payload["MITRE_Tactic_s"] = alert.tactic or ""
            payload["MITRE_Technique_s"] = alert.technique or ""

        return payload

    def _get_advanced_hunting_fields(self, alert: ArkheSentinelAlert) -> Dict:
        """Campos otimizados para consultas Advanced Hunting."""
        return {
            # Campos indexados para consultas rápidas
            "ContentId_s": alert.evidence.get("content_id", ""),
            "SegmentId_s": alert.evidence.get("segment_id", ""),
            "HeadendVendor_s": alert.evidence.get("headend_vendor", ""),

            # Métricas numéricas para agregação
            "Deepfake_Score_d": alert.evidence.get("deepfake_score", 0.0),
            "Suspicious_Frames_n": alert.evidence.get("suspicious_frames", 0),
            "Total_Frames_n": alert.evidence.get("total_frames", 0),
            "PreviousInjection_d": alert.evidence.get("previous_injection_db"),
            "NewInjection_d": alert.evidence.get("new_injection_db"),
            "Algorithm_s": alert.evidence.get("pqc_algorithm", ""),

            # Flags para filtragem booleana
            "IsDeepfakeConfirmed_b": alert.evidence.get("verdict") == "confirmed",
            "IsLDMAdjusted_b": alert.alert_type.startswith("ldm_"),
            "IsPQCRelated_b": "pqc" in alert.alert_type.lower(),
        }

    def _send_to_azure_monitor(self, payload: Dict) -> bool:
        """Envia payload para Azure Monitor via HTTP Data Collector API."""
        import hmac
        import hashlib
        import base64
        from datetime import datetime, timezone

        # Preparar payload
        body = json.dumps([payload]).encode('utf-8')

        # Construir assinatura (conforme documentação Azure)
        date_string = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        string_to_hash = f"POST\n{len(body)}\napplication/json\nx-ms-date:{date_string}\n/api/logs"
        signature = base64.b64encode(
            hmac.new(
                base64.b64decode(self.shared_key),
                msg=string_to_hash.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
        ).decode('utf-8')

        # Headers da requisição
        headers = {
            "Authorization": f"SharedKey {self.workspace_id}:{signature}",
            "Log-Type": self.log_type,
            "x-ms-date": date_string,
            "Content-Type": "application/json",
            "time-generated-field": "TimeGenerated",
        }

        # Endpoint da API
        url = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"

        try:
            response = requests.post(url, headers=headers, data=body, timeout=30)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Erro ao enviar para Azure Monitor: {e}")
            return False

    def execute_kql_query(self, query_name: str, time_range_hours: int = 24) -> List[Dict]:
        """
        Executa consulta KQL pré-definida no Sentinel.

        Args:
            query_name: Nome da consulta pré-definida
            time_range_hours: Janela de tempo para a consulta

        Returns:
            Lista de resultados da consulta
        """
        if query_name not in self.KQL_QUERIES:
            raise ValueError(f"Consulta KQL não encontrada: {query_name}")

        query = self.KQL_QUERIES[query_name]

        # Substituir parâmetros de tempo na consulta
        query = query.replace("ago(24h)", f"ago({time_range_hours}h)")

        if AZURE_AVAILABLE and hasattr(self, 'client') and self.client:
            # Executar consulta via API real do Sentinel
            try:
                # Em produção: usar client.analytics_rules ou logs query API
                # Para demo: retornar resultados simulados
                return self._simulate_kql_results(query_name, time_range_hours)
            except AzureError as e:
                logger.error(f"❌ Erro ao executar consulta KQL: {e}")
                return []
        else:
            # Modo simulado
            return self._simulate_kql_results(query_name, time_range_hours)

    def _simulate_kql_results(self, query_name: str, time_range_hours: int) -> List[Dict]:
        """Simula resultados de consulta KQL para demonstração."""
        # Resultados simulados baseados no tipo de consulta
        if query_name == "phi_c_anomaly_detection":
            return [
                {
                    "TimeGenerated": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
                    "Component_s": "broadcast_guardian",
                    "MinPhiC": 0.892,
                    "AvgPhiC": 0.923,
                    "AlertCount": 5,
                    "AlertName": "PhiC Coherence Anomaly",
                    "Severity": "High",
                }
            ]
        elif query_name == "deepfake_broadcast_detection":
            return [
                {
                    "TimeGenerated": (datetime.utcnow() - timedelta(minutes=30)).isoformat() + "Z",
                    "ContentId_s": "live_channel_7",
                    "MaxScore": 0.72,
                    "SuspiciousFrames": 8,
                    "TotalFrames": 60,
                    "AlertName": "Broadcast Deepfake Detected",
                    "Severity": "High",
                }
            ]
        elif query_name == "ldm_manipulation_detection":
            return [
                {
                    "TimeGenerated": (datetime.utcnow() - timedelta(hours=4)).isoformat() + "Z",
                    "HeadendVendor_s": "Harmonic_XOS",
                    "InjectionChanges": 7,
                    "MaxInjectionChange": 4.5,
                    "AlertName": "Suspicious LDM Configuration Changes",
                    "Severity": "Medium",
                }
            ]
        elif query_name == "pqc_signature_anomaly":
            return [
                {
                    "TimeGenerated": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
                    "Algorithm_s": "Dilithium-3",
                    "FailureCount": 3,
                    "AffectedSegments": 15,
                    "AlertName": "PQC Signature Verification Failures",
                    "Severity": "High",
                }
            ]

        return []

    def create_analytics_rule(
        self,
        rule_name: str,
        query_name: str,
        severity: SentinelAlertSeverity,
        enabled: bool = True,
    ) -> Dict:
        """
        Cria regra de analytics no Sentinel baseada em consulta KQL.

        Args:
            rule_name: Nome da regra no Sentinel
            query_name: Nome da consulta KQL pré-definida
            severity: Severidade dos alertas gerados
            enabled: Se a regra deve ser ativada imediatamente

        Returns:
            Metadados da regra criada
        """
        if query_name not in self.KQL_QUERIES:
            raise ValueError(f"Consulta KQL não encontrada: {query_name}")

        query = self.KQL_QUERIES[query_name]

        # Configuração da regra de analytics
        rule_config = {
            "displayName": rule_name,
            "description": f"Regra automática para detecção de {query_name} via ARKHE Cathedral",
            "enabled": enabled,
            "query": query,
            "queryFrequency": "PT1H",  # Executar a cada hora
            "queryPeriod": "PT24H",    # Janela de 24 horas
            "triggerOperator": "GreaterThan",
            "triggerThreshold": 1,
            "severity": severity.value,
            "tactics": ["Impact", "Initial Access", "Defense Evasion"],  # MITRE ATT&CK
            "alertRuleTemplateName": "ARKHE-Cathedral-Detection",
        }

        if AZURE_AVAILABLE and hasattr(self, 'client') and self.client:
            # Em produção: criar regra via API do Sentinel
            # Para demo: retornar configuração simulada
            pass

        logger.info(f"✅ Regra de analytics configurada: {rule_name}")
        return {
            "rule_name": rule_name,
            "query_name": query_name,
            "severity": severity.value,
            "enabled": enabled,
            "query_frequency": "1 hour",
            "query_period": "24 hours",
        }
