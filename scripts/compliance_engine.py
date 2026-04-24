# compliance_engine.py — Motor de conformidade regulatória automatizada

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from audit_logger import AuditLogger, AuditRecord, DecisionType

class ComplianceEngine:
    """
    Motor de conformidade que mapeia decisões automatizadas para requisitos regulatórios.
    """

    # Mapeamento: tipo de decisão → requisitos regulatórios aplicáveis
    REGULATORY_MAPPING = {
        DecisionType.PROACTIVE_ALERT: ["LGPD_art18", "GDPR_art22", "ISO27001_A.12.4"],
        DecisionType.RECOVERY_ACTION: ["LGPD_art46", "GDPR_art32", "ISO27001_A.17.1"],
        DecisionType.MODEL_PROMOTION: ["LGPD_art6", "GDPR_art25", "ISO27001_A.18.1"],
        DecisionType.THRESHOLD_ADJUSTMENT: ["LGPD_art18", "GDPR_art22"],
        DecisionType.ROLLBACK_EXECUTION: ["LGPD_art46", "ISO27001_A.17.2"],
        DecisionType.MANUAL_OVERRIDE: ["LGPD_art18", "GDPR_art22", "ISO27001_A.12.4"],
    }

    # Regras de conformidade: funções que avaliam se uma decisão viola requisitos
    COMPLIANCE_RULES: Dict[str, Callable[[AuditRecord], bool]] = {
        "LGPD_art18": lambda record: record.explainability.get("bias_detected", 0.0) < 0.3,
        "GDPR_art22": lambda record: record.context.get("human_in_loop", False) or record.expected_impact.get("risk", 0.0) < 0.2,
        "ISO27001_A.12.4": lambda record: record.signature is not None and len(record.signature) > 0,
        # Regra de explicabilidade: deve haver uma explicação em linguagem natural
        "EXPLAINABILITY_NL": lambda record: len(record.explainability.get("natural_language", "")) > 10
    }

    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger
        self.violation_alerts: List[Dict] = []

    async def evaluate_compliance(self, record: AuditRecord) -> Dict[str, bool]:
        """Avalia conformidade de um registro contra requisitos regulatórios."""
        results = {}

        # Tags explícitas no registro
        tags_to_check = set(record.compliance_tags)

        # Adiciona tags automáticas baseadas no tipo de decisão se não estiverem presentes
        auto_tags = self.REGULATORY_MAPPING.get(record.decision_type, [])
        tags_to_check.update(auto_tags)

        for tag in tags_to_check:
            rule = self.COMPLIANCE_RULES.get(tag)
            if rule:
                try:
                    results[tag] = rule(record)
                except Exception as e:
                    logging.error(f"[COMPLIANCE] Erro ao avaliar regra {tag}: {e}")
                    results[tag] = False
            else:
                # Se não houver regra definida, assume conformidade (ou loga aviso)
                results[tag] = True

        return results

    async def check_decision_compliance(self, decision_id: str) -> Dict[str, Any]:
        """Verifica conformidade de uma decisão específica."""
        record = await self.audit.get_decision(decision_id)
        if not record:
            return {"error": "Decision not found"}

        compliance_results = await self.evaluate_compliance(record)

        return {
            "decision_id": decision_id,
            "decision_type": record.decision_type.name,
            "timestamp": record.timestamp,
            "compliance_results": compliance_results,
            "all_compliant": all(compliance_results.values()),
            "violations": [tag for tag, compliant in compliance_results.items() if not compliant]
        }

    async def generate_compliance_report(
        self,
        start_time: float,
        end_time: float,
        regulatory_framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gera relatório de conformidade."""
        records = await self.audit.query_decisions(
            start_time=start_time,
            end_time=end_time
        )

        compliant_count = 0
        violations = []

        for record in records:
            if regulatory_framework and not any(tag.startswith(regulatory_framework) for tag in record.compliance_tags):
                continue

            results = await self.evaluate_compliance(record)
            if all(results.values()):
                compliant_count += 1
            else:
                violations.append({
                    "decision_id": record.decision_id,
                    "violations": [tag for tag, compliant in results.items() if not compliant]
                })

        total = len(records) if not regulatory_framework else (compliant_count + len(violations))

        return {
            "report_period": {"start": start_time, "end": end_time},
            "regulatory_framework": regulatory_framework or "ALL",
            "total_decisions": total,
            "compliant_decisions": compliant_count,
            "compliance_rate": compliant_count / max(1, total),
            "violations": violations,
            "generated_at": time.time()
        }
