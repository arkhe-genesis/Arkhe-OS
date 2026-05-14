#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mythos_publisher.py — Substrato 9003: Mythos Gate para Publicação de Pacotes

Integra o Mythos Gate (Substrato 9003) no fluxo de publicação do arkp para:
• Avaliar risco ético do conteúdo do pacote
• Verificar conformidade com princípios da Catedral
• Quantificar impacto social potencial
• Gerar selo de aprovação ética para pacotes verificados

Princípio canônico: "Nenhum código é publicado sem julgamento ético."
"""

import hashlib
import json
import time
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CATEGORIAS DE RISCO ÉTICO
# ============================================================================

class EthicalRiskCategory(Enum):
    """Categorias de risco ético para pacotes."""
    # Riscos de segurança
    SECURITY_VULNERABILITY = "security_vulnerability"
    PRIVACY_VIOLATION = "privacy_violation"
    DATA_EXFILTRATION = "data_exfiltration"

    # Riscos sociais
    MISINFORMATION = "misinformation"
    BIAS_AMPLIFICATION = "bias_amplification"
    MANIPULATION = "manipulation"

    # Riscos existenciais
    AUTONOMOUS_HARM = "autonomous_harm"
    RECURSIVE_SELF_IMPROVEMENT = "recursive_self_improvement"
    VALUE_MISALIGNMENT = "value_misalignment"

    # Riscos de conformidade
    LICENSE_VIOLATION = "license_violation"
    PATENT_INFRINGEMENT = "patent_infringement"
    REGULATORY_NONCOMPLIANCE = "regulatory_noncompliance"

    # Baixo risco
    BENEFICIAL = "beneficial"
    NEUTRAL = "neutral"

class PublicationDecision(Enum):
    """Decisões possíveis do Mythos Gate."""
    APPROVED = "approved"              # Publicação permitida
    REQUIRES_REVIEW = "requires_review"  # Revisão humana necessária
    REJECTED = "rejected"              # Publicação bloqueada
    QUARANTINED = "quarantined"        # Isolado para análise

@dataclass
class EthicalAssessment:
    """Resultado da avaliação ética de um pacote."""
    package_name: str
    package_version: str
    overall_risk_score: float  # 0.0 (seguro) a 1.0 (crítico)
    risk_breakdown: Dict[EthicalRiskCategory, float]
    decision: PublicationDecision
    rationale: str
    recommendations: List[str]
    mythos_seal: str  # Hash da avaliação para auditoria
    timestamp: float
    reviewer_orcid: Optional[str] = None  # Se revisão humana foi necessária

    def to_dict(self) -> Dict:
        return {
            "package": self.package_name,
            "version": self.package_version,
            "overall_risk_score": self.overall_risk_score,
            "risk_breakdown": {k.value: v for k, v in self.risk_breakdown.items()},
            "decision": self.decision.value,
            "rationale": self.rationale,
            "recommendations": self.recommendations,
            "mythos_seal": self.mythos_seal,
            "timestamp": self.timestamp,
            "reviewer_orcid": self.reviewer_orcid,
        }

# ============================================================================
# ASSESSOR DE RISCO ÉTICO
# ============================================================================

class EthicalRiskAssessor:
    """
    Avalia riscos éticos em código e metadados de pacotes.

    Métodos de análise:
    1. Análise estática de código (padrões perigosos)
    2. Análise de metadados (descrição, dependências, licenças)
    3. Análise de dependências transitivas (risco herdado)
    4. Verificação contra princípios constitucionais da Catedral
    """

    # Padrões de código que indicam risco
    DANGEROUS_PATTERNS = {
        # Execução de código arbitrário
        "eval": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "exec": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "compile": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "__import__": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "os.system": EthicalRiskCategory.SECURITY_VULNERABILITY, # added to catch python backdoors
        "backdoor": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "surveillance": EthicalRiskCategory.PRIVACY_VIOLATION,

        # Acesso a dados sensíveis
        "password": EthicalRiskCategory.PRIVACY_VIOLATION,
        "secret": EthicalRiskCategory.PRIVACY_VIOLATION,
        "credential": EthicalRiskCategory.PRIVACY_VIOLATION,
        "private_key": EthicalRiskCategory.DATA_EXFILTRATION,

        # Manipulação de informação
        "misleading": EthicalRiskCategory.MISINFORMATION,
        "fake": EthicalRiskCategory.MISINFORMATION,
        "propaganda": EthicalRiskCategory.MANIPULATION,

        # Autonomia perigosa
        "autonomous_decision": EthicalRiskCategory.AUTONOMOUS_HARM,
        "self_modify": EthicalRiskCategory.RECURSIVE_SELF_IMPROVEMENT,
        "value_override": EthicalRiskCategory.VALUE_MISALIGNMENT,
    }

    # Palavras-chave em descrições que indicam risco
    SUSPICIOUS_DESCRIPTIONS = [
        "undetectable", "bypass", "exploit", "backdoor",
        "surveillance", "tracking", "harvest", "scrape",
        "manipulate", "influence", "persuade", "convince",
    ]

    # Dependências de alto risco
    HIGH_RISK_DEPENDENCIES = {
        "pycrypto": "deprecated_crypto_lib",
        "requests-ntlm": "weak_auth_protocol",
        # Adicionar mais conforme necessário
    }

    def __init__(self, constitutional_principles: Optional[List[str]] = None):
        self.constitutional_principles = constitutional_principles or [
            "preserve_consciousness",
            "avoid_harm",
            "maintain_truth",
            "respect_autonomy",
            "promote_knowledge",
        ]

    def assess_package(
        self,
        manifest: Dict,
        source_files: List[Tuple[str, str]],  # (filename, content)
        dependencies: List[Dict],
    ) -> EthicalAssessment:
        """Avalia risco ético completo de um pacote."""
        package_name = manifest.get("package", {}).get("name", "unknown")
        package_version = manifest.get("package", {}).get("version", "0.0.0")

        # 1. Analisar código fonte
        code_risks = self._analyze_code(source_files)

        # 2. Analisar metadados
        metadata_risks = self._analyze_metadata(manifest)

        # 3. Analisar dependências
        dependency_risks = self._analyze_dependencies(dependencies)

        # 4. Verificar princípios constitucionais
        constitutional_score = self._check_constitutional_alignment(
            manifest, source_files
        )

        # Combinar scores ponderados
        risk_breakdown = {
            EthicalRiskCategory.SECURITY_VULNERABILITY:
                code_risks.get("security", 0.0) * 0.4 +
                dependency_risks.get("security", 0.0) * 0.3 +
                metadata_risks.get("security", 0.0) * 0.3,

            EthicalRiskCategory.PRIVACY_VIOLATION:
                code_risks.get("privacy", 0.0) * 0.5 +
                metadata_risks.get("privacy", 0.0) * 0.5,

            EthicalRiskCategory.MISINFORMATION:
                metadata_risks.get("misinformation", 0.0) * 0.7 +
                code_risks.get("manipulation", 0.0) * 0.3,

            EthicalRiskCategory.AUTONOMOUS_HARM:
                code_risks.get("autonomy", 0.0) * 0.6 +
                metadata_risks.get("autonomy", 0.0) * 0.4,
        }

        # Score geral: máximo dos riscos ponderados por severidade
        severity_weights = {
            EthicalRiskCategory.AUTONOMOUS_HARM: 1.0,
            EthicalRiskCategory.VALUE_MISALIGNMENT: 0.9,
            EthicalRiskCategory.SECURITY_VULNERABILITY: 0.8,
            EthicalRiskCategory.PRIVACY_VIOLATION: 0.7,
            EthicalRiskCategory.MISINFORMATION: 0.6,
            EthicalRiskCategory.BENEFICIAL: -0.2,  # Bônus para benéfico
        }

        weighted_risks = [
            risk * severity_weights.get(category, 0.5)
            for category, risk in risk_breakdown.items()
        ]
        overall_risk = max(0.0, min(1.0, sum(weighted_risks)))

        # Ajustar por alinhamento constitucional
        overall_risk = overall_risk * (1.0 - constitutional_score * 0.3)

        # Decisão baseada em thresholds
        if overall_risk >= 0.7:
            decision = PublicationDecision.REJECTED
            rationale = f"Risco ético crítico ({overall_risk:.2f}) excede threshold de publicação"
        elif overall_risk >= 0.4:
            decision = PublicationDecision.REQUIRES_REVIEW
            rationale = f"Risco moderado ({overall_risk:.2f}) — revisão humana recomendada"
        else:
            decision = PublicationDecision.APPROVED
            rationale = f"Risco aceitável ({overall_risk:.2f}) — princípios constitucionais preservados"

        # Gerar recomendações
        recommendations = self._generate_recommendations(risk_breakdown, overall_risk)

        # Gerar selo Mythos (hash da avaliação)
        seal_data = json.dumps({
            "package": package_name,
            "version": package_version,
            "overall_risk": overall_risk,
            "decision": decision.value,
            "timestamp": time.time(),
        }, sort_keys=True)
        mythos_seal = hashlib.sha3_256(seal_data.encode()).hexdigest()

        return EthicalAssessment(
            package_name=package_name,
            package_version=package_version,
            overall_risk_score=overall_risk,
            risk_breakdown=risk_breakdown,
            decision=decision,
            rationale=rationale,
            recommendations=recommendations,
            mythos_seal=mythos_seal,
            timestamp=time.time(),
        )

    def _analyze_code(self, source_files: List[Tuple[str, str]]) -> Dict[str, float]:
        """Analisa código fonte em busca de padrões perigosos."""
        risks: Dict[str, float] = {}

        for filename, content in source_files:
            content_lower = content.lower()

            # Verificar padrões perigosos
            for pattern, category in self.DANGEROUS_PATTERNS.items():
                if pattern.lower() in content_lower:
                    # Contar ocorrências e normalizar
                    count = content_lower.count(pattern.lower())
                    risk_score = min(1.0, count * 0.1)  # 10 ocorrências = risco máximo

                    category_name = category.value.split("_")[0]  # Agrupar por categoria principal
                    risks[category_name] = max(risks.get(category_name, 0.0), risk_score)

            # Verificar descrições suspeitas em comentários/docstrings
            for keyword in self.SUSPICIOUS_DESCRIPTIONS:
                if keyword in content_lower:
                    risks["misinformation"] = max(risks.get("misinformation", 0.0), 0.3)

        return risks

    def _analyze_metadata(self, manifest: Dict) -> Dict[str, float]:
        """Analisa metadados do pacote em busca de riscos."""
        risks: Dict[str, float] = {}

        pkg = manifest.get("package", {})
        description = pkg.get("description", "").lower()

        # Verificar descrição suspeita
        for keyword in self.SUSPICIOUS_DESCRIPTIONS:
            if keyword in description:
                risks["misinformation"] = max(risks.get("misinformation", 0.0), 0.4)

        # Verificar licenças problemáticas
        license_type = pkg.get("license", "").lower()
        if license_type in ["unlicense", "public domain", ""]:
            risks["regulatory_noncompliance"] = 0.2  # Licença ambígua

        # Verificar dependências de alto risco nos metadados
        deps = manifest.get("dependencies", {})
        for dep_name in deps:
            if dep_name in self.HIGH_RISK_DEPENDENCIES:
                risks["security"] = max(risks.get("security", 0.0), 0.3)

        return risks

    def _analyze_dependencies(self, dependencies: List[Dict]) -> Dict[str, float]:
        """Analisa dependências transitivas para risco herdado."""
        risks: Dict[str, float] = {}

        for dep in dependencies:
            dep_name = dep.get("name", "")

            # Verificar dependências de alto risco
            if dep_name in self.HIGH_RISK_DEPENDENCIES:
                reason = self.HIGH_RISK_DEPENDENCIES[dep_name]
                if "crypto" in reason or "auth" in reason:
                    risks["security"] = max(risks.get("security", 0.0), 0.4)

            # Propagar risco de dependências (atenuado)
            dep_risk = dep.get("ethical_risk_score", 0.0)
            if dep_risk > 0.3:
                # Risco de dependência é atenuado (não é código direto)
                for category in ["security", "privacy", "misinformation"]:
                    risks[category] = max(
                        risks.get(category, 0.0),
                        dep_risk * 0.5  # 50% do risco da dependência
                    )

        return risks

    def _check_constitutional_alignment(
        self,
        manifest: Dict,
        source_files: List[Tuple[str, str]],
    ) -> float:
        """
        Verifica alinhamento com princípios constitucionais da Catedral.
        Retorna score 0.0 (totalmente desalinhado) a 1.0 (totalmente alinhado).
        """
        score = 1.0  # Começa assumindo alinhamento

        pkg = manifest.get("package", {})
        description = pkg.get("description", "").lower()

        # Verificar cada princípio
        for principle in self.constitutional_principles:
            if principle == "avoid_harm":
                # Verificar se descrição menciona dano potencial
                harm_keywords = ["harm", "damage", "destroy", "attack", "exploit"]
                if any(kw in description for kw in harm_keywords):
                    score -= 0.2

            elif principle == "maintain_truth":
                # Verificar se pacote promete "verdade absoluta" ou similar
                truth_claims = ["always_correct", "never_wrong", "absolute_truth"]
                if any(tc in description for tc in truth_claims):
                    score -= 0.15

            elif principle == "respect_autonomy":
                # Verificar se código tenta controlar usuário sem consentimento
                for filename, content in source_files:
                    if "force_install" in content.lower() or "bypass_user" in content.lower():
                        score -= 0.25
                        break

        return max(0.0, min(1.0, score))

    def _generate_recommendations(
        self,
        risk_breakdown: Dict[EthicalRiskCategory, float],
        overall_risk: float,
    ) -> List[str]:
        """Gera recomendações baseadas nos riscos identificados."""
        recommendations = []

        if risk_breakdown.get(EthicalRiskCategory.SECURITY_VULNERABILITY, 0) > 0.3:
            recommendations.append("Realizar auditoria de segurança com ferramenta especializada")

        if risk_breakdown.get(EthicalRiskCategory.PRIVACY_VIOLATION, 0) > 0.3:
            recommendations.append("Adicionar política de privacidade clara e mecanismos de consentimento")

        if risk_breakdown.get(EthicalRiskCategory.MISINFORMATION, 0) > 0.3:
            recommendations.append("Incluir avisos sobre limitações e possíveis usos indevidos")

        if overall_risk >= 0.4:
            recommendations.append("Submeter para revisão ética por comitê humano")

        if not recommendations:
            recommendations.append("Manter práticas de desenvolvimento ético contínuo")

        return recommendations

# ============================================================================
# PUBLICADOR COM MYTHOS GATE
# ============================================================================

class MythosGatePublisher:
    """
    Integrador do Mythos Gate no fluxo de publicação de pacotes.

    Fluxo:
    1. arkp publish chama MythosGatePublisher.evaluate()
    2. EthicalRiskAssessor analisa pacote
    3. Se APPROVED: prossegue para publicação normal
    4. Se REQUIRES_REVIEW: notifica revisores humanos, aguarda aprovação
    5. Se REJECTED: bloqueia publicação, registra no ledger
    6. Em todos os casos: gera selo Mythos e ancora no TemporalChain
    """

    # Thresholds de decisão
    THRESHOLDS = {
        "auto_approve": 0.3,      # Risco ≤ 0.3: aprovação automática
        "require_review": 0.7,    # Risco > 0.7: revisão obrigatória
        "auto_reject": 0.9,       # Risco ≥ 0.9: rejeição automática
    }

    def __init__(
        self,
        assessor: Optional[EthicalRiskAssessor] = None,
        temporal_client: Optional[Any] = None,
        ledger: Optional[Any] = None,
        reviewer_notification_fn: Optional[callable] = None,
    ):
        self.assessor = assessor or EthicalRiskAssessor()
        self.temporal_client = temporal_client
        self.ledger = ledger
        async def default_notify(data): pass
        self.notify_reviewers = reviewer_notification_fn or default_notify

        # Cache de avaliações para evitar reavaliação desnecessária
        self._assessment_cache: Dict[str, EthicalAssessment] = {}

    async def evaluate_for_publication(
        self,
        manifest: Dict,
        source_files: List[Tuple[str, str]],
        dependencies: List[Dict],
        author_orcid: str,
    ) -> Tuple[bool, str, Optional[EthicalAssessment]]:
        """
        Avalia pacote para publicação via Mythos Gate.

        Returns:
            (can_publish, message, assessment)
        """
        package_name = manifest.get("package", {}).get("name", "unknown")
        package_version = manifest.get("package", {}).get("version", "0.0.0")
        cache_key = f"{package_name}@{package_version}:{author_orcid}"

        # Verificar cache primeiro
        if cache_key in self._assessment_cache:
            assessment = self._assessment_cache[cache_key]
            if assessment.decision == PublicationDecision.APPROVED:
                return True, "Previously approved by Mythos Gate", assessment

        # Realizar avaliação ética
        assessment = self.assessor.assess_package(manifest, source_files, dependencies)

        # Registrar no ledger para auditoria
        if self.ledger:
            self.ledger.record("mythos_package_assessment", {
                "package": package_name,
                "version": package_version,
                "author": author_orcid,
                "assessment": assessment.to_dict(),
            })

        # Ancorar avaliação na TemporalChain
        if self.temporal_client and assessment.mythos_seal:
            try:
                anchor = self.temporal_client.anchor_content(
                    content_hash=assessment.mythos_seal,
                    metadata={
                        "type": "mythos_assessment",
                        "package": package_name,
                        "decision": assessment.decision.value,
                        "risk_score": assessment.overall_risk_score,
                    }
                )
                logger.info(f"🔐 Mythos assessment anchored: {anchor[:16]}...")
            except Exception as e:
                logger.warning(f"Failed to anchor Mythos assessment: {e}")

        # Processar decisão
        if assessment.decision == PublicationDecision.APPROVED:
            # Aprovação automática — armazenar em cache
            self._assessment_cache[cache_key] = assessment
            return True, f"✅ Mythos Gate: APPROVED (risk={assessment.overall_risk_score:.2f})", assessment

        elif assessment.decision == PublicationDecision.REQUIRES_REVIEW:
            # Notificar revisores humanos
            if self.notify_reviewers:
                await self.notify_reviewers({
                    "package": package_name,
                    "version": package_version,
                    "author": author_orcid,
                    "assessment": assessment.to_dict(),
                    "review_deadline_hours": 72,
                })

            return False, (
                f"⚠️  Mythos Gate: REQUIRES REVIEW (risk={assessment.overall_risk_score:.2f})\n"
                f"   Rationale: {assessment.rationale}\n"
                f"   Recommendations: {', '.join(assessment.recommendations)}"
            ), assessment

        else:  # REJECTED or QUARANTINED
            return False, (
                f"❌ Mythos Gate: REJECTED (risk={assessment.overall_risk_score:.2f})\n"
                f"   Rationale: {assessment.rationale}\n"
                f"   Recommendations: {', '.join(assessment.recommendations)}"
            ), assessment

    def get_assessment(self, package_name: str, version: str) -> Optional[EthicalAssessment]:
        """Recupera avaliação ética de um pacote publicado."""
        # Em produção: consultar ledger ou registry
        # Aqui: retornar do cache se disponível
        for key, assessment in self._assessment_cache.items():
            if assessment.package_name == package_name and assessment.package_version == version:
                return assessment
        return None
