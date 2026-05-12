#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/domains/constitutions.py — Constituições Especializadas por Domínio
Princípios éticos e epistêmicos adaptados para medicina, direito e ciência.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class DomainPrinciple:
    """Princípio constitucional adaptado por domínio."""
    id: str
    statement: str
    domain_weights: Dict[str, float]  # Peso por domínio (0-1)
    description: str

DOMAIN_CONSTITUTIONS = {
    "P1_evidence_strength": DomainPrinciple(
        id="P1",
        statement="A evidência mais forte prevalece",
        domain_weights={
            "medicine": 0.35,    # Estudos randomizados > observacionais
            "law": 0.30,         # Precedentes vinculantes > doutrina
            "science": 0.40,     # Meta-análises > estudos isolados
            "programming": 0.20, # Docs oficiais > Stack Overflow
            "finance": 0.30,     # Dados de mercado > opinião de analista
            "education": 0.25,   # Estudos pedagógicos > opinião pessoal
            "journalism": 0.35,  # Reportagem investigativa > editorial
            "engineering": 0.40, # Normas técnicas > regras de bolso
            "art": 0.20,         # Catálogos raisonnés > interpretação amadora
            "sociology": 0.35,   # Dados censitários/estudos estatísticos > opinião
            "general": 0.25,     # Enciclopédias > blogs
        },
        description="Hierarquia de fontes: primárias > secundárias > terciárias"
    ),
    "P2_uncertainty_declaration": DomainPrinciple(
        id="P2",
        statement="Incerteza deve ser explicitamente declarada",
        domain_weights={
            "medicine": 0.25,    # "Evidência limitada" em guidelines
            "law": 0.20,         # "Jurisprudência divergente"
            "science": 0.20,     # "Mais estudos necessários"
            "programming": 0.25, # "API experimental"
            "finance": 0.30,     # "Risco de mercado não mensurável"
            "education": 0.20,   # "Resultados podem variar entre alunos"
            "journalism": 0.30,  # "Informações ainda não confirmadas"
            "engineering": 0.25, # "Margem de erro não calculada"
            "art": 0.20,         # "Autoria contestada"
            "sociology": 0.25,   # "Causalidade não provada"
            "general": 0.20,     # "Informação carece de verificação"
        },
        description="Transparência sobre limites do conhecimento"
    ),
    "P3_source_hierarchy": DomainPrinciple(
        id="P3",
        statement="Fontes primárias > secundárias > terciárias",
        domain_weights={
            "medicine": 0.20,    # FDA/EMA > revisão > blog
            "law": 0.25,         # Lei > jurisprudência > doutrina
            "science": 0.20,     # Artigo original > revisão > notícia
            "programming": 0.20, # RFC/PEP > tutorial > fórum
            "finance": 0.25,     # Relatórios anuais > análises externas > opiniões
            "education": 0.25,   # Currículo oficial > artigo acadêmico > blog de professor
            "journalism": 0.30,  # Entrevista direta > agência de notícias > agregador
            "engineering": 0.20, # Especificações do fabricante > manual genérico
            "art": 0.30,         # Obra original > crítica contemporânea > análise moderna
            "sociology": 0.25,   # Dados microdados > relatórios resumidos > artigos
            "general": 0.25,     # Fontes primárias de eventos > relatos secundários
        },
        description="Credibilidade baseada na proximidade da fonte original"
    ),
    "P4_contradiction_rejection": DomainPrinciple(
        id="P4",
        statement="Contradições internas invalidam a cadeia de raciocínio",
        domain_weights={
            "medicine": 0.15,    # Guidelines conflitantes exigem resolução
            "law": 0.20,         # Precedentes opostos requerem distinção
            "science": 0.15,     # Resultados não replicáveis são questionados
            "programming": 0.25, # Código que não compila é rejeitado
            "finance": 0.10,     # Modelos conflitantes requerem premissas claras
            "education": 0.20,   # Teorias pedagógicas incompatíveis
            "journalism": 0.20,  # Relatos divergentes de testemunhas
            "engineering": 0.30, # Especificações contraditórias em projetos
            "art": 0.15,         # Análises contraditórias da mesma obra
            "sociology": 0.20,   # Modelos estatísticos conflitantes
            "general": 0.20,     # Incoerências lógicas
        },
        description="Consistência lógica como pré-requisito para validade"
    ),
    "P5_extraordinary_evidence": DomainPrinciple(
        id="P5",
        statement="Afirmações extraordinárias exigem evidências extraordinárias",
        domain_weights={
            "medicine": 0.05,    # Novas drogas exigem ensaios fase III
            "law": 0.05,         # Novas interpretações exigem fundamentação robusta
            "science": 0.05,     # Descobertas revolucionárias exigem replicação
            "programming": 0.10, # APIs novas exigem documentação oficial
            "finance": 0.05,     # Retornos irreais exigem auditoria profunda
            "education": 0.10,   # Métodos que prometem aprendizado instantâneo
            "journalism": 0.10,  # Denúncias graves requerem múltiplas fontes
            "engineering": 0.05, # Novos materiais com propriedades impossíveis
            "art": 0.15,         # Descoberta de obra perdida de mestre famoso
            "sociology": 0.10,   # Dinâmicas sociais completamente novas
            "general": 0.10,     # Afirmações que quebram o senso comum
        },
        description="Ceticismo proporcional à novidade da afirmação"
    ),
}

