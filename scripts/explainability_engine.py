# explainability_engine.py — Geração de explicações em linguagem natural

import asyncio
import json
import hashlib
import logging
import time
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime

from audit_logger import AuditRecord, DecisionType, AuditLogger
from compliance_engine import ComplianceEngine


class ExplanationPersona(Enum):
    """Personas para adaptação da explicação."""
    TECHNICAL = auto()      # Engenheiro: detalhes técnicos completos
    REGULATORY = auto()     # DPO/Auditor: conformidade e evidência
    EXECUTIVE = auto()      # Gestor: risco e impacto de negócio
    CITIZEN = auto()        # Público: linguagem simples e direitos


@dataclass
class ExplanationComponent:
    """Componente estruturado de uma explicação."""
    component_type: str  # "trigger", "logic", "data", "confidence", "impact", "recourse"
    technical_content: Dict[str, Any]  # Dados técnicos originais
    natural_language: Dict[ExplanationPersona, str]   # Traduções por persona
    confidence_score: Optional[float] = None  # Confiança nesta explicação


@dataclass
class GeneratedExplanation:
    """Explicação completa gerada para uma decisão."""
    decision_id: str
    persona: ExplanationPersona
    summary: str  # Resumo em 1-2 frases
    detailed_explanation: str  # Explicação completa
    components: List[ExplanationComponent]
    recourse_options: List[str]  # Como contestar/revisar
    verification_hash: str  # Hash para vincular ao AuditLedger
    generated_at: float
    model_version: str  # Versão do gerador de explicações


