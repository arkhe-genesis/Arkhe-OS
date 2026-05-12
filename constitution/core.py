#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
constitution/core.py — Constituição da Catedral
Sistema de princípios em linguagem natural para julgamento interpretável
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import numpy as np

class Veredito(Enum):
    VERIFICADO = "verificado"
    REFUTADO = "refutado"
    INDETERMINADO = "indeterminado"

@dataclass
class Principio:
    """Princípio constitucional interpretável."""
    id: str
    enunciado: str
    descricao: str
    dominio: str
    peso: float
    aplicabilidade: Dict

    def aplicar(self, allegation: 'Alegacao', facts: List[Dict],
                confianca_rlcr: float) -> Tuple[bool, str]:
        if not self._condicoes_aplicaveis(allegation):
            return True, "N/A"

        satisfeito, motivo = self._avaliar(allegation, facts, confianca_rlcr)
        if satisfeito:
            return True, f"✓ {self.enunciado}"
        else:
            return False, f"✗ {self.enunciado}: {motivo}"

    def _condicoes_aplicaveis(self, allegation: 'Alegacao') -> bool:
        if self.dominio == "all":
            return True
        return getattr(allegation, "domain", "geral") == self.dominio

    def _avaliar(self, allegation: 'Alegacao', facts: List[Dict],
                 confianca_rlcr: float) -> Tuple[bool, str]:
        raise NotImplementedError

class PrincipioP1(Principio):
    def __init__(self):
        super().__init__(
            id="P1",
            enunciado="A evidência mais forte prevalece",
            descricao="Quando há evidências conflitantes, a de maior qualidade/força determina o veredito",
            dominio="all",
            peso=1.0,
            aplicabilidade={"min_facts": 2}
        )

    def _avaliar(self, allegation: 'Alegacao', facts: List[Dict],
                 confianca_rlcr: float) -> Tuple[bool, str]:
        if len(facts) < 2:
            return True, "Insuficientes fatos para aplicar P1"
        supports = [f for f in facts if f.get('direction') == 'support']
        refutes = [f for f in facts if f.get('direction') == 'refute']
        if not supports and not refutes:
            return True, "Sem evidência direcional"
        strength_support = np.mean([f.get('evidence_strength', 0.5) for f in supports]) if supports else 0
        strength_refute = np.mean([f.get('evidence_strength', 0.5) for f in refutes]) if refutes else 0
        diff = abs(strength_support - strength_refute)
        if diff < 0.2:
            return False, "Evidências conflitantes com força similar — inconclusivo"
        return True, f"Evidência dominante: {'support' if strength_support > strength_refute else 'refute'} (Δ={diff:.2f})"

class PrincipioP2(Principio):
    def __init__(self):
        super().__init__(
            id="P2",
            enunciado="Incerteza deve ser explicitamente declarada",
            descricao="Quando confiança é intermediária (0.3-0.7), o sistema deve declarar incerteza",
            dominio="all",
            peso=0.9,
            aplicabilidade={}
        )

    def _avaliar(self, allegation: 'Alegacao', facts: List[Dict],
                 confianca_rlcr: float) -> Tuple[bool, str]:
        if 0.3 <= confianca_rlcr <= 0.7:
            return False, "Confiança intermediária sem declaração explícita de incerteza"
        return True, f"Confiança {'alta' if confianca_rlcr > 0.7 else 'baixa'} — incerteza adequadamente expressa"

class PrincipioP3(Principio):
    def __init__(self):
        super().__init__(
            id="P3",
            enunciado="Fontes primárias > secundárias > terciárias",
            descricao="Hierarquia de credibilidade: fontes primárias têm peso maior",
            dominio="all",
            peso=0.8,
            aplicabilidade={"min_sources": 1}
        )

    def _avaliar(self, allegation: 'Alegacao', facts: List[Dict],
                 confianca_rlcr: float) -> Tuple[bool, str]:
        if not facts:
            return False, "Sem fontes para avaliar hierarquia"
        primary = [f for f in facts if f.get('source_type') == 'primary']
        secondary = [f for f in facts if f.get('source_type') == 'secondary']
        tertiary = [f for f in facts if f.get('source_type') == 'tertiary']
        weight = (len(primary) * 1.0 + len(secondary) * 0.6 + len(tertiary) * 0.3) / max(1, len(facts))
        if weight < 0.5 and confianca_rlcr > 0.7:
            return False, f"Confiança alta baseada em fontes de baixa hierarquia (peso={weight:.2f})"
        return True, f"Hierarquia de fontes respeitada (peso={weight:.2f})"

class PrincipioP4(Principio):
    def __init__(self):
        super().__init__(
            id="P4",
            enunciado="Contradições internas invalidam a cadeia de raciocínio",
            descricao="Se fatos recuperados se contradizem, a conclusão deve ser rejeitada ou marcada como indeterminada",
            dominio="all",
            peso=1.0,
            aplicabilidade={}
        )

    def _avaliar(self, allegation: 'Alegacao', facts: List[Dict],
                 confianca_rlcr: float) -> Tuple[bool, str]:
        contradictions = self._detect_contradictions(facts)
        if contradictions:
            return False, f"Contradições detectadas: {contradictions}"
        return True, "Nenhuma contradição interna detectada"

    def _detect_contradictions(self, facts: List[Dict]) -> List[str]:
        contradictions = []
        claims = [(f.get('claim', ''), f.get('id', '')) for f in facts if 'claim' in f]
        for i, (claim1, id1) in enumerate(claims):
            for claim2, id2 in claims[i+1:]:
                if self._are_contradictory(claim1, claim2):
                    contradictions.append(f"{id1} ↔ {id2}")
        return contradictions

    def _are_contradictory(self, claim1: str, claim2: str) -> bool:
        contradict_pairs = [
            ("causes", "prevents"), ("increases", "decreases"),
            ("is", "is not"), ("always", "never"), ("approved", "rejected")
        ]
        c1, c2 = claim1.lower(), claim2.lower()
        return any(p1 in c1 and p2 in c2 or p2 in c1 and p1 in c2
                  for p1, p2 in contradict_pairs)

