# demo_compliance_audit.py — Demonstração do ciclo completo de auditoria e compliance

import asyncio
import logging
import time
import sys
import os

# Adiciona o diretório scripts ao path para importação
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from codex_crystal import CrystalCodexMemory
from audit_logger import AuditLogger, DecisionType
from compliance_engine import ComplianceEngine
from regulatory_playbook import RegulatoryIncidentResponsePlaybook
from explainability_protocol import ExplainabilityProtocol

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_demo():
    logging.info("=== INICIANDO DEMONSTRAÇÃO DO PROTOCOLO FS-51 ===")

    # 1. Setup da Infraestrutura
    codex = CrystalCodexMemory()
    # Chave de 32 bytes para compatibilidade com PyNaCl
    audit = AuditLogger(codex, b"secret_key_arkhe_2024_demo_32bit")
    compliance = ComplianceEngine(audit)
    playbook = RegulatoryIncidentResponsePlaybook(audit, compliance)

    # 2. Simulação de uma Decisão Automatizada Conforme
    logging.info("\n[Cenário 1] Decisão Automatizada Conforme")

    context_alert = {
        "metric": "cathedral_organism_vitality",
        "threshold": 0.85,
        "confidence": 0.88,
        "prediction_horizon": 10
    }

    explanation_nl = ExplainabilityProtocol.translate_decision(
        "PROACTIVE_ALERT",
        context_alert,
        {},
        ["latency_increase (0.45)", "error_rate_spike (0.32)"]
    )

    logging.info(f"Explicação gerada: {explanation_nl}")

    record_ok = await audit.log_decision(
        decision_type=DecisionType.PROACTIVE_ALERT,
        context=context_alert,
        explainability={
            "natural_language": explanation_nl,
            "bias_detected": 0.02
        },
        compliance_tags=["LGPD_art18", "GDPR_art22"],
        expected_impact={"risk_reduction": 0.8}
    )

    status_ok = await compliance.check_decision_compliance(record_ok.decision_id)
    logging.info(f"Conformidade OK: {status_ok['all_compliant']}")

    # 3. Simulação de uma Decisão Não-Conforme (Sem explicabilidade suficiente)
    logging.info("\n[Cenário 2] Decisão Não-Conforme (Violação detectada)")

    record_fail = await audit.log_decision(
        decision_type=DecisionType.RECOVERY_ACTION,
        context={"action_name": "FORCE_REBOOT", "alert_id": "omega_fail"},
        explainability={
            "natural_language": "Curta.", # Muito curta para EXPLAINABILITY_NL
            "bias_detected": 0.45 # Acima do limite para LGPD_art18
        },
        compliance_tags=["LGPD_art18"],
        expected_impact={"risk": 0.5}
    )

    status_fail = await compliance.check_decision_compliance(record_fail.decision_id)
    logging.info(f"Conformidade OK: {status_fail['all_compliant']} | Violações: {status_fail['violations']}")

    # 4. Resposta Automática do Playbook Regulatório
    logging.info("\n[Cenário 3] Resposta do Playbook Regulatório")

    # Simula o monitoramento processando a violação
    await playbook._handle_compliance_incident(record_fail, status_fail["violations"])

    incidents = playbook.get_active_incidents()
    logging.info(f"Incidentes ativos: {len(incidents)}")
    for inc in incidents:
        logging.info(f"Ações de mitigação: {inc['mitigation_actions']}")

    # 5. Relatório Final de Compliance
    logging.info("\n[Relatório Final]")
    report = await compliance.generate_compliance_report(time.time() - 3600, time.time())
    logging.info(f"Taxa de Conformidade: {report['compliance_rate']*100}%")
    logging.info(f"Total de Decisões: {report['total_decisions']}")

    logging.info("\n=== DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO ===")

if __name__ == "__main__":
    asyncio.run(run_demo())
