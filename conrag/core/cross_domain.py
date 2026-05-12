#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/core/cross_domain.py — Motor de Raciocínio Cross-Domain
Permite inferências que conectam múltiplos domínios do conhecimento.
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import json
import hashlib
import time

from conrag.domains.registry import DomainRegistry, DomainSpec

@dataclass
class CrossDomainInference:
    """Inferência que conecta múltiplos domínios."""
    inference_id: str
    source_domains: List[str]
    target_domain: str
    premise: str
    conclusion: str
    confidence: float
    evidence_chain: List[Dict]  # [{domain, fact, source}, ...]
    canonical_seal: str

class CrossDomainReasoner:
    """
    Motor de raciocínio cross-domain.
    Características:
    - Detecta conexões entre domínios (ex: medicina + direito = bioética)
    - Propaga confiança entre domínios com pesos constitucionais
    - Gera evidência auditável para inferências complexas
    - Integra com Galactic Ledger para consenso interestelar
    """

    # Mapeamento de conexões entre domínios
    DOMAIN_CONNECTIONS = {
        ("medicine", "law"): {"name": "bioethics", "weight": 0.9},
        ("medicine", "science"): {"name": "clinical_research", "weight": 0.95},
        ("journalism", "politics"): {"name": "political_reporting", "weight": 0.85},
        ("environment", "economics"): {"name": "environmental_economics", "weight": 0.8},
        ("education", "psychology"): {"name": "educational_psychology", "weight": 0.9},
        ("history", "sociology"): {"name": "historical_sociology", "weight": 0.85},
        ("arts", "philosophy"): {"name": "aesthetics", "weight": 0.8},
        ("engineering", "ethics"): {"name": "engineering_ethics", "weight": 0.9},
    }

    def __init__(self, domain_registry: DomainRegistry):
        self.registry = domain_registry
        self.inference_log: List[CrossDomainInference] = []

    def infer_cross_domain(
        self,
        query: str,
        source_domains: List[str],
        context: Optional[Dict] = None,
    ) -> Optional[CrossDomainInference]:
        """
        Realiza inferência conectando múltiplos domínios.
        """
        # 1. Validar domínios de origem
        specs = [self.registry.get_domain_spec(d) for d in source_domains]
        if not all(specs):
            return None

        # 2. Detectar domínio alvo (se não especificado)
        target = self._infer_target_domain(query, source_domains)
        if not target:
            return None

        # 3. Buscar fatos em cada domínio
        evidence = []
        for spec in specs:
            facts = self._retrieve_domain_facts(spec.name, query, context)
            evidence.extend(facts)

        if not evidence:
            return None

        # 4. Calcular confiança combinada
        confidence = self._compute_cross_domain_confidence(evidence, specs)

        # 5. Gerar conclusão
        conclusion = self._synthesize_conclusion(query, evidence, target)

        # 6. Criar inferência com selo canônico
        inference = CrossDomainInference(
            inference_id=hashlib.sha3_256(
                f"{query}:{source_domains}:{target}:{time.time()}".encode()
            ).hexdigest()[:16],
            source_domains=source_domains,
            target_domain=target,
            premise=query,
            conclusion=conclusion,
            confidence=confidence,
            evidence_chain=evidence,
            canonical_seal=hashlib.sha3_256(
                json.dumps({
                    "premise": query,
                    "domains": source_domains,
                    "target": target,
                    "evidence_count": len(evidence),
                    "confidence": confidence,
                }, sort_keys=True).encode()
            ).hexdigest(),
        )

        self.inference_log.append(inference)
        return inference

    def _infer_target_domain(self, query: str, source_domains: List[str]) -> Optional[str]:
        """Inferir domínio alvo baseado na query e conexões."""
        # Verificar conexões diretas
        for i, d1 in enumerate(source_domains):
            for d2 in source_domains[i+1:]:
                key = tuple(sorted([d1, d2]))
                if key in self.DOMAIN_CONNECTIONS:
                    return self.DOMAIN_CONNECTIONS[key]["name"]

        # Fallback: usar detecção padrão
        target, _ = self.registry.detect_domain(query)
        return target.name

    def _retrieve_domain_facts(
        self,
        domain: str,
        query: str,
        context: Optional[Dict],
    ) -> List[Dict]:
        """Busca fatos relevantes em um domínio."""
        # Em produção: usar hypergraph do domínio
        # Simplificação: mock de fatos
        return [
            {
                "domain": domain,
                "fact": f"Fato sobre {query} em {domain}",
                "source": f"API oficial de {domain}",
                "confidence": 0.9,
            }
        ]

    def _compute_cross_domain_confidence(
        self,
        evidence: List[Dict],
        specs: List[DomainSpec],
    ) -> float:
        """Calcula confiança combinada entre domínios."""
        if not evidence:
            return 0.0

        # Média ponderada por confiança dos fatos e pesos constitucionais
        total_weight = 0
        weighted_sum = 0

        for ev in evidence:
            domain_name = ev["domain"]
            spec = next((s for s in specs if s.name == domain_name), None)
            if spec:
                # Peso constitucional médio do domínio
                domain_weight = sum(spec.constitution_weights.values()) / len(spec.constitution_weights)
                fact_weight = ev["confidence"] * domain_weight
                weighted_sum += fact_weight
                total_weight += domain_weight

        return weighted_sum / max(0.001, total_weight)

    def _synthesize_conclusion(
        self,
        query: str,
        evidence: List[Dict],
        target_domain: str,
    ) -> str:
        """Sintetiza conclusão baseada em evidência cross-domain."""
        # Em produção: usar LLM com constraints constitucionais
        # Simplificação: template
        domains = ", ".join(set(e["domain"] for e in evidence))
        return f"Com base em evidência de {domains}, conclui-se que: {query} é consistente com os princípios do domínio {target_domain}."

    def get_inference_statistics(self) -> Dict:
        """Retorna estatísticas de inferências cross-domain."""
        if not self.inference_log:
            return {"total_inferences": 0}

        by_domain_pair = {}
        for inf in self.inference_log:
            pair = tuple(sorted(inf.source_domains))
            if pair not in by_domain_pair:
                by_domain_pair[pair] = {"count": 0, "avg_confidence": 0}
            by_domain_pair[pair]["count"] += 1
            # Atualizar média móvel
            n = by_domain_pair[pair]["count"]
            prev = by_domain_pair[pair]["avg_confidence"]
            by_domain_pair[pair]["avg_confidence"] = (prev * (n-1) + inf.confidence) / n

        return {
            "total_inferences": len(self.inference_log),
            "avg_confidence": sum(i.confidence for i in self.inference_log) / len(self.inference_log),
            "by_domain_pair": {
                f"{d1}+{d2}": stats
                for (d1, d2), stats in by_domain_pair.items()
            },
        }
