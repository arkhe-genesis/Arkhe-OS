"""
Base class para regras de compliance regulatório.
Cada jurisdição (HIPAA, GDPR, ANVISA, LGPD) implementa suas regras específicas.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum, auto
import hashlib
import json
from datetime import datetime

class ComplianceLevel(Enum):
    """Níveis de severidade para violações de compliance."""
    CRITICAL = "critical"    # Violação que exige parada imediata
    HIGH = "high"           # Violação que exige correção em 24h
    MEDIUM = "medium"       # Violação que exige plano de correção
    LOW = "low"             # Observação para melhoria contínua
    INFO = "info"           # Informação para auditoria

class Jurisdiction(Enum):
    """Jurisdições regulatórias suportadas."""
    HIPAA_US = "hipaa_us"           # Health Insurance Portability and Accountability Act
    GDPR_EU = "gdpr_eu"             # General Data Protection Regulation
    ANVISA_BR = "anvisa_brazil"     # Agência Nacional de Vigilância Sanitária
    LGPD_BR = "lgpd_brazil"         # Lei Geral de Proteção de Dados
    FDA_US = "fda_us"               # Food and Drug Administration (ensaios clínicos)

@dataclass
class ComplianceRule:
    """Representação de uma regra de compliance."""
    rule_id: str
    jurisdiction: Jurisdiction
    name: str
    description: str
    condition: Callable[[Dict], bool]  # Condição de ativação
    requirement: Callable[[Dict], bool]  # Requisito a ser satisfeito
    severity: ComplianceLevel
    remediation: str  # Instruções para corrigir violação
    references: List[str] = field(default_factory=list)  # Referências legais (ex: "45 CFR 164.312(a)(1)")

    def evaluate(self, system_state: Dict) -> tuple[bool, Optional[str]]:
        """
        Avalia a regra contra o estado do sistema.

        Returns:
            (compliant, violation_message):
            - compliant=True se regra satisfeita
            - violation_message descreve a violação se aplicável
        """
        if not self.condition(system_state):
            # Regra não se aplica a este estado
            return True, None

        if self.requirement(system_state):
            return True, None
        else:
            return False, f"Violação: {self.name} - {self.remediation}"

    def to_circuit_input(self, system_state: Dict) -> Dict:
        """Converte estado do sistema para inputs do circuito ZK."""
        # Em produção: compilar condition/requirement para circuito aritmético
        return {
            "rule_id": self.rule_id,
            "jurisdiction": self.jurisdiction.value,
            "inputs": {k: str(v) for k, v in system_state.items()
                      if isinstance(v, (str, int, float, bool))}
        }

@dataclass
class ComplianceResult:
    """Resultado da avaliação de compliance."""
    jurisdiction: Jurisdiction
    rules_evaluated: int
    rules_passed: int
    rules_failed: int
    violations: List[Dict]  # Lista de violações com detalhes
    zk_proof_hash: Optional[str] = None  # Hash do proof de compliance
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_compliant(self) -> bool:
        """Verifica se todas as regras foram satisfeitas."""
        return self.rules_failed == 0

    def to_report(self) -> Dict:
        """Gera relatório estruturado para auditoria."""
        return {
            "jurisdiction": self.jurisdiction.value,
            "compliance_status": "COMPLIANT" if self.is_compliant else "NON_COMPLIANT",
            "summary": {
                "total_rules": self.rules_evaluated,
                "passed": self.rules_passed,
                "failed": self.rules_failed,
            },
            "violations": [
                {
                    "rule_id": v["rule_id"],
                    "severity": v["severity"],
                    "description": v["description"],
                    "remediation": v["remediation"],
                }
                for v in self.violations
            ],
            "proof_reference": self.zk_proof_hash,
            "audit_timestamp": self.timestamp,
        }