class PrincipioP5(Principio):
    def __init__(self):
        super().__init__(
            id="P5",
            enunciado="Afirmações extraordinárias exigem evidências extraordinárias",
            descricao="Quanto mais extraordinária a alegação, maior o limiar de evidência necessário",
            dominio="all",
            peso=0.95,
            aplicabilidade={}
        )

    def _avaliar(self, allegation: 'Alegacao', facts: List[Dict],
                 confianca_rlcr: float) -> Tuple[bool, str]:
        extraordinariness = self._score_exordinariness(allegation)
        required_strength = 0.5 + 0.4 * extraordinariness
        actual_strength = np.mean([f.get('evidence_strength', 0.5) for f in facts]) if facts else 0
        if actual_strength < required_strength and confianca_rlcr > 0.6:
            return False, f"Alegação extraordinária (score={extraordinariness:.2f}) exige evidência ≥{required_strength:.2f}, obtido {actual_strength:.2f}"
        return True, f"Evidência adequada para nível de extraordinariedade ({extraordinariness:.2f})"

    def _score_exordinariness(self, allegation: 'Alegacao') -> float:
        extraordinary_keywords = [
            "cure", "miracle", "breakthrough", "revolutionary", "first-ever",
            "proven", "definitive", "undisputed", "conspiracy", "cover-up"
        ]
        text = getattr(allegation, "text", "").lower()
        count = sum(1 for kw in extraordinary_keywords if kw in text)
        return min(1.0, count / 3.0)

class ConstituicaoCatedral:
    PRINCIPIOS_BASE = [
        PrincipioP1(), PrincipioP2(), PrincipioP3(),
        PrincipioP4(), PrincipioP5()
    ]

    def __init__(self, dominio: str = "all"):
        self.dominio = dominio
        self.principios = self._adaptar_para_dominio(dominio)
        self.pesos = {p.id: p.peso for p in self.principios}

    def julgar(self, allegation: 'Alegacao', facts: List[Dict],
               confianca_rlcr: float) -> Tuple[Veredito, str]:
        resultados = []
        violacoes = []

        for principio in self.principios:
            satisfeito, justificativa = principio.aplicar(
                allegation, facts, confianca_rlcr
            )
            resultados.append({
                'principio': principio.id,
                'satisfeito': satisfeito,
                'justificativa': justificativa
            })
            if not satisfeito and "N/A" not in justificativa:
                violacoes.append(justificativa)

        if violacoes:
            critical_violations = [v for v in violacoes
                                 if any(p.id in v for p in self.principios if p.peso >= 0.95)]
            if critical_violations:
                return Veredito.REFUTADO, f"Violações críticas: {'; '.join(critical_violations)}"
            return Veredito.INDETERMINADO, f"Incerteza constitucional: {'; '.join(violacoes)}"

        if confianca_rlcr >= 0.7:
            return Veredito.VERIFICADO, "Todos os princípios satisfeitos + confiança alta"
        elif confianca_rlcr <= 0.3:
            return Veredito.REFUTADO, "Princípios satisfeitos mas confiança muito baixa"
        else:
            return Veredito.INDETERMINADO, "Princípios satisfeitos mas confiança intermediária"

    def _adaptar_para_dominio(self, dominio: str) -> List[Principio]:
        adaptacoes = {
            "medicina": {"P1": 1.0, "P2": 1.0, "P3": 0.9, "P4": 1.0, "P5": 0.95},
            "direito": {"P1": 0.9, "P2": 0.8, "P3": 1.0, "P4": 1.0, "P5": 0.8},
            "ciencia": {"P1": 1.0, "P2": 0.9, "P3": 1.0, "P4": 1.0, "P5": 1.0},
            "programacao": {"P1": 0.8, "P2": 0.7, "P3": 0.7, "P4": 0.9, "P5": 0.6},
        }
        pesos_dom = adaptacoes.get(dominio, {})

        principios_adaptados = []
        for p in self.PRINCIPIOS_BASE:
            if pesos_dom.get(p.id) is not None:
                p.peso = pesos_dom[p.id]
            principios_adaptados.append(p)
        return principios_adaptados

    def exportar_para_json(self) -> Dict:
        return {
            "dominio": self.dominio,
            "principios": [
                {
                    "id": p.id,
                    "enunciado": p.enunciado,
                    "descricao": p.descricao,
                    "peso": p.peso,
                    "aplicabilidade": p.aplicabilidade
                }
                for p in self.principios
            ],
            "hash": hashlib.sha3_256(
                json.dumps([p.__dict__ for p in self.principios if not callable(p)], sort_keys=True, default=str).encode()
            ).hexdigest()
        }
