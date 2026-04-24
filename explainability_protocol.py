# explainability_protocol.py — Narrador que traduz decisões em palavras humanas

from typing import Dict, List, Any
from audit_logger import AuditRecord, DecisionType
import logging

class DecisionNarrator:
    """
    Gera explicações em linguagem natural para decisões automatizadas,
    adaptadas ao público-alvo.
    """

    AUDIENCE_TEMPLATES = {
        "EXECUTIVE": {
            "intro": "Uma ação automática foi tomada para {intent}.",
            "impacto": "O impacto esperado é {beneficio} e o serviço {status}.",
            "acao_recomendada": "Nenhuma ação manual é necessária neste momento."
        },
        "TECHNICAL": {
            "intro": "O modelo {modelo} previu que '{metrica}' atingiria {valor_previsto}.",
            "detalhes": "Fatores principais: {fatores}. Confiança: {confianca}%.",
            "resultado": "Após a ação '{acao}', a métrica foi para {valor_final} (Δ={delta})."
        },
        "REGULATORY": {
            "intro": "Decisão automatizada registrada sob o ID {decision_id}.",
            "compliance": "Em conformidade com {compliance_tags}. Viés detectado: {bias}%.",
            "rastreabilidade": "Auditável via hash {hash} no Livro de Bronze."
        },
        "CITIZEN": {
            "intro": "Nossos sistemas identificaram uma situação que precisava de ajuste.",
            "direitos": "Esta ação foi reversível e seus dados não foram utilizados.",
            "contato": "Dúvidas podem ser enviadas para nosso DPO em {dpo_email}."
        }
    }

    def __init__(self, llm_available=False):
        self.llm_available = llm_available

    def generate_narrative(self, decision: AuditRecord, audience: str, lang: str = "pt") -> str:
        """
        Gera uma explicação em linguagem natural para a decisão.
        """
        templates = self.AUDIENCE_TEMPLATES.get(audience, self.AUDIENCE_TEMPLATES["TECHNICAL"])

        # Preenche os templates com dados do registro
        narrative = ""
        if audience == "EXECUTIVE":
            # outcome simulation
            omega_before = decision.context.get("omega_before", 0.9)
            omega_after = decision.context.get("omega_after", 0.95)
            narrative = templates["intro"].format(
                intent="manter a estabilidade do serviço" if omega_after > omega_before else "mitigar uma degradação"
            )
            narrative += " " + templates["impacto"].format(
                beneficio="alto" if decision.expected_impact.get("benefit", 0) > 0.7 else "moderado",
                status="foi estabilizado" if decision.context.get("validation") == "SUCCESS" else "necessita de atenção"
            )
        elif audience == "TECHNICAL":
            narrative = templates["intro"].format(
                modelo=decision.model_version or "v1.0",
                metrica=decision.context.get("trigger_metric", "desconhecida"),
                valor_previsto=decision.context.get("trigger_value", "N/A")
            )
            factors = decision.explainability.get("top_features", [])
            narrative += " " + templates["detalhes"].format(
                fatores=", ".join([f"{f[0]} ({f[1]})" for f in factors]),
                confianca=decision.context.get("confidence", 0) * 100
            )
        elif audience == "REGULATORY":
            narrative = templates["intro"].format(decision_id=decision.decision_id)
            narrative += " " + templates["compliance"].format(
                compliance_tags=", ".join(decision.compliance_tags),
                bias=decision.context.get("bias", 0.0) * 100
            )
            narrative += " " + templates["rastreabilidade"].format(
                hash=decision.merkle_root[:16] if decision.merkle_root else "N/A"
            )
        elif audience == "CITIZEN":
            narrative = templates["intro"]
            narrative += " " + templates["direitos"]
            narrative += " " + templates["contato"].format(dpo_email="dpo@cathedral.ark")
        else:
            narrative = "Explicação para " + audience + " em desenvolvimento."

        # (Opcional) Utilizar LLM para polir a narrativa final
        if self.llm_available:
            narrative = self._polish_with_llm(narrative, audience, lang)

        return narrative

    def _polish_with_llm(self, draft: str, audience: str, lang: str) -> str:
        return draft
