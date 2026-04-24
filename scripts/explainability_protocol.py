# explainability_protocol.py — Protocolo de explicabilidade em linguagem natural

from typing import Dict, Any, List
import logging

class ExplainabilityProtocol:
    """
    Traduz decisões técnicas e métricas de modelos para stakeholders não-técnicos.
    """

    @staticmethod
    def translate_decision(
        decision_type: str,
        context: Dict[str, Any],
        model_metrics: Dict[str, float] = None,
        top_features: List[str] = None
    ) -> str:
        """
        Gera uma explicação em linguagem natural para uma decisão técnica.
        """

        explanation_templates = {
            "PROACTIVE_ALERT": (
                "A Catedral detectou uma tendência de instabilidade no subsistema '{subsystem}'. "
                "Baseado em padrões históricos, há uma probabilidade de {confidence}% de que o Ω-score caia "
                "abaixo do limite de segurança ({threshold}) nos próximos {horizon} minutos. "
                "Os fatores principais que levaram a esta conclusão foram: {features}."
            ),
            "RECOVERY_ACTION": (
                "Para prevenir uma degradação iminente do sistema, a Catedral decidiu aplicar a ação '{action}'. "
                "Esta medida visa reduzir o risco detectado pelo alerta '{alert_id}'. "
                "O impacto esperado é uma melhoria de {omega_delta} no Ω-score vital, "
                "priorizando a continuidade do serviço sobre a carga máxima."
            ),
            "MODEL_PROMOTION": (
                "Um novo modelo de inteligência artificial foi promovido para o subsistema '{metric}'. "
                "O novo modelo (v{new_version}) demonstrou uma melhoria de {improvement}% na precisão "
                "em relação ao modelo anterior (v{old_version}) durante a fase de validação (Shadow Mode). "
                "Esta atualização aumenta a confiabilidade das predições preventivas."
            ),
            "COMPLIANCE_MITIGATION": (
                "Uma ação de correção foi executada automaticamente devido a uma inconformidade regulatória. "
                "O registro de decisão '{original_id}' foi identificado como violando os requisitos de {violations}. "
                "Como medida de segurança, o sistema realizou '{mitigation}' para garantir a proteção de dados e a governança."
            )
        }

        template = explanation_templates.get(decision_type, "Decisão técnica executada para manutenção da estabilidade do sistema.")

        # Preenchimento inteligente baseado no contexto
        features_str = ", ".join(top_features) if top_features else "múltiplas métricas de latência e erro"

        try:
            if decision_type == "PROACTIVE_ALERT":
                return template.format(
                    subsystem=context.get("metric", "desconhecido"),
                    confidence=int(context.get("confidence", 0.8) * 100),
                    threshold=context.get("threshold", 0.85),
                    horizon=context.get("prediction_horizon", 10),
                    features=features_str
                )
            elif decision_type == "RECOVERY_ACTION":
                return template.format(
                    action=context.get("action_name", "redução de carga"),
                    alert_id=context.get("alert_id", "tendência_negativa"),
                    omega_delta=context.get("expected_improvement", 0.05)
                )
            elif decision_type == "MODEL_PROMOTION":
                return template.format(
                    metric=context.get("metric", "Ω-core"),
                    new_version=context.get("new_version", "2.0"),
                    old_version=context.get("old_version", "1.9"),
                    improvement=int(context.get("improvement", 0.05) * 100)
                )
            elif decision_type == "COMPLIANCE_MITIGATION":
                return template.format(
                    original_id=context.get("original_decision", "N/A"),
                    violations=context.get("violations_str", "conformidade"),
                    mitigation=context.get("mitigation_action", "suspensão da atividade")
                )
        except Exception as e:
            logging.error(f"Erro ao gerar explicação: {e}")
            return "A Catedral executou uma ação técnica baseada em análise de dados para garantir a resiliência."

        return template
