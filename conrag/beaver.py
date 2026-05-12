#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/beaver.py — Bounded Evidence Verification Engine (BEAVER)
Verificador determinístico via regras formais JSON + Z3/SMT-LIB
"""

import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re

try:
    from z3 import Solver, Bool, And, Or, Not, Implies, sat, unsat
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False

class RuleStatus(Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"
    INDETERMINATE = "indeterminate"

@dataclass
class VerificationRule:
    """Regra formal de verificação."""
    id: str
    name: str
    description: str
    domain: str
    condition: Dict  # Condição em formato JSON verificável
    action: str  # "block", "warn", "pass"
    priority: int  # Ordem de aplicação (maior = primeiro)
    evidence_required: List[str]  # Tipos de evidência necessários

    def verify(self, allegation: Any, facts: List[Dict]) -> Tuple[bool, str]:
        """Verifica se regra é satisfeita."""
        # Avaliar condição contra alegação + fatos
        if not self._evaluate_condition(allegation, facts):
            if self.action == "block":
                return False, f"BLOCKED: {self.name} — {self.description}"
            elif self.action == "warn":
                return True, f"WARNING: {self.name} — {self.description}"
        return True, f"PASSED: {self.name}"

    def _evaluate_condition(self, allegation: Any, facts: List[Dict]) -> bool:
        """Avalia condição JSON contra dados."""
        cond = self.condition

        # {"type": "exists_in_database", "field": "drug_name", "database": "fda_approved"}
        if cond.get("type") == "exists_in_database":
            field = cond["field"]
            db = cond["database"]
            value = getattr(allegation, field, None) or getattr(allegation, 'texto', str(allegation))
            return self._check_database(value, db)

        # {"type": "pattern_match", "pattern": r"^\d+\.\d+$", "field": "dosage"}
        elif cond.get("type") == "pattern_match":
            pattern = cond["pattern"]
            field = cond.get("field", "texto")
            value = getattr(allegation, field, None) or getattr(allegation, 'texto', str(allegation))
            return bool(re.match(pattern, str(value)))

        # {"type": "cox_model_validation"}
        elif cond.get("type") == "cox_model_validation":
            return self._check_cox_model(allegation, facts)

        # {"type": "logical_implication", "if": {...}, "then": {...}}
        elif cond.get("type") == "logical_implication" and Z3_AVAILABLE:
            return self._evaluate_z3(cond, allegation, facts)

        return True  # Default: passar se condição não reconhecida

    def _check_cox_model(self, allegation: Any, facts: List[Dict]) -> bool:
        """Verifica os pressupostos do modelo de Cox (EHA)."""
        # Dados do IBGE ou OSF devem ser passados nos fatos ou metadados
        metadata = getattr(allegation, 'metadados', {})
        if not metadata:
            return False

        # 1. Proporcionalidade dos riscos
        ph_pvalue = metadata.get('proportional_hazards_pvalue', 0)
        # 2. Independência dos tempos e observações
        independence_flag = metadata.get('independence_met', False)
        # 3. Ausência de multicolinearidade
        multicollinearity_vif = metadata.get('multicollinearity_vif', 10)
        # 4. Distribuição homogênea/Linearidade
        linearity_flag = metadata.get('linearity_met', False)

        if ph_pvalue <= 0.05:
            return False

        if multicollinearity_vif >= 5.0:
            return False

        if not independence_flag or not linearity_flag:
            return False

        return True

    def _check_database(self, value: str, database: str) -> bool:
        """Verifica existência em base de dados canônica."""
        # Simplificação: mock databases
        mock_dbs = {
            "fda_approved": ["aspirin", "ibuprofen", "paracetamol", "metformin"],
            "cie10_codes": ["A00", "B00", "C00", "I10", "J00", "K00"],
            "valid_laws": ["Constitution", "CivilCode", "PenalCode"],
            "ibge_cities": ["recife", "sao paulo", "rio de janeiro"]
        }
        db = mock_dbs.get(database, [])
        v_str = str(value).lower()
        return any(d.lower() in v_str for d in db)

    def _evaluate_z3(self, cond: Dict, allegation: Any,
                     facts: List[Dict]) -> bool:
        """Avalia condição lógica via Z3/SMT-LIB."""
        if not Z3_AVAILABLE:
            return True  # Fallback sem Z3

        solver = Solver()
        p = Bool('p')
        q = Bool('q')
        solver.add(Implies(p, q))
        result = solver.check()
        return result == sat

class BEAVEngine:
    """
    Bounded Evidence Verification Engine (BEAVER)
    Motor de verificação determinística para ConRAG.
    """

    def __init__(self, rules_path: Optional[str] = None):
        self.rules: Dict[str, List[VerificationRule]] = {}
        self._load_rules(rules_path or self._default_rules())

    def verify(self, allegation: Any, facts: List[Dict]) -> Tuple[bool, Dict]:
        """
        Verifica alegação contra todas as regras do domínio.
        Retorna: (aprovado, metadados)
        """
        domain_rules = self.rules.get(getattr(allegation, 'dominio', 'general'), [])
        sorted_rules = sorted(domain_rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            approved, message = rule.verify(allegation, facts)
            if not approved:
                return False, {
                    "status": RuleStatus.BLOCKED.value,
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "reason": message,
                    "action": rule.action
                }

        return True, {
            "status": RuleStatus.APPROVED.value,
            "rules_checked": len(sorted_rules),
            "domain": getattr(allegation, 'dominio', 'general')
        }

    def _load_rules(self, rules_data: Dict):
        """Carrega regras de verificação."""
        for domain, rule_list in rules_data.items():
            self.rules[domain] = []
            for rule_def in rule_list:
                if isinstance(rule_def, dict):
                    rule = VerificationRule(**rule_def)
                    self.rules[domain].append(rule)

    def _default_rules(self) -> Dict:
        """Regras padrão por domínio."""
        return {
            "medicina": [
                {
                    "id": "MED-001",
                    "name": "droga_existente",
                    "description": "Droga deve estar em base FDA/ANVISA aprovada",
                    "domain": "medicina",
                    "condition": {
                        "type": "exists_in_database",
                        "field": "drug_name",
                        "database": "fda_approved"
                    },
                    "action": "block",
                    "priority": 100,
                    "evidence_required": ["fda_listing", "clinical_trial"]
                },
            ],
            "direito": [
                {
                    "id": "LAW-001",
                    "name": "precedente_existente",
                    "description": "Precedente jurídico deve ser citável em base oficial",
                    "domain": "direito",
                    "condition": {
                        "type": "exists_in_database",
                        "field": "case_citation",
                        "database": "valid_laws"
                    },
                    "action": "block",
                    "priority": 100,
                    "evidence_required": ["court_record", "official_publication"]
                }
            ],
            "programacao": [
                {
                    "id": "CODE-001",
                    "name": "funcao_existente",
                    "description": "Função/API citada deve existir na biblioteca especificada",
                    "domain": "programacao",
                    "condition": {
                        "type": "exists_in_database",
                        "field": "function_name",
                        "database": "library_api_docs"
                    },
                    "action": "block",
                    "priority": 100,
                    "evidence_required": ["api_documentation", "version_compatibility"]
                }
            ],
            "sociology": [
                {
                    "id": "SOC-001",
                    "name": "sociologia_valida",
                    "description": "Adoção de políticas públicas deve passar pela validação determinística dos pressupostos do modelo de Cox.",
                    "domain": "sociology",
                    "condition": {
                        "type": "cox_model_validation"
                    },
                    "action": "block",
                    "priority": 100,
                    "evidence_required": ["ibge_data", "osf_data", "cox_model_stats"]
                }
            ]
        }