class ExplainabilityEngine:
    """
    Motor de geração de explicações em linguagem natural adaptadas por persona.
    """

    # Templates de explicação por tipo de decisão e persona
    EXPLANATION_TEMPLATES: Dict[DecisionType, Dict[ExplanationPersona, str]] = {
        DecisionType.PROACTIVE_ALERT: {
            ExplanationPersona.CITIZEN: """
Sua solicitação foi analisada por nosso sistema automatizado de proteção.
Detectamos um padrão que pode indicar risco à sua privacidade ({risk_description}).
Por precaução, tomamos a ação {action_taken} para proteger seus dados.

Confiança: {confidence_natural}.
Se acredita que esta decisão foi incorreta, você pode:
{recourse_options}
            """,
            ExplanationPersona.REGULATORY: """
Decisão automatizada registrada sob ID {decision_id}.
Base legal: {regulatory_basis}.
Gatilho: métrica {metric_name} apresentou valor {metric_value}, abaixo do threshold {threshold} com confiança {confidence}.
Ação tomada: {action_taken}.
Evidências: hash {evidence_hash}, assinatura {signature}.
Conformidade: {compliance_status}.
            """,
        },
        DecisionType.RECOVERY_ACTION: {
            ExplanationPersona.EXECUTIVE: """
Ação de recuperação automática executada para mitigar risco operacional.
Risco identificado: {risk_description} (impacto estimado: {impact_estimate}).
Ação tomada: {action_taken}, resultando em melhoria de Ω de {omega_delta}.
Custo da ação: {action_cost}.
Recomendação: {recommendation}.
            """,
        },
    }

    # Mapeamento de scores técnicos para linguagem natural
    CONFIDENCE_TRANSLATIONS = {
        (0.9, 1.01): "confiança muito alta",
        (0.7, 0.9): "confiança alta",
        (0.5, 0.7): "confiança moderada",
        (0.3, 0.5): "confiança baixa",
        (0.0, 0.3): "confiança muito baixa"
    }

    # Opções de recurso por framework regulatório
    RECOURSE_OPTIONS = {
        "LGPD": [
            "Solicitar revisão humana através do canal de privacidade: privacy@empresa.com",
            "Registrar reclamação na ANPD dentro de 30 dias",
            "Acessar seus dados e a lógica da decisão via portal do titular"
        ],
        "GDPR": [
            "Request human review via DPO contact: dpo@company.com",
            "Lodge a complaint with your national supervisory authority",
            "Access your data and the decision logic via subject access request"
        ],
    }

    def __init__(self, audit_logger: AuditLogger, compliance_engine: ComplianceEngine):
        self.audit = audit_logger
        self.compliance = compliance_engine
        self.explanation_log: List[GeneratedExplanation] = []

    async def generate_explanation(
        self,
        decision_id: str,
        persona: ExplanationPersona,
        include_technical_details: bool = False
    ) -> GeneratedExplanation:
        """Gera explicação em linguagem natural para uma decisão registrada."""
        # Recupera registro técnico do AuditLedger
        record = await self.audit.get_decision(decision_id)
        if not record:
            raise ValueError(f"Decision {decision_id} not found in audit ledger")

        # Decompõe decisão em componentes explicáveis
        components = await self._decompose_decision(record)

        # Gera resumo e explicação detalhada por persona
        summary = self._generate_summary(record, persona)
        detailed = await self._generate_detailed_explanation(record, components, persona)

        # Prepara opções de recurso baseado em compliance tags
        recourse = self._prepare_recourse_options(record.compliance_tags)

        # Gera hash de verificação para vincular explicação ao registro
        verification_data = {
            "decision_id": decision_id,
            "persona": persona.name,
            "summary": summary,
            "components": [c.technical_content for c in components],
            "generated_at": time.time()
        }
        verification_hash = hashlib.sha256(
            json.dumps(verification_data, sort_keys=True, default=str).encode()
        ).hexdigest()

        # Cria explicação gerada
        explanation = GeneratedExplanation(
            decision_id=decision_id,
            persona=persona,
            summary=summary,
            detailed_explanation=detailed,
            components=components,
            recourse_options=recourse,
            verification_hash=verification_hash,
            generated_at=time.time(),
            model_version="ExplainabilityEngine_v1.0"
        )

        # Registra explicação no log (para auditoria)
        self.explanation_log.append(explanation)

        logging.info(f"[EXPLAIN] Explicação gerada para {decision_id} (persona: {persona.name})")
        return explanation

    async def _decompose_decision(self, record: AuditRecord) -> List[ExplanationComponent]:
        """Decompõe registro técnico em componentes explicáveis."""
        components = []

        # Componente: Gatilho (o que disparou a decisão)
        trigger_comp = ExplanationComponent(
            component_type="trigger",
            technical_content=record.context.get("trigger", {}),
            natural_language={
                ExplanationPersona.CITIZEN: f"Detectamos {record.context.get('trigger_description', 'um padrão de risco')}",
                ExplanationPersona.REGULATORY: f"Gatilho: {record.context.get('trigger_metric')} = {record.context.get('trigger_value')} (threshold: {record.context.get('threshold')})",
                ExplanationPersona.EXECUTIVE: f"Risco identificado: {record.context.get('risk_description', 'anomalia operacional')}",
                ExplanationPersona.TECHNICAL: json.dumps(record.context.get("trigger", {}), indent=2)
            }
        )
        components.append(trigger_comp)

        # Componente: Lógica (qual regra/modelo foi aplicado)
        logic_comp = ExplanationComponent(
            component_type="logic",
            technical_content={
                "model_version": record.model_version,
                "rule_applied": record.context.get("rule_applied"),
                "features_used": record.context.get("features_used", [])
            },
            natural_language={
                ExplanationPersona.CITIZEN: "Nosso sistema de proteção aplicou regras automatizadas para analisar sua situação",
                ExplanationPersona.REGULATORY: f"Modelo {record.model_version} aplicou regra {record.context.get('rule_applied')} com features {record.context.get('features_used', [])}",
                ExplanationPersona.EXECUTIVE: f"Algoritmo {record.model_version} avaliou {len(record.context.get('features_used', []))} indicadores de risco",
                ExplanationPersona.TECHNICAL: f"Model: {record.model_version}\nRule: {record.context.get('rule_applied')}\nFeatures: {record.context.get('features_used', [])}"
            }
        )
        components.append(logic_comp)

        # Componente: Confiança (score e margem de erro)
        confidence = record.context.get("confidence", 0.5)
        confidence_natural = self._translate_confidence(confidence)
        confidence_comp = ExplanationComponent(
            component_type="confidence",
            technical_content={"score": confidence, "margin_of_error": 0.1},
            natural_language={
                ExplanationPersona.CITIZEN: f"Confiança: {confidence_natural}",
                ExplanationPersona.REGULATORY: f"Confidence score: {confidence:.2f} (margem de erro: ±0.1)",
                ExplanationPersona.EXECUTIVE: f"Confiança na decisão: {confidence_natural} (score: {confidence:.2f})",
                ExplanationPersona.TECHNICAL: f"Confidence: {confidence:.3f} ± 0.1"
            },
            confidence_score=confidence
        )
        components.append(confidence_comp)

        # Componente: Impacto (mudança em Ω, riscos/benefícios)
        impact = record.expected_impact
        impact_comp = ExplanationComponent(
            component_type="impact",
            technical_content=impact,
            natural_language={
                ExplanationPersona.CITIZEN: f"Esta ação visa proteger seus dados, com benefício estimado de {impact.get('benefit', 'alto')} e risco de {impact.get('risk', 'baixo')}",
                ExplanationPersona.REGULATORY: f"Impacto: benefício={impact.get('benefit')}, risco={impact.get('risk')}, valor líquido={impact.get('net_value')}",
                ExplanationPersona.EXECUTIVE: f"ROI estimado: {impact.get('net_value', 0):.2f} (benefício: {impact.get('benefit')}, risco: {impact.get('risk')})",
                ExplanationPersona.TECHNICAL: json.dumps(impact, indent=2)
            }
        )
        components.append(impact_comp)

        return components

    def _translate_confidence(self, score: float) -> str:
        """Traduz score numérico de confiança para linguagem natural."""
        for (low, high), label in self.CONFIDENCE_TRANSLATIONS.items():
            if low <= score < high:
                return label
        return "confiança desconhecida"

    def _generate_summary(self, record: AuditRecord, persona: ExplanationPersona) -> str:
        """Gera resumo de 1-2 frases para a explicação."""
        decision_type = record.decision_type.name
        if persona == ExplanationPersona.CITIZEN:
            return f"Sistema automatizado tomou decisão de {decision_type.lower().replace('_', ' ')} para proteger seus dados."
        elif persona == ExplanationPersona.REGULATORY:
            return f"Decisão {decision_type} registrada em {datetime.fromtimestamp(record.timestamp).isoformat()} com conformidade {record.compliance_tags}."
        elif persona == ExplanationPersona.EXECUTIVE:
            return f"Ação {decision_type} executada com impacto líquido estimado de {record.expected_impact.get('net_value', 'N/A')}."
        else:  # TECHNICAL
            return f"{decision_type} decision logged at {record.timestamp} with hash {record.merkle_root[:12]}..."

    async def _generate_detailed_explanation(
        self,
        record: AuditRecord,
        components: List[ExplanationComponent],
        persona: ExplanationPersona
    ) -> str:
        """Gera explicação detalhada usando templates por persona."""
        # Seleciona template base por tipo de decisão e persona
        template = self.EXPLANATION_TEMPLATES.get(
            record.decision_type, {}
        ).get(persona, "Decisão registrada: {decision_id}")

        # Prepara contexto para preenchimento do template
        compliance_eval = self.compliance.evaluate_compliance(record)
        context = {
            "decision_id": record.decision_id,
            "risk_description": record.context.get("risk_description", "padrão de risco"),
            "action_taken": record.context.get("action_taken", "ação protetiva"),
            "confidence_natural": self._translate_confidence(record.context.get("confidence", 0.5)),
            "recourse_options": "\n".join(self._prepare_recourse_options(record.compliance_tags)),
            "regulatory_basis": ", ".join(record.compliance_tags),
            "metric_name": record.context.get("trigger_metric", "Ω-score"),
            "metric_value": record.context.get("trigger_value", "N/A"),
            "threshold": record.context.get("threshold", "N/A"),
            "confidence": f"{record.context.get('confidence', 0.5):.2f}",
            "evidence_hash": record.merkle_root or "N/A",
            "signature": record.signature[:16] + "..." if record.signature else "N/A",
            "compliance_status": "Conforme" if all(compliance_eval.values()) else "Não conforme",
            "impact_estimate": record.expected_impact.get("net_value", "N/A"),
            "omega_delta": record.context.get("omega_delta", "N/A"),
            "action_cost": record.context.get("action_cost", "N/A"),
            "recommendation": record.context.get("recommendation", "Monitorar evolução"),
        }

        # Preenche template com contexto
        explanation = template.format(**context)

        # Adiciona componentes detalhados se persona for técnica
        if persona == ExplanationPersona.TECHNICAL:
            explanation += "\n\nComponentes Técnicos:\n"
            for comp in components:
                explanation += f"\n{comp.component_type.upper()}:\n"
                explanation += json.dumps(comp.technical_content, indent=2, default=str)

        return explanation.strip()

    def _prepare_recourse_options(self, compliance_tags: List[str]) -> List[str]:
        """Prepara lista de opções de recurso baseado em tags de compliance."""
        options = []
        for tag in compliance_tags:
            framework = tag.split("_")[0]  # ex: "LGPD_art18" → "LGPD"
            if framework in self.RECOURSE_OPTIONS:
                options.extend(self.RECOURSE_OPTIONS[framework])
        return list(set(options)) if options else ["Contate nosso DPO para mais informações."]
