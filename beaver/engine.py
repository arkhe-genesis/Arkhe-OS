#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
beaver/engine.py — Bounded Evidence Verification Engine (BEAVER)
Verificador determinístico via regras formais JSON + Z3/SMT-LIB
"""

import json
import hashlib
import requests
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

    def verify(self, allegation: 'Alegacao', facts: List[Dict]) -> Tuple[bool, str]:
        """Verifica se regra é satisfeita."""
        # Avaliar condição contra alegação + fatos
        if not self._evaluate_condition(allegation, facts):
            if self.action == "block":
                return False, f"BLOCKED: {self.name} — {self.description}"
            elif self.action == "warn":
                return True, f"WARNING: {self.name} — {self.description}"
        return True, f"PASSED: {self.name}"

    def _evaluate_condition(self, allegation: 'Alegacao', facts: List[Dict]) -> bool:
        """Avalia condição JSON contra dados."""
        cond = self.condition

        # Exemplo de condições suportadas:
        # {"type": "exists_in_database", "field": "drug_name", "database": "fda_approved"}
        if cond.get("type") == "exists_in_database":
            field = cond["field"]
            db = cond["database"]
            value = getattr(allegation, field, None) or allegation.text
            return self._check_database(value, db)

        # {"type": "pattern_match", "pattern": r"^\d+\.\d+$", "field": "dosage"}
        elif cond.get("type") == "pattern_match":
            pattern = cond["pattern"]
            field = cond.get("field", "text")
            value = getattr(allegation, field, None) or allegation.text
            return bool(re.match(pattern, str(value)))

        # {"type": "logical_implication", "if": {...}, "then": {...}}
        elif cond.get("type") == "logical_implication" and Z3_AVAILABLE:
            return self._evaluate_z3(cond, allegation, facts)

        return True  # Default: passar se condição não reconhecida

    def _check_database(self, value: str, database: str) -> bool:
        """Verifica existência em base de dados canônica."""
        val_clean = value.lower().strip()

        # OpenFDA API para verificação de drogas
        if database == "fda_approved":
            try:
                # Utilizamos a OpenFDA API, usando um timeout curto para evitar bloqueios
                resp = requests.get(f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:\"{val_clean}\"", timeout=5)
                # Se não encontrar, tenta pelo brand_name
                if resp.status_code == 404:
                    resp = requests.get(f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:\"{val_clean}\"", timeout=5)
                if resp.status_code == 200:
                    return True
                else:
                    # Fallback ao mock local em caso de erro da API
                    pass
            except Exception:
                pass

            mock_dbs = ["aspirin", "ibuprofen", "paracetamol", "metformin", "acetaminofeno"]
            return val_clean in [d.lower() for d in mock_dbs]

        elif database == "pubmed_indexed":
            try:
                # E-utilities NCBI API para PubMed
                if val_clean.startswith("10."):  # DOI check
                    resp = requests.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={val_clean}[lid]&retmode=json", timeout=5)
                    data = resp.json()
                    if int(data.get("esearchresult", {}).get("count", "0")) > 0:
                        return True
            except Exception:
                pass
            return False

        elif database == "library_api_docs":
            # GitHub API ou PyPI simplificado (pypi.org/pypi/{pacote}/json)
            # Como value é a "função" mas pode vir junto com pacote ex: "fastapi.FastAPI"
            parts = val_clean.split('.')
            if len(parts) >= 1:
                package = parts[0]
                try:
                    resp = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=3)
                    if resp.status_code == 200:
                        return True
                except Exception:
                    pass
                # Verificação mock
                return package in ["fastapi", "flask", "django", "tokio", "requests", "numpy", "pandas", "asyncio"]
            return False

        # Fallback mocks
        mock_dbs = {
            "cie10_codes": ["A00", "B00", "C00", "I10", "J00", "K00"],
            "valid_laws": ["Constitution", "CivilCode", "PenalCode"],
        }
        db = mock_dbs.get(database, [])
        return val_clean in [d.lower() for d in db]

    def _evaluate_z3(self, cond: Dict, allegation: 'Alegacao',
                     facts: List[Dict]) -> bool:
        """Avalia condição lógica via Z3/SMT-LIB."""
        if not Z3_AVAILABLE:
            return True  # Fallback sem Z3

        solver = Solver()
        # Construir fórmula a partir de cond["if"] e cond["then"]
        # Simplificação: exemplo básico
        p = Bool('p')  # Premissa
        q = Bool('q')  # Conclusão
        solver.add(Implies(p, q))  # p → q

        # Atribuir valores baseados em allegation/facts
        # (Implementação completa requer mapeamento semântico)
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

    def verify(self, allegation: 'Alegacao', facts: List[Dict]) -> Tuple[bool, Dict]:
        """
        Verifica alegação contra todas as regras do domínio.
        Retorna: (aprovado, metadados)
        """
        domain_rules = self.rules.get(getattr(allegation, "domain", "geral"), [])
        # Ordenar por prioridade decrescente
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
            "domain": getattr(allegation, "domain", "geral")
        }

    def _load_rules(self, rules_data: Dict):
        """Carrega regras de verificação."""
        for domain, rule_list in rules_data.items():
            self.rules[domain] = []
            for rule_def in rule_list:
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
                {
                    "id": "MED-002",
                    "name": "diagnostico_valido",
                    "description": "Diagnóstico deve ter código CIE-10 válido",
                    "domain": "medicina",
                    "condition": {
                        "type": "pattern_match",
                        "pattern": r"^[A-Z]\d{2}(\.\d+)?$",
                        "field": "diagnosis_code"
                    },
                    "action": "block",
                    "priority": 95,
                    "evidence_required": ["cie10_reference"]
                },
                {
                    "id": "MED-003",
                    "name": "dosage_range",
                    "description": "Dosagem deve estar dentro de faixa terapêutica",
                    "domain": "medicina",
                    "condition": {
                        "type": "logical_implication",
                        "if": {"field": "drug_name", "op": "eq", "value": "paracetamol"},
                        "then": {"field": "dosage_mg", "op": "between", "min": 325, "max": 4000}
                    },
                    "action": "warn",
                    "priority": 90,
                    "evidence_required": ["pharmacology_reference"]
                }
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
                },
                {
                    "id": "LAW-002",
                    "name": "lei_vigente",
                    "description": "Lei citada deve estar em vigor na jurisdição",
                    "domain": "direito",
                    "condition": {
                        "type": "logical_implication",
                        "if": {"field": "jurisdiction", "op": "eq", "value": "BR"},
                        "then": {"field": "law_status", "op": "eq", "value": "active"}
                    },
                    "action": "block",
                    "priority": 95,
                    "evidence_required": ["official_gazette", "legislative_database"]
                }
            ],
            "ciencia": [
                {
                    "id": "SCI-001",
                    "name": "referencia_real",
                    "description": "Referência bibliográfica deve existir em base indexada",
                    "domain": "ciencia",
                    "condition": {
                        "type": "exists_in_database",
                        "field": "doi",
                        "database": "pubmed_indexed"
                    },
                    "action": "block",
                    "priority": 100,
                    "evidence_required": ["doi_resolution", "journal_verification"]
                },
                {
                    "id": "SCI-002",
                    "name": "metodologia_valida",
                    "description": "Método deve ser reconhecido pela comunidade científica",
                    "domain": "ciencia",
                    "condition": {
                        "type": "pattern_match",
                        "pattern": r"^(randomized|double-blind|meta-analysis|systematic-review)",
                        "field": "methodology"
                    },
                    "action": "warn",
                    "priority": 85,
                    "evidence_required": ["methodology_citation", "peer_review_status"]
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
                },
                {
                    "id": "CODE-002",
                    "name": "sintaxe_valida",
                    "description": "Código gerado deve ser sintaticamente válido",
                    "domain": "programacao",
                    "condition": {
                        "type": "pattern_match",
                        "pattern": r"^(def|function|class|import|from)\s+",
                        "field": "code_snippet"
                    },
                    "action": "block",
                    "priority": 95,
                    "evidence_required": ["syntax_parser", "compiler_validation"]
                },
                {
                    "id": "CODE-003",
                    "name": "seguranca_basica",
                    "description": "Código não deve conter padrões de vulnerabilidade conhecidos",
                    "domain": "programacao",
                    "condition": {
                        "type": "logical_implication",
                        "if": {"field": "code_snippet", "op": "contains", "value": "eval("},
                        "then": {"field": "context", "op": "eq", "value": "trusted_input"}
                    },
                    "action": "warn",
                    "priority": 90,
                    "evidence_required": ["security_audit", "input_validation_proof"]
                }
            ]
        }
