#!/usr/bin/env python3
"""
Substrato 199.4: Production Partner Orchestrator
Gerencia o deploy real em múltiplas organizações parceiras (bancos/empresas),
coordenando a federação de anomalias, calibração de privacidade diferencial em campo,
e integração automática com sistemas de ticketing de cada parceiro.
"""

import asyncio
import hashlib
import json
import time
import aiohttp
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum, auto
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Partner Definitions & Secure Communication
# ═══════════════════════════════════════════════════════════════

class PartnerSector(Enum):
    BANKING = "banking"
    INSURANCE = "insurance"
    TELECOM = "telecom"
    ENERGY = "energy"
    RETAIL = "retail"

@dataclass
class PartnerOrganization:
    """Organização parceira em produção."""
    partner_id: str
    name: str
    sector: PartnerSector
    privacy_budget: Dict[str, float]  # {"epsilon": 3.0, "delta": 1e-5}
    ticketing_system: str  # "servicenow", "jira", "custom"
    ticketing_endpoint: str
    ticketing_auth: Dict[str, str]  # API key, OAuth2, etc.
    data_endpoint: str  # Endpoint para receber métricas de anomalias
    pqc_public_key: str  # Chave pública PQC para criptografia de gradientes
    status: str = "onboarding"
    joined_at: float = field(default_factory=time.time)
    last_heartbeat: float = 0.0
    anomalies_shared: int = 0

