# ontological/recursive_learning.py — Motor de aprendizado para o OntologicalForge

import hashlib
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class LearnedPattern:
    """Representa um padrão extraído do histórico de gerações."""
    pattern_id: str
    description: str
    logic_rule: Dict[str, Any]
    support_count: int
    confidence_score: float
    validated: bool = False
    created_at: float = field(default_factory=time.time)

class RecursiveLearningEngine:
    """
    Motor que analisa o histórico de gerações para extrair padrões e regras
    que aprimoram a precisão semântica das futuras ontologias.
    """

    def __init__(self):
        self._learned_patterns: Dict[str, LearnedPattern] = {}
        self._execution_history: List[Dict] = []

    def extract_patterns(self, history: List[Dict]) -> List[LearnedPattern]:
        """
        Analisa o histórico e extrai padrões (ex: 'Domínios de Saúde exigem mais entidades').
        """
        if not history:
            return []

        patterns = []

        # Exemplo de padrão extraído: Correlação entre domínio e sucesso
        # Em produção, usaria algoritmos de mineração de regras de associação (ex: Apriori)
        domain_counts = {}
        for entry in history:
            domain = entry.get("domain")
            status = entry.get("status")
            if domain not in domain_counts:
                domain_counts[domain] = {"total": 0, "valid": 0}
            domain_counts[domain]["total"] += 1
            if status == "valid":
                domain_counts[domain]["valid"] += 1

        for domain, stats in domain_counts.items():
            if stats["total"] >= 5:
                confidence = stats["valid"] / stats["total"]
                if confidence > 0.8:
                    pattern = LearnedPattern(
                        pattern_id=f"pattern_{domain.lower()}_{int(time.time())}",
                        description=f"Domínio {domain} possui alta taxa de validade ({confidence*100}%).",
                        logic_rule={"domain": domain, "action": "enforce_rigor", "confidence": confidence},
                        support_count=stats["total"],
                        confidence_score=confidence,
                        validated=True
                    )
                    patterns.append(pattern)
                    self._learned_patterns[pattern.pattern_id] = pattern

        return patterns

    def get_optimization_suggestions(self) -> Dict[str, Any]:
        """Retorna sugestões baseadas nos padrões validados."""
        suggestions = {}
        for pattern in self._learned_patterns.values():
            if pattern.validated and pattern.confidence_score > 0.9:
                # Sugere aumentar thresholds para domínios de alta confiança
                suggestions["rigor_increase"] = True
                suggestions["target_domain"] = pattern.logic_rule.get("domain")
        return suggestions
