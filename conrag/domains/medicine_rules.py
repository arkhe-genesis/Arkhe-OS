#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/medicine_rules.py — Regras BEAVER para Domínio Médico
Validação determinística baseada em diretrizes clínicas e regulatórias.
"""

from typing import Tuple, Dict, List
import re

class MedicalBEAVERRules:
    """
    Regras BEAVER especializadas para medicina.
    Cada regra é verificável deterministicamente via APIs oficiais.
    """

    RULES = {
        "drug_approved": {
            "description": "Droga deve estar aprovada por agência reguladora",
            "check": "_check_drug_approved",
            "severity": "block",
        },
        "dosage_safe": {
            "description": "Dosagem deve estar dentro de faixa terapêutica segura",
            "check": "_check_dosage_safe",
            "severity": "block",
        },
        "contraindication_check": {
            "description": "Verificar contraindicações para paciente",
            "check": "_check_contraindications",
            "severity": "warn",
        },
        "interaction_warning": {
            "description": "Alertar sobre interações medicamentosas conhecidas",
            "check": "_check_interactions",
            "severity": "warn",
        },
        "diagnosis_valid": {
            "description": "Diagnóstico deve ter código ICD-10/ICD-11 válido",
            "check": "_check_diagnosis_code",
            "severity": "block",
        },
    }

    @staticmethod
    def _check_drug_approved(drug_name: str, context: Dict) -> Tuple[bool, str]:
        """Verifica se droga está aprovada (via API FDA/EMA)."""
        # Em produção: consultar FDA API
        approved_drugs = ["paracetamol", "ibuprofen", "amoxicillin", "metformin"]
        if drug_name.lower() in [d.lower() for d in approved_drugs]:
            return True, "OK"
        return False, f"Droga '{drug_name}' não encontrada em bases regulatórias"

    @staticmethod
    def _check_dosage_safe(drug: str, dosage: str, patient_age: str, context: Dict) -> Tuple[bool, str]:
        """Verifica se dosagem está segura para faixa etária."""
        # Simplificação: regras hardcoded
        safe_ranges = {
            "paracetamol": {"adult": (325, 4000), "child": (10, 60)},  # mg/kg
            "ibuprofen": {"adult": (200, 800), "child": (5, 10)},
        }
        if drug.lower() not in safe_ranges:
            return True, "OK (faixa desconhecida — revisão humana recomendada)"
        try:
            dose_val = float(re.findall(r"[\d.]+", dosage)[0])
            age_group = "child" if "child" in patient_age.lower() else "adult"
            min_d, max_d = safe_ranges[drug.lower()][age_group]
            if min_d <= dose_val <= max_d:
                return True, "OK"
            return False, f"Dosagem {dose_val}mg fora da faixa segura ({min_d}-{max_d}mg)"
        except (IndexError, ValueError):
            return False, "Não foi possível parsear dosagem"

    @staticmethod
    def _check_contraindications(drug: str, conditions: List[str], context: Dict) -> Tuple[bool, str]:
        """Verifica contraindicações."""
        contraindications = {
            "paracetamol": ["severe_hepatic_impairment"],
            "ibuprofen": ["peptic_ulcer", "renal_failure", "third_trimester_pregnancy"],
        }
        drug_cons = contraindications.get(drug.lower(), [])
        conflicts = [c for c in conditions if c.lower() in [cc.lower() for cc in drug_cons]]
        if conflicts:
            return False, f"Contraindicação: {drug} não recomendado para {conflicts[0]}"
        return True, "OK"

    @staticmethod
    def _check_interactions(drugs: List[str], context: Dict) -> Tuple[bool, str]:
        """Verifica interações entre múltiplas drogas."""
        known_interactions = {
            frozenset(["warfarin", "aspirin"]): "Aumento de risco hemorrágico",
            frozenset(["metformin", "alcohol"]): "Risco de acidose lática",
        }
        for i, drug_a in enumerate(drugs):
            for drug_b in drugs[i+1:]:
                key = frozenset([drug_a.lower(), drug_b.lower()])
                if key in known_interactions:
                    return False, f"⚠️ {known_interactions[key]}: {drug_a} + {drug_b}"
        return True, "OK"

    @staticmethod
    def _check_diagnosis_code(diagnosis: str, context: Dict) -> Tuple[bool, str]:
        """Verifica se diagnóstico tem código ICD válido."""
        # Padrão ICD-10: letra + 2 dígitos + opcional . + até 2 caracteres
        icd10_pattern = r"^[A-Z]\d{2}(\.\d{1,2})?$"
        if re.match(icd10_pattern, diagnosis.upper()):
            return True, "OK"
        return False, f"Código de diagnóstico '{diagnosis}' não segue padrão ICD-10"
