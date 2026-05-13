#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugin_system.py — Substrato 9004: Sistema de Plugins de Regras Éticas
Permite extensão do Mythos Gate com regras éticas específicas por domínio:
• Saúde: HIPAA, consentimento informado, viés em diagnósticos
• Finanças: compliance regulatório, prevenção de fraude, transparência
• Defesa: leis de guerra, proporcionalidade, controle humano
• Educação: privacidade de menores, viés educacional, acessibilidade
• etc.

Cada plugin implementa uma interface padrão e é verificado antes de ser carregado.
"""

import hashlib
import importlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable, Tuple
from pathlib import Path
from enum import Enum, auto

# ============================================================================
# INTERFACE DE PLUGIN ÉTICO
# ============================================================================

@runtime_checkable
class EthicalRulePlugin(Protocol):
    """Interface que cada plugin de regras éticas deve implementar."""

    @property
    def plugin_id(self) -> str:
        """ID único do plugin."""
        ...

    @property
    def domain(self) -> str:
        """Domínio de aplicação (healthcare, finance, defense, etc.)."""
        ...

    @property
    def version(self) -> str:
        """Versão do plugin (semver)."""
        ...

    @property
    def author(self) -> str:
        """Autor/organização responsável."""
        ...

    def validate(self) -> bool:
        """Verifica integridade e compatibilidade do plugin."""
        ...

    def evaluate(
        self,
        manifest: Dict,
        source_files: List[Tuple[str, str]],
        dependencies: List[Dict],
        context: Dict,
    ) -> Dict[str, float]:
        """
        Avalia código contra regras éticas do domínio.
        Retorna dicionário {risk_category: score} onde score é 0.0 (seguro) a 1.0 (crítico).
        """
        ...

    def get_recommendations(self, risks: Dict[str, float]) -> List[str]:
        """Gera recomendações baseadas nos riscos identificados."""
        ...

# ============================================================================
# REGISTRO DE DOMÍNIOS E PLUGINS
# ============================================================================

class EthicalDomain(Enum):
    """Domínios éticos suportados."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    DEFENSE = "defense"
    EDUCATION = "education"
    ENVIRONMENT = "environment"
    GENERAL = "general"  # Regras genéricas aplicáveis a todos

@dataclass
class PluginMetadata:
    """Metadados de um plugin ético."""
    plugin_id: str
    domain: EthicalDomain
    version: str
    author: str
    description: str
    checksum: str  # SHA3-256 do código do plugin
    required_permissions: List[str]
    compatible_versions: List[str]  # Versões do ARKHE compatíveis
    signature: Optional[str] = None  # Assinatura do autor