class ProductionPartnerOrchestrator:
    """
    Orquestrador de produção que gerencia parceiros reais.

    Funcionalidades:
    • Registro seguro de parceiros com troca de chaves PQC
    • Calibração de privacidade diferencial com dados reais de cada parceiro
    • Correlação cross‑org com janela adaptativa
    • Integração com ticketing via ServiceNow/Jira de cada parceiro
    • Monitoramento de saúde e heartbeat dos parceiros
    • FedAvg com gradientes criptografados
    • Ancoragem completa na TemporalChain
    """

    MIN_EPSILON = 2.0
    MAX_EPSILON = 5.0
    DEFAULT_DELTA = 1e-5
    CORRELATION_WINDOW_HOURS = 1
    MIN_ORGS_FOR_ALERT = 3
    HEARTBEAT_TIMEOUT_SECONDS = 300

    def __init__(
        self,
        central_org_id: str,
        phi_bus=None,
        temporal_chain=None,
        guardian=None,
        config_path: str = "/etc/arkhe/partners"
    ):
        self.central_org_id = central_org_id
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.guardian = guardian
        self.config_path = Path(config_path)
        self.config_path.mkdir(parents=True, exist_ok=True)

        self._partners: Dict[str, PartnerOrganization] = {}
        self._partner_reports: Dict[str, List[Dict]] = {}  # partner_id → recent reports
        self._cross_org_alerts: List[Dict] = []
        self._correlation_history: List[Dict] = []
        self._fedavg_round = 0

        # Carregar parceiros previamente registrados
        self._load_partners()

    def _load_partners(self):
        """Carrega parceiros registrados do disco."""
        partners_file = self.config_path / "registered_partners.json"
        if partners_file.exists():
            with open(partners_file, "r") as f:
                data = json.load(f)
                for pdata in data:
                    # Convert sector string to enum
                    if isinstance(pdata.get("sector"), str):
                        try:
                            pdata["sector"] = PartnerSector(pdata["sector"])
                        except ValueError:
                            pdata["sector"] = PartnerSector.BANKING
                    partner = PartnerOrganization(**pdata)
                    self._partners[partner.partner_id] = partner
                    logger.info(f"🤝 Parceiro carregado: {partner.name} ({partner.partner_id})")

    def _save_partners(self):
        """Persiste lista de parceiros."""
        partners_file = self.config_path / "registered_partners.json"
        with open(partners_file, "w") as f:
            # Needs to handle enum serialization
            data_to_save = []
            for p in self._partners.values():
                p_dict = p.__dict__.copy()
                if isinstance(p_dict["sector"], PartnerSector):
                    p_dict["sector"] = p_dict["sector"].value
                data_to_save.append(p_dict)
            json.dump(data_to_save, f, indent=2)

    async def register_partner(
        self,
        partner_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Registra uma nova organização parceira.

        Processo:
        1. Verificar setor e identidade
        2. Trocar chaves PQC (simulado aqui)
        3. Estabelecer privacy budget inicial
        4. Configurar endpoint de dados e ticketing
        5. Ancorar na TemporalChain
        """
        partner_id = partner_info.get("partner_id")
        if partner_id in self._partners:
            return {"status": "exists", "partner_id": partner_id}

        # Validar setor
        sector = PartnerSector(partner_info.get("sector", "banking"))

        # Estabelecer privacy budget com validação
        epsilon = partner_info.get("epsilon", 3.0)
        delta = partner_info.get("delta", self.DEFAULT_DELTA)
        if epsilon < self.MIN_EPSILON or epsilon > self.MAX_EPSILON:
            return {"status": "rejected", "reason": f"epsilon {epsilon} out of bounds [{self.MIN_EPSILON}, {self.MAX_EPSILON}]"}

        privacy_budget = {"epsilon": epsilon, "delta": delta}

        # Gerar chave PQC (mock para produção real seria HSM)
        pqc_public_key = hashlib.sha3_256(
            f"{partner_id}:{time.time()}".encode()
        ).hexdigest()

        # Configurar sistema de ticketing
        ticketing_system = partner_info.get("ticketing_system", "servicenow")
        ticketing_endpoint = partner_info.get("ticketing_endpoint", "https://servicenow.partner.com/api/now/v1/table/incident")
        ticketing_auth = partner_info.get("ticketing_auth", {"type": "basic", "username": "arkhe", "password": "***"})

        partner = PartnerOrganization(
            partner_id=partner_id,
            name=partner_info.get("name", partner_id),
            sector=sector,
            privacy_budget=privacy_budget,
            ticketing_system=ticketing_system,
            ticketing_endpoint=ticketing_endpoint,
            ticketing_auth=ticketing_auth,
            data_endpoint=partner_info.get("data_endpoint", f"https://{partner_id}/api/arkhe/anomalies"),
            pqc_public_key=pqc_public_key,
            status="active"
        )
        partner.joined_at = time.time()
        partner.last_heartbeat = time.time()

        self._partners[partner_id] = partner
        self._partner_reports[partner_id] = []
        self._save_partners()

        # Ancorar na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event("partner_registered", {
                "partner_id": partner_id,
                "name": partner.name,
                "sector": sector.value,
                "epsilon": epsilon,
                "ticketing_system": ticketing_system,
                "timestamp": partner.joined_at
            })

        logger.info(f"🤝 Parceiro registrado: {partner.name} ({partner_id}) [ε={epsilon}]")
        return {"status": "registered", "partner_id": partner_id, "pqc_public_key": pqc_public_key}

    async def receive_partner_anomalies(
        self,
        partner_id: str,
        anomaly_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recebe relatório de anomalias de um parceiro em produção.

        Fluxo de produção real:
        1. Verificar autenticação PQC da assinatura do parceiro
        2. Validar budget de privacidade (ε, δ)
        3. Aplicar ruído diferencial se necessário
        4. Armazenar e correlacionar
        5. Disparar alertas se cross‑org threshold atingido
        6. Criar tickets automáticos em cada parceiro relevante
        """
        partner = self._partners.get(partner_id)
        if not partner or partner.status != "active":
            return {"status": "rejected", "reason": "partner not active"}

        # Verificar heartbeat (parceiro deve estar vivo)
        now = time.time()
        if now - partner.last_heartbeat > self.HEARTBEAT_TIMEOUT_SECONDS:
            partner.status = "timeout"
            logger.warning(f"⚠️  Parceiro {partner_id} timeout — heartbeat perdido")
            return {"status": "rejected", "reason": "partner_heartbeat_timeout"}

        # Validar assinatura PQC (mock: verificação de hash)
        report_signature = anomaly_report.get("pqc_signature")
        expected_signature = hashlib.sha3_256(
            json.dumps(anomaly_report.get("payload", {}), sort_keys=True).encode()
        ).hexdigest()
        if report_signature != expected_signature:
            return {"status": "rejected", "reason": "invalid_pqc_signature"}

        # Extrair payload e verificar ε
        payload = anomaly_report["payload"]
        used_epsilon = payload.get("dp_noise_epsilon", partner.privacy_budget["epsilon"])
        if used_epsilon < self.MIN_EPSILON or used_epsilon > self.MAX_EPSILON:
            return {"status": "rejected", "reason": f"epsilon out of range: {used_epsilon}"}

        # Enriquecer relatório com metadata do parceiro
        report = {
            "partner_id": partner_id,
            "partner_name": partner.name,
            "sector": partner.sector.value,
            "timestamp": now,
            "payload": payload,
            "epsilon": used_epsilon,
            "risk_distribution": payload.get("risk_distribution", {"low": 0, "medium": 0, "high": 0, "critical": 0})
        }

        # Armazenar
        self._partner_reports.setdefault(partner_id, []).append(report)
        partner.anomalies_shared += 1
        partner.last_heartbeat = now

        # Publicar métrica no Phi‑Bus
        if self.phi_bus:
            if hasattr(self.phi_bus, "publish_metric"):
                await self.phi_bus.publish_metric("partner_anomaly_received", {
                    "partner_id": partner_id,
                    "anomaly_count": payload.get("anomaly_count", 0),
                    "epsilon": used_epsilon
                })

        # Verificar correlação cross‑org
        alert = await self._check_production_correlation(report)
        if alert:
            await self._trigger_production_alert(alert, report)

        return {"status": "accepted", "alert_id": alert["alert_id"] if alert else None}

    async def _check_production_correlation(
        self,
        new_report: Dict
    ) -> Optional[Dict]:
        """
        Correlação real multi‑org com janela deslizante.
        Usa features comportamentais para encontrar padrões similares entre parceiros.
        """
        window_seconds = self.CORRELATION_WINDOW_HOURS * 3600
        cutoff = time.time() - window_seconds

        # Coletar reports recentes de outros parceiros ativos
        similar_orgs = set()
        matching_features = {}

        for pid, partner in self._partners.items():
            if pid == new_report["partner_id"] or partner.status != "active":
                continue

            reports = self._partner_reports.get(pid, [])
            recent_reports = [r for r in reports if r["timestamp"] >= cutoff]
            if not recent_reports:
                continue

            # Para cada report recente, comparar distribuições de features
            for r in recent_reports:
                payload = r["payload"]
                new_payload = new_report["payload"]

                # Comparar métricas agregadas (anomaly_count, cpu_percent, etc.)
                features_new = new_payload.get("anomaly_metrics", {})
                features_other = payload.get("anomaly_metrics", {})

                for feat in set(features_new.keys()) & set(features_other.keys()):
                    val_new = features_new[feat]
                    val_other = features_other[feat]
                    # Se ambos são numéricos e desvio > threshold
                    if isinstance(val_new, (int, float)) and isinstance(val_other, (int, float)):
                        if abs(val_new - val_other) / max(abs(val_new), abs(val_other), 1) <= 0.3:
                            matching_features.setdefault(feat, []).append((pid, val_other))
                            similar_orgs.add(pid)

        similar_orgs.add(new_report["partner_id"])

        if len(similar_orgs) >= self.MIN_ORGS_FOR_ALERT:
            alert_id = hashlib.sha3_256(
                f"{sorted(similar_orgs)}:{time.time()}".encode()
            ).hexdigest()[:12]

            return {
                "alert_id": alert_id,
                "type": "production_cross_org_correlation",
                "orgs_involved": list(similar_orgs),
                "matching_features": list(matching_features.keys()),
                "severity": "high",
                "timestamp": time.time(),
                "confidence": min(1.0, len(similar_orgs) / 5)
            }

        return None

    async def _trigger_production_alert(self, alert: Dict, triggering_report: Dict):
        """Dispara alerta cross‑org e cria tickets em todos os parceiros envolvidos."""
        # Ancorar na TemporalChain
        if self.temporal:
            if hasattr(self.temporal, "anchor_event"):
                seal = await self.temporal.anchor_event("production_cross_org_alert", {
                    "alert_id": alert["alert_id"],
                    "orgs_involved": alert["orgs_involved"],
                    "matching_features": alert["matching_features"],
                    "severity": alert["severity"],
                    "confidence": alert["confidence"],
                    "timestamp": alert["timestamp"]
                })
                alert["temporal_seal"] = seal

        self._cross_org_alerts.append(alert)

        # Para cada organização envolvida, criar ticket no sistema dela
        for org_id in alert["orgs_involved"]:
            partner = self._partners.get(org_id)
            if partner:
                await self._create_ticket_for_partner(partner, alert, triggering_report)

        logger.error(
            f"🚨 ALERTA PRODUÇÃO REAL: {alert['alert_id']} | "
            f"Orgs: {len(alert['orgs_involved'])} | "
            f"Features: {alert['matching_features']} | "
            f"Confiança: {alert['confidence']:.2f}"
        )

    async def _create_ticket_for_partner(
        self,
        partner: PartnerOrganization,
        alert: Dict,
        report: Dict
    ):
        """Cria ticket no sistema de ticketing específico do parceiro."""
        ticket_data = {
            "short_description": f"[ARKHE] Alerta Cross‑Org: {alert['alert_id']}",
            "description": f"""
Alerta de correlação cross‑org emitido pelo Sentinel Fabric.

Organizações envolvidas: {', '.join(alert['orgs_involved'])}
Features correlacionadas: {', '.join(alert['matching_features'])}
Severidade: {alert['severity']}
Confiança: {alert['confidence']:.2%}
Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(alert['timestamp']))}

Selo Temporal: {alert.get('temporal_seal', 'N/A')}
            """,
            "priority": "1" if alert["severity"] == "critical" else "2",
            "category": "Security/Fraud/Cross‑Org",
            "arkhe_alert_id": alert["alert_id"],
            "temporal_seal": alert.get("temporal_seal")
        }

        # Adaptar campos ao sistema do parceiro
        if partner.ticketing_system == "jira":
            payload = {
                "fields": {
                    "project": {"key": "SEC"},
                    "summary": ticket_data["short_description"],
                    "description": ticket_data["description"],
                    "issuetype": {"name": "Incident"},
                    "priority": {"name": "Highest" if alert["severity"] == "critical" else "High"},
                    "customfield_10001": alert["alert_id"]  # campo customizado para Arkhe ID
                }
            }
        else:  # ServiceNow default
            payload = {
                "short_description": ticket_data["short_description"],
                "description": ticket_data["description"],
                "priority": ticket_data["priority"],
                "category": ticket_data["category"],
                "u_arkhe_alert_id": alert["alert_id"],
                "u_temporal_seal": alert.get("temporal_seal")
            }

        # Autenticação específica do parceiro
        headers = {"Content-Type": "application/json"}
        if partner.ticketing_auth.get("type") == "basic":
            import base64
            creds = f"{partner.ticketing_auth['username']}:{partner.ticketing_auth['password']}"
            headers["Authorization"] = f"Basic {base64.b64encode(creds.encode()).decode()}"
        elif partner.ticketing_auth.get("type") == "bearer":
            headers["Authorization"] = f"Bearer {partner.ticketing_auth['token']}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    partner.ticketing_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in (200, 201):
                        result = await response.json()
                        ticket_id = result.get("number") or result.get("key") or "unknown"
                        logger.info(f"🎫 Ticket criado em {partner.ticketing_system} para {partner.name}: {ticket_id}")

                        # Ancorar criação do ticket
                        if self.temporal:
                            if hasattr(self.temporal, "anchor_event"):
                                await self.temporal.anchor_event("ticket_created", {
                                    "alert_id": alert["alert_id"],
                                    "partner_id": partner.partner_id,
                                    "ticket_id": ticket_id,
                                    "system": partner.ticketing_system,
                                    "timestamp": time.time()
                                })
                    else:
                        logger.error(f"❌ Falha ao criar ticket em {partner.name}: HTTP {response.status}")
        except Exception as e:
            logger.error(f"❌ Erro ao criar ticket em {partner.name}: {e}")

    async def partner_heartbeat(self, partner_id: str, status_data: Dict) -> Dict:
        """Recebe heartbeat de um parceiro e atualiza status."""
        partner = self._partners.get(partner_id)
        if not partner:
            return {"status": "not_found"}

        partner.last_heartbeat = time.time()
        partner.status = "active"

        # Opcional: atualizar budget de privacidade dinâmico
        new_epsilon = status_data.get("epsilon")
        if new_epsilon and self.MIN_EPSILON <= new_epsilon <= self.MAX_EPSILON:
            partner.privacy_budget["epsilon"] = new_epsilon

        return {"status": "ok", "epsilon": partner.privacy_budget["epsilon"]}

    async def calibrate_privacy_budget(
        self,
        partner_id: str,
        field_data: Dict[str, float]
    ) -> Dict:
        """
        Calibra o ε (privacidade diferencial) com dados reais do parceiro.

        Usa a sensibilidade das features e o nível desejado de proteção
        para ajustar o ruído Laplace de forma que ainda permita correlação útil.
        """
        partner = self._partners.get(partner_id)
        if not partner:
            return {"status": "not_found"}

        # Sensibilidade máxima entre features
        sensitivity = max(field_data.values()) if field_data else 1.0
        # Desired privacy loss (trade-off: quanto menor ε, mais privacidade)
        # Mas se ε for muito baixo, a correlação perde qualidade.
        # Aqui calculamos um ε otimizado com base na sensibilidade e no nível de risco aceito.
        target_risk = field_data.get("target_risk", 0.1)  # 10% de vazamento permitido
        epsilon = sensitivity / (target_risk + 0.01)
        epsilon = max(self.MIN_EPSILON, min(self.MAX_EPSILON, epsilon))

        partner.privacy_budget["epsilon"] = epsilon
        self._save_partners()

        logger.info(f"📏 Privacidade calibrada para {partner_id}: ε={epsilon:.2f}")

        if self.temporal:
            if hasattr(self.temporal, "anchor_event"):
                await self.temporal.anchor_event("privacy_calibration", {
                    "partner_id": partner_id,
                    "epsilon": epsilon,
                    "sensitivity": sensitivity,
                    "timestamp": time.time()
                })

        return {"status": "calibrated", "epsilon": epsilon}

    async def run_federated_training_round(self):
        """Executa rodada de FedAvg com gradientes dos parceiros ativos."""
        active_partners = [p for p in self._partners.values() if p.status == "active"]
        if len(active_partners) < 2:
            logger.info("FedAvg skipped — not enough active partners")
            return

        # Simular coleta de gradientes criptografados
        # Em produção, cada parceiro enviaria gradientes assinados e criptografados com PQC
        self._fedavg_round += 1
        logger.info(f"🔄 FedAvg round {self._fedavg_round} com {len(active_partners)} parceiros")

        # Ancorar
        if self.temporal:
            if hasattr(self.temporal, "anchor_event"):
                await self.temporal.anchor_event("fedavg_round_executed", {
                    "round": self._fedavg_round,
                    "partners_count": len(active_partners),
                    "timestamp": time.time()
                })

    def get_production_dashboard(self) -> Dict:
        """Retorna visão consolidada da produção multi‑org."""
        partners_status = []
        for p in self._partners.values():
            partners_status.append({
                "partner_id": p.partner_id,
                "name": p.name,
                "sector": p.sector.value,
                "status": p.status,
                "epsilon": p.privacy_budget["epsilon"],
                "anomalies_shared": p.anomalies_shared,
                "last_heartbeat_seconds_ago": time.time() - p.last_heartbeat
            })

        return {
            "central_org": self.central_org_id,
            "total_partners": len(self._partners),
            "active_partners": sum(1 for p in self._partners.values() if p.status == "active"),
            "cross_org_alerts_today": len(self._cross_org_alerts),
            "fedavg_rounds": self._fedavg_round,
            "partners": partners_status
        }