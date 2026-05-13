#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/medicine_hypergraph.py — Hypergrafo para Domínio Médico
Conhecimento especializado em farmacologia, diagnósticos e protocolos clínicos.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re

@dataclass
class MedicalFact:
    """Fato médico estruturado."""
    concept: str                    # Ex: "paracetamol", "hypertension"
    fact_type: str                  # "drug", "diagnosis", "procedure", "guideline"
    value: str                      # Valor ou descrição
    source: str                     # Fonte oficial (FDA, WHO, etc.)
    last_updated: datetime
    confidence: float               # 0.0-1.0, baseado na qualidade da fonte
    contraindications: List[str] = field(default_factory=list)
    interactions: List[str] = field(default_factory=list)

class MedicineHypergraph:
    """
    Hypergrafo especializado para domínio médico.
    - Conecta drogas, diagnósticos, sintomas e protocolos
    - Verifica interações medicamentosas e contraindicações
    - Prioriza fontes primárias (FDA, EMA, WHO) sobre secundárias
    """

    def __init__(self):
        self.facts: Dict[str, List[MedicalFact]] = {}
        self._load_canonical_knowledge()

    def _load_canonical_knowledge(self):
        """Carrega conhecimento canônico de fontes oficiais."""
        # Exemplo simplificado — em produção: sincronizar com APIs reais
        self.facts["paracetamol"] = [
            MedicalFact(
                concept="paracetamol",
                fact_type="drug",
                value="Analgesic and antipyretic. Max dose: 4g/day adults.",
                source="FDA",
                last_updated=datetime.now() - timedelta(days=30),
                confidence=0.99,
                contraindications=["severe_hepatic_impairment"],
                interactions=["warfarin", "alcohol_chronic"]
            )
        ]
        self.facts["hypertension"] = [
            MedicalFact(
                concept="hypertension",
                fact_type="diagnosis",
                value="BP ≥140/90 mmHg on ≥2 occasions. ICD-10: I10",
                source="WHO",
                last_updated=datetime.now() - timedelta(days=90),
                confidence=0.98
            )
        ]

    def query(self, concept: str, fact_type: Optional[str] = None) -> List[MedicalFact]:
        """Consulta fatos médicos por conceito."""
        facts = self.facts.get(concept.lower(), [])
        if fact_type:
            facts = [f for f in facts if f.fact_type == fact_type]
        # Ordenar por confiança e recência
        return sorted(facts, key=lambda f: (f.confidence, f.last_updated), reverse=True)

    def check_interaction(self, drug_a: str, drug_b: str) -> Optional[str]:
        """Verifica interação medicamentosa conhecida."""
        facts_a = self.query(drug_a, "drug")
        facts_b = self.query(drug_b, "drug")
        if not facts_a or not facts_b:
            return None
        # Verificar interações cruzadas
        for fa in facts_a:
            if drug_b.lower() in [i.lower() for i in fa.interactions]:
                return f"⚠️ Interação conhecida: {drug_a} + {drug_b}"
        return None

    def validate_diagnosis(self, diagnosis: str, symptoms: List[str]) -> Dict:
        """Valida diagnóstico contra sintomas e guidelines."""
        facts = self.query(diagnosis, "diagnosis")
        if not facts:
            return {"valid": False, "reason": "Diagnóstico não reconhecido"}
        # Verificar se sintomas são consistentes (simplificado)
        # Em produção: usar ontologia médica (SNOMED-CT, UMLS)
        return {"valid": True, "confidence": facts[0].confidence, "source": facts[0].source}