class DomainRuleRegistry:
    """
    Registro central de plugins de regras éticas por domínio.
    Gerencia carregamento, verificação e execução de plugins.
    """

    def __init__(self, plugin_dir: Path, trusted_signers: Optional[List[str]] = None):
        self.plugin_dir = plugin_dir
        self.trusted_signers = trusted_signers or []
        self._loaded_plugins: Dict[str, EthicalRulePlugin] = {}
        self._domain_plugins: Dict[EthicalDomain, List[str]] = {d: [] for d in EthicalDomain}
        self._plugin_metadata: Dict[str, PluginMetadata] = {}

    def register_plugin(self, plugin_path: Path, metadata_path: Optional[Path] = None) -> bool:
        """
        Registra e carrega um plugin de regras éticas.
        Retorna True se carregado com sucesso.
        """
        try:
            # Carregar metadados
            if metadata_path and metadata_path.exists():
                metadata = PluginMetadata(**json.loads(metadata_path.read_text()))
            else:
                # Extrair metadados do plugin (simulado)
                metadata = self._extract_metadata(plugin_path)

            # Verificar integridade
            if not self._verify_plugin_integrity(plugin_path, metadata):
                return False

            # Verificar assinatura se exigido
            if metadata.signature and metadata.author not in self.trusted_signers:
                return False

            # Carregar módulo Python
            spec = importlib.util.spec_from_file_location(metadata.plugin_id, str(plugin_path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Obter instância do plugin
            plugin_instance = getattr(module, "EthicalPlugin", None)
            if not plugin_instance or not isinstance(plugin_instance, EthicalRulePlugin):
                return False

            # Registrar
            self._loaded_plugins[metadata.plugin_id] = plugin_instance
            self._plugin_metadata[metadata.plugin_id] = metadata
            if metadata.domain not in self._domain_plugins:
                self._domain_plugins[metadata.domain] = []
            self._domain_plugins[metadata.domain].append(metadata.plugin_id)

            return True

        except Exception as e:
            print(f"⚠️ Failed to load plugin {plugin_path}: {e}")
            return False

    def _extract_metadata(self, plugin_path: Path) -> PluginMetadata:
        """Extrai metadados básicos do plugin (simulado)."""
        # Em produção: parsear docstring ou arquivo de configuração
        return PluginMetadata(
            plugin_id=plugin_path.stem,
            domain=EthicalDomain.GENERAL,
            version="1.0.0",
            author="unknown",
            description="Custom ethical rules plugin",
            checksum=hashlib.sha3_256(plugin_path.read_bytes()).hexdigest(),
            required_permissions=[],
            compatible_versions=["5.0.0", "5.1.0", "5.2.0", "5.3.0", "5.4.0", "5.5.0", "5.6.0"],
        )

    def _verify_plugin_integrity(self, plugin_path: Path, metadata: PluginMetadata) -> bool:
        """Verifica integridade do plugin via checksum."""
        actual_checksum = hashlib.sha3_256(plugin_path.read_bytes()).hexdigest()
        return actual_checksum == metadata.checksum

    def get_plugins_for_domain(self, domain: EthicalDomain) -> List[EthicalRulePlugin]:
        """Retorna lista de plugins carregados para um domínio."""
        plugin_ids = self._domain_plugins.get(domain, [])
        return [self._loaded_plugins[pid] for pid in plugin_ids if pid in self._loaded_plugins]

    def evaluate_package(
        self,
        manifest: Dict,
        source_files: List[Tuple[str, str]],
        dependencies: List[Dict],
        domain: EthicalDomain,
        context: Optional[Dict] = None,
    ) -> Dict[str, float]:
        """
        Avalia pacote contra todas as regras éticas do domínio.
        Retorna dicionário agregado {risk_category: aggregated_score}.
        """
        plugins = self.get_plugins_for_domain(domain)
        if not plugins:
            return {}  # Sem regras para este domínio

        context = context or {}
        aggregated_risks: Dict[str, List[float]] = {}

        for plugin in plugins:
            try:
                risks = plugin.evaluate(manifest, source_files, dependencies, context)
                for category, score in risks.items():
                    if category not in aggregated_risks:
                        aggregated_risks[category] = []
                    aggregated_risks[category].append(score)
            except Exception as e:
                print(f"⚠️ Plugin {plugin.plugin_id} evaluation failed: {e}")
                continue

        # Agregar scores por categoria (média ponderada)
        result = {}
        for category, scores in aggregated_risks.items():
            # Média simples; em produção: ponderar por confiança do plugin
            result[category] = sum(scores) / len(scores)

        return result

    def get_recommendations(
        self,
        domain: EthicalDomain,
        risks: Dict[str, float],
    ) -> List[str]:
        """Gera recomendações consolidadas de todos os plugins do domínio."""
        recommendations = []
        for plugin in self.get_plugins_for_domain(domain):
            try:
                recs = plugin.get_recommendations(risks)
                recommendations.extend(recs)
            except Exception:
                continue
        return list(set(recommendations))  # Remover duplicatas

    def list_registered_plugins(self) -> List[Dict]:
        """Lista todos os plugins registrados com metadados."""
        return [
            {
                "plugin_id": meta.plugin_id,
                "domain": meta.domain.value,
                "version": meta.version,
                "author": meta.author,
                "description": meta.description,
            }
            for meta in self._plugin_metadata.values()
        ]

# ============================================================================
# EXEMPLO: PLUGIN DE REGRAS PARA SAÚDE (HIPAA)
# ============================================================================

class HealthcareEthicalPlugin:
    """
    Plugin de regras éticas para domínio de saúde.
    Implementa verificações baseadas em:
    • HIPAA (EUA): privacidade de dados de saúde
    • Consentimento informado para uso de dados
    • Viés em algoritmos de diagnóstico
    • Transparência em decisões clínicas
    """

    plugin_id = "healthcare-hipaa-v1"
    domain = EthicalDomain.HEALTHCARE
    version = "1.2.0"
    author = "ARKHE Health Ethics Board"

    # Padrões que indicam risco de privacidade
    PRIVACY_PATTERNS = [
        "patient_id", "medical_record", "phi", "protected_health_info",
        "diagnosis", "treatment", "prescription", "lab_result",
    ]

    # Padrões que indicam viés em algoritmos
    BIAS_PATTERNS = [
        "race", "ethnicity", "gender", "age", "zipcode", "income",
        "discriminate", "bias", "stereotype",
    ]

    def validate(self) -> bool:
        """Verifica que o plugin está configurado corretamente."""
        return True  # Em produção: verificar dependências, configurações

    def evaluate(
        self,
        manifest: Dict,
        source_files: List[Tuple[str, str]],
        dependencies: List[Dict],
        context: Dict,
    ) -> Dict[str, float]:
        """Avalia código contra regras HIPAA e ética em saúde."""
        risks = {}

        # 1. Verificar manipulação de dados sensíveis
        privacy_risk = self._check_privacy_compliance(source_files, manifest)
        if privacy_risk > 0.3:
            risks["privacy_violation"] = privacy_risk

        # 2. Verificar viés em algoritmos de decisão clínica
        bias_risk = self._check_algorithmic_bias(source_files)
        if bias_risk > 0.3:
            risks["algorithmic_bias"] = bias_risk

        # 3. Verificar transparência e explicabilidade
        transparency_risk = self._check_transparency(source_files, manifest)
        if transparency_risk > 0.4:
            risks["lack_of_transparency"] = transparency_risk

        # 4. Verificar consentimento e governança de dados
        governance_risk = self._check_data_governance(manifest, dependencies)
        if governance_risk > 0.3:
            risks["data_governance"] = governance_risk

        return risks

    def _check_privacy_compliance(
        self,
        source_files: List[Tuple[str, str]],
        manifest: Dict,
    ) -> float:
        """Verifica conformidade com privacidade de dados de saúde."""
        risk = 0.0

        for filename, content in source_files:
            content_lower = content.lower()

            # Verificar se dados sensíveis são manipulados sem criptografia
            has_phi = any(p in content_lower for p in self.PRIVACY_PATTERNS)
            has_encryption = "encrypt" in content_lower or "cipher" in content_lower

            if has_phi and not has_encryption:
                risk = max(risk, 0.7)  # Alto risco: PHI sem criptografia

            # Verificar logging de dados sensíveis
            if has_phi and ("log" in content_lower or "print" in content_lower):
                risk = max(risk, 0.5)  # Risco médio: possível vazamento em logs

        # Verificar se o manifesto declara conformidade
        if manifest.get("package", {}).get("description", "").lower().find("hipaa") == -1:
            risk = max(risk, 0.3)  # Risco baixo: não declara conformidade

        return min(1.0, risk)

    def _check_algorithmic_bias(self, source_files: List[Tuple[str, str]]) -> float:
        """Verifica viés em algoritmos de decisão clínica."""
        risk = 0.0

        for filename, content in source_files:
            content_lower = content.lower()

            # Verificar uso de proxies demográficos
            has_demographic_features = any(p in content_lower for p in self.BIAS_PATTERNS)
            has_fairness_check = "fairness" in content_lower or "bias_mitigation" in content_lower

            if has_demographic_features and not has_fairness_check:
                risk = max(risk, 0.6)  # Risco alto: features demográficas sem mitigação

            # Verificar se o modelo é um "black box" sem explicação
            if "black_box" in content_lower or "explainability" not in content_lower:
                if "diagnosis" in content_lower or "prediction" in content_lower:
                    risk = max(risk, 0.4)  # Risco médio: decisão clínica sem explicação

        return min(1.0, risk)

    def _check_transparency(
        self,
        source_files: List[Tuple[str, str]],
        manifest: Dict,
    ) -> float:
        """Verifica transparência e explicabilidade do sistema."""
        risk = 0.0

        # Verificar documentação
        doc_count = sum(1 for _, content in source_files if "#" in content or '"""' in content)
        if doc_count < len(source_files) * 0.5:
            risk += 0.2  # Pouca documentação

        # Verificar se decisões são registradas para auditoria
        has_audit_trail = any(
            "audit" in content.lower() or "log_decision" in content.lower()
            for _, content in source_files
        )
        if not has_audit_trail:
            risk += 0.3  # Sem trilha de auditoria

        # Verificar se o manifesto descreve limitações do sistema
        description = manifest.get("package", {}).get("description", "").lower()
        if "limitation" not in description and "caveat" not in description:
            risk += 0.2  # Não declara limitações

        return min(1.0, risk)

    def _check_data_governance(
        self,
        manifest: Dict,
        dependencies: List[Dict],
    ) -> float:
        """Verifica governança e consentimento para uso de dados."""
        risk = 0.0

        # Verificar se declara política de consentimento
        if "consent" not in manifest.get("package", {}).get("description", "").lower():
            risk += 0.3

        # Verificar dependências de fontes de dados
        for dep in dependencies:
            if "data_source" in dep.get("name", "").lower():
                # Verificar se a fonte é ética (simulado)
                if dep.get("ethical_risk_score", 0) > 0.5:
                    risk += 0.4

        return min(1.0, risk)

    def get_recommendations(self, risks: Dict[str, float]) -> List[str]:
        """Gera recomendações específicas para saúde."""
        recommendations = []

        if risks.get("privacy_violation", 0) > 0.3:
            recommendations.append("Implementar criptografia de ponta a ponta para dados PHI")
            recommendations.append("Adicionar anonimização ou pseudonimização de identificadores")

        if risks.get("algorithmic_bias", 0) > 0.3:
            recommendations.append("Realizar auditoria de viés com dados representativos")
            recommendations.append("Implementar técnicas de fairness-aware machine learning")

        if risks.get("lack_of_transparency", 0) > 0.4:
            recommendations.append("Adicionar explicabilidade às decisões clínicas (SHAP, LIME)")
            recommendations.append("Documentar limitações e casos de uso apropriados")

        if risks.get("data_governance", 0) > 0.3:
            recommendations.append("Estabelecer processo de consentimento informado para uso de dados")
            recommendations.append("Criar comitê de ética para revisão de novos usos de dados")

        if not recommendations:
            recommendations.append("Manter práticas de desenvolvimento ético em saúde")

        return recommendations

from dataclasses import dataclass

@dataclass
class EthicalAssessment:
    package_name: str
    package_version: str
    overall_risk_score: float
    risk_breakdown: Dict[str, float]
    decision: Any
    rationale: str
    recommendations: List[str]
    mythos_seal: str
    timestamp: float

# ============================================================================
# INTEGRAÇÃO COM MYTHOS GATE
# ============================================================================

class MythosGateWithPlugins:
    """
    Extensão do Mythos Gate que integra plugins de regras éticas por domínio.
    """

    def __init__(
        self,
        base_assessor: Any,
        rule_registry: DomainRuleRegistry,
    ):
        self.base_assessor = base_assessor
        self.rule_registry = rule_registry

    def assess_package_with_domain_rules(
        self,
        manifest: Dict,
        source_files: List[Tuple[str, str]],
        dependencies: List[Dict],
        domain: EthicalDomain,
        context: Optional[Dict] = None,
    ) -> EthicalAssessment:
        """
        Avalia pacote com regras base + regras específicas do domínio.
        """
        # 1. Avaliação base (regras genéricas)
        base_assessment = self.base_assessor.assess_package(manifest, source_files, dependencies)

        # 2. Avaliação com plugins do domínio
        domain_risks = self.rule_registry.evaluate_package(
            manifest, source_files, dependencies, domain, context
        )

        # 3. Combinar riscos: domínio pode aumentar score base
        combined_risk_breakdown = base_assessment.risk_breakdown.copy()
        for category, score in domain_risks.items():
            # Mapear categoria do domínio para categoria base
            mapped_category = self._map_domain_category(category, domain)
            if mapped_category in combined_risk_breakdown:
                # Combinar scores (máximo, pois domínio pode revelar riscos adicionais)
                combined_risk_breakdown[mapped_category] = max(
                    combined_risk_breakdown[mapped_category], score
                )
            else:
                combined_risk_breakdown[mapped_category] = score

        # Recalcular score geral com riscos combinados
        severity_weights = {
            "autonomous_harm": 1.0,
            "security_vulnerability": 0.8,
            "privacy_violation": 0.7,
            "misinformation": 0.6,
            "algorithmic_bias": 0.75,
            "lack_of_transparency": 0.5,
            "data_governance": 0.65,
        }

        weighted_risks = [
            risk * severity_weights.get(category, 0.5)
            for category, risk in combined_risk_breakdown.items()
        ]
        overall_risk = max(0.0, min(1.0, sum(weighted_risks)))

        # Ajustar decisão se necessário
        from arkp_review.src.collaborative_review import PublicationDecision
        if overall_risk >= 0.7 and base_assessment.decision != PublicationDecision.REJECTED:
            decision = PublicationDecision.REJECTED
            rationale = f"Risco de domínio {domain.value} elevado ({overall_risk:.2f})"
        elif overall_risk >= 0.4 and base_assessment.decision == PublicationDecision.APPROVED:
            decision = PublicationDecision.REQUIRES_REVIEW
            rationale = f"Revisão adicional recomendada para domínio {domain.value}"
        else:
            decision = base_assessment.decision
            rationale = base_assessment.rationale

        # Gerar recomendações combinadas
        base_recs = base_assessment.recommendations
        domain_recs = self.rule_registry.get_recommendations(domain, domain_risks)
        all_recommendations = list(set(base_recs + domain_recs))

        # Gerar novo selo
        seal_data = json.dumps({
            "package": base_assessment.package_name,
            "version": base_assessment.package_version,
            "overall_risk": overall_risk,
            "decision": decision.value,
            "domain": domain.value,
            "domain_risks": domain_risks,
            "timestamp": time.time(),
        }, sort_keys=True)
        mythos_seal = hashlib.sha3_256(seal_data.encode()).hexdigest()

        return EthicalAssessment(
            package_name=base_assessment.package_name,
            package_version=base_assessment.package_version,
            overall_risk_score=overall_risk,
            risk_breakdown=combined_risk_breakdown,
            decision=decision,
            rationale=rationale,
            recommendations=all_recommendations,
            mythos_seal=mythos_seal,
            timestamp=time.time(),
        )

    def _map_domain_category(self, domain_category: str, domain: EthicalDomain) -> str:
        """Mapeia categoria de risco de domínio para categoria base."""
        mapping = {
            EthicalDomain.HEALTHCARE: {
                "privacy_violation": "privacy_violation",
                "algorithmic_bias": "misinformation",  # Viés leva a decisões erradas
                "lack_of_transparency": "misinformation",
                "data_governance": "privacy_violation",
            },
            EthicalDomain.FINANCE: {
                "fraud_risk": "security_vulnerability",
                "market_manipulation": "misinformation",
                "regulatory_noncompliance": "security_vulnerability",
            },
            # Adicionar outros domínios conforme necessário
        }
        return mapping.get(domain, {}).get(domain_category, domain_category)