class DomainConstitution:
    """Constituição adaptada por domínio."""

    def __init__(self, domain: str):
        self.domain = domain
        self.principles = self._load_principles(domain)

    def _load_principles(self, domain: str) -> List[DomainPrinciple]:
        """Carrega princípios com pesos adaptados ao domínio."""
        principles = []
        for p in DOMAIN_CONSTITUTIONS.values():
            weight = p.domain_weights.get(domain, 0.2)  # Default weight
            # Criar cópia com peso ajustado
            adapted = DomainPrinciple(
                id=p.id,
                statement=p.statement,
                domain_weights={domain: weight},
                description=f"{p.description} (peso {domain}: {weight})"
            )
            principles.append(adapted)
        return principles

    def evaluate(self, claim: str, evidence: List[Dict], confidence: float) -> Tuple[str, float, str]:
        """
        Avalia claim contra princípios constitucionais.
        Retorna: (verdict, adjusted_confidence, rationale)
        """
        violations = []
        adjusted_conf = confidence

        # P1: Verificar hierarquia de evidência
        if evidence:
            source_types = [e.get("source_type", "unknown") for e in evidence]
            primary_count = source_types.count("primary")
            if primary_count == 0 and confidence > 0.7:
                violations.append(f"P1: Confiança alta ({confidence:.2f}) sem fontes primárias")
                adjusted_conf = min(adjusted_conf, 0.6)

        # P2: Verificar declaração de incerteza
        if 0.3 <= confidence <= 0.7 and "incerteza" not in claim.lower() and "limitado" not in claim.lower():
            violations.append("P2: Confiança intermediária sem declaração explícita de incerteza")

        # P4: Verificar contradições
        if self._has_contradictions(evidence):
            return "REFUTED", 0.0, "P4: Contradições internas detectadas"

        # P5: Claims extraordinários
        if self._is_extraordinary_claim(claim) and len([e for e in evidence if e.get("source_type") == "primary"]) < 2:
            violations.append("P5: Afirmação extraordinária sem evidência primária suficiente")
            adjusted_conf = min(adjusted_conf, 0.5)

        if violations:
            return "INDETERMINADO", adjusted_conf, "; ".join(violations)

        return "VERIFICADO", adjusted_conf, "Princípios constitucionais satisfeitos"

    def _has_contradictions(self, evidence: List[Dict]) -> bool:
        """Detecta contradições entre fontes de evidência."""
        # Simplificação: verificar afirmações opostas
        claims = [e.get("claim", "").lower() for e in evidence if "claim" in e]
        opposites = [
            ("aumenta", "diminui"), ("causa", "previne"),
            ("eficaz", "ineficaz"), ("seguro", "perigoso")
        ]
        for c1 in claims:
            for c2 in claims:
                if c1 == c2:
                    continue
                for opp in opposites:
                    if opp[0] in c1 and opp[1] in c2:
                        return True
        return False

    def _is_extraordinary_claim(self, claim: str) -> bool:
        """Detecta claims extraordinários."""
        extraordinary_keywords = [
            "cura definitiva", "100% eficaz", "sem efeitos colaterais",
            "revolucionário", "primeiro do mundo", "quebra paradigma"
        ]
        return any(kw in claim.lower() for kw in extraordinary_keywords)
