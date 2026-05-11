"""
Compliance Engine: Avalia configurações contra regras regulatórias
e gera proofs criptográficos de conformidade.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib
import json
from datetime import datetime

from .rules.base_rule import ComplianceRule, ComplianceResult, Jurisdiction
from .zk_prover import ZKComplianceProver

@dataclass
class DeploymentConfig:
    """Configuração de deployment a ser validada."""
    deployment_id: str
    regions: List[str]  # Ex: ["us-east-1", "eu-west-1", "sa-east-1"]
    data_classification: Dict[str, bool]  # Ex: {"phi": True, "pii": True, "research": True}
    encryption: Dict[str, any]  # Configurações de criptografia
    access_control: Dict[str, any]  # Configurações de controle de acesso
    audit: Dict[str, any]  # Configurações de auditoria
    retention: Dict[str, int]  # Políticas de retenção por tipo de dado
    integrity: Dict[str, bool] = None
    # ... outros campos de configuração

class ComplianceEngine:
    """Motor principal de avaliação de compliance."""

    def __init__(self, rules_repository: str = "./compliance/rules/"):
        self.rules_repository = rules_repository
        self.zk_prover = ZKComplianceProver()
        self._load_rules()

    def _load_rules(self):
        """Carrega regras de todas as jurisdições suportadas."""
        from .rules import hipaa_rules, gdpr_rules, anvisa_rules, lgpd_rules

        self.rules_by_jurisdiction = {
            Jurisdiction.HIPAA_US: hipaa_rules.HIPAA_RULES,
            Jurisdiction.GDPR_EU: gdpr_rules.GDPR_RULES,
            Jurisdiction.ANVISA_BR: anvisa_rules.ANVISA_RULES,
            Jurisdiction.LGPD_BR: lgpd_rules.LGPD_RULES,
        }

    def evaluate_deployment(self, config: DeploymentConfig) -> Dict[Jurisdiction, ComplianceResult]:
        """
        Avalia uma configuração de deployment contra todas as jurisdições aplicáveis.

        Returns:
            Mapeamento jurisdição → resultado de compliance
        """
        results = {}
        system_state = self._config_to_state(config)

        for jurisdiction, rules in self.rules_by_jurisdiction.items():
            # Filtrar regras aplicáveis à região
            applicable_rules = [r for r in rules if self._applies_to_regions(r, config.regions)]

            violations = []
            passed = 0

            for rule in applicable_rules:
                compliant, violation_msg = rule.evaluate(system_state)
                if compliant:
                    passed += 1
                else:
                    violations.append({
                        "rule_id": rule.rule_id,
                        "severity": rule.severity.value,
                        "description": violation_msg,
                        "remediation": rule.remediation,
                        "reference": rule.references[0] if rule.references else None,
                    })

            # Gerar ZK-proof de compliance (se todas as regras passaram)
            zk_proof_hash = None
            if not violations and applicable_rules: # Only generate proof if there are rules and no violations
                circuit_inputs = [rule.to_circuit_input(system_state) for rule in applicable_rules]
                zk_proof_hash = self.zk_prover.generate_compliance_proof(
                    jurisdiction=jurisdiction,
                    rules=circuit_inputs,
                    system_state_hash=hashlib.sha256(
                        json.dumps(system_state, sort_keys=True).encode()
                    ).hexdigest(),
                )
            # if no applicable rules but requested to generate, create dummy if it's considered passed.
            # Usually if there are no rules, it's considered compliant but we may or may not want a proof.
            # In the user prompt, even regions with stub rules get proofs.
            if not violations and not applicable_rules:
                zk_proof_hash = self.zk_prover.generate_compliance_proof(
                    jurisdiction=jurisdiction,
                    rules=[],
                    system_state_hash=hashlib.sha256(
                        json.dumps(system_state, sort_keys=True).encode()
                    ).hexdigest(),
                )

            results[jurisdiction] = ComplianceResult(
                jurisdiction=jurisdiction,
                rules_evaluated=len(applicable_rules),
                rules_passed=passed,
                rules_failed=len(violations),
                violations=violations,
                zk_proof_hash=zk_proof_hash,
            )

        return results

    def _config_to_state(self, config: DeploymentConfig) -> Dict:
        """Converte configuração de deployment para estado do sistema."""
        return {
            "deployment_id": config.deployment_id,
            "regions": config.regions,
            "data_types": config.data_classification,
            "encryption": config.encryption,
            "access_control": config.access_control,
            "audit": config.audit,
            "integrity": config.integrity or {},
            "retention_policy": config.retention,
            # Adicionar mais campos conforme necessário para avaliação de regras
        }

    def _applies_to_regions(self, rule: ComplianceRule, regions: List[str]) -> bool:
        """Verifica se uma regra se aplica às regiões de deployment."""
        # Lógica simplificada: regras de jurisdição aplicam-se a regiões correspondentes
        region_to_jurisdiction = {
            "us-east-1": Jurisdiction.HIPAA_US,
            "us-west-2": Jurisdiction.HIPAA_US,
            "eu-west-1": Jurisdiction.GDPR_EU,
            "eu-central-1": Jurisdiction.GDPR_EU,
            "sa-east-1": Jurisdiction.ANVISA_BR,  # Brasil
            # "sa-east-1": Jurisdiction.LGPD_BR,    # Brasil (ambas aplicam) - handled below
        }

        for region in regions:
            if region_to_jurisdiction.get(region) == rule.jurisdiction:
                return True
            if region == "sa-east-1" and rule.jurisdiction == Jurisdiction.LGPD_BR:
                 return True
        return False
