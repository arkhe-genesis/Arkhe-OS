# ontological/recursive_learning.py — Mecanismo de aprendizado recursivo do OntologicalForge

import hashlib
import json
import time
import math
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter

from ontological.forge import (
    OntologicalForge, DomainOntologySpec, GeneratedOntology,
    OntologyConsistency, GeneratedSubstrate
)

# Mock ou Import do Códice
try:
    from cathedral_codex import CrystalCodex
except ImportError:
    class CrystalCodex:
        def store_artifact(self, **kwargs): pass

class FeedbackType(Enum):
    """Tipos de feedback para aprendizado."""
    VALIDATION = "validation"      # Feedback automático de validação
    HUMAN = "human"               # Feedback de revisores humanos
    PRODUCTION = "production"     # Feedback de monitoramento em produção

class LearningStrategy(Enum):
    """Estratégias de aprendizado suportadas."""
    ASSOCIATION_RULES = "association_rules"
    SEMANTIC_CLUSTERING = "semantic_clustering"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"

@dataclass
class FeedbackEntry:
    """Entrada de feedback para aprendizado."""
    feedback_id: str
    generation_id: str
    feedback_type: FeedbackType
    sentiment: float  # -1.0 a +1.0
    details: Dict[str, Any]
    source: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class GenerationRecord:
    """Registro completo de uma geração para histórico."""
    record_id: str
    spec: Dict
    ontology: Dict
    intention: str
    substrate: Optional[Dict]
    metrics: Dict[str, Any]
    feedback_entries: List[str]
    created_at: float = field(default_factory=time.time)
    updated_at: Optional[float] = None

@dataclass
class LearnedPattern:
    """Padrão aprendido a partir do histórico."""
    pattern_id: str
    description: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    confidence: float
    support_count: int
    validated: bool
    created_at: float = field(default_factory=time.time)

@dataclass
class OptimizedParameters:
    """Parâmetros otimizados para geração."""
    domain_name: str
    parameters: Dict[str, Any]
    optimization_score: float
    validation_count: int
    last_updated: float = field(default_factory=time.time)

class RecursiveLearningEngine:
    """
    Mecanismo de aprendizado recursivo do OntologicalForge.
    """

    LEARNING_THRESHOLDS = {
        "min_patterns_for_application": 5,
        "min_confidence_for_pattern": 0.7,
        "min_feedback_entries_for_learning": 5, # Reduzido para demo
        "optimization_evaluation_window": 20,
    }

    OPTIMIZABLE_PARAMETERS = {
        "consistency_threshold": {"min": 0.90, "max": 0.99, "default": 0.95, "type": float},
        "translation_strategy": {"values": ["STRICT", "FLEXIBLE", "HYBRID"], "default": "HYBRID", "type": str},
        "privacy_epsilon_default": {"min": 0.1, "max": 2.0, "default": 1.0, "type": float},
        "max_inheritance_depth": {"min": 3, "max": 7, "default": 5, "type": int},
        "reasoner_timeout_seconds": {"min": 10, "max": 60, "default": 30, "type": int},
    }

    def __init__(self, forge: OntologicalForge, codex: Optional[CrystalCodex] = None):
        self.forge = forge
        self.codex = codex or CrystalCodex()
        self._generation_history: Dict[str, GenerationRecord] = {}
        self._feedback_store: Dict[str, FeedbackEntry] = {}
        self._learned_patterns: Dict[str, LearnedPattern] = {}
        self._optimized_parameters: Dict[str, OptimizedParameters] = {}
        self._meta_learning_enabled = True

    def record_generation(self, spec: DomainOntologySpec, ontology: GeneratedOntology,
                          intention: str, substrate: Optional[GeneratedSubstrate],
                          metrics: Dict[str, Any]) -> str:
        record_id = f"gen_{spec.domain_name}_{hashlib.sha256(f'{intention}{time.time()}'.encode()).hexdigest()[:12]}"

        record = GenerationRecord(
            record_id=record_id,
            spec=asdict(spec),
            ontology={
                "ontology_id": ontology.ontology_id,
                "consistency_status": ontology.consistency_status.value,
                "classes_count": ontology.classes_count,
            },
            intention=intention,
            substrate=asdict(substrate) if substrate else None,
            metrics=metrics,
            feedback_entries=[]
        )

        self._generation_history[record_id] = record
        logging.info(f"[RecursiveLearning] Geração registrada: {record_id}")
        return record_id

    def add_feedback(self, generation_id: str, feedback_type: FeedbackType,
                     sentiment: float, details: Dict[str, Any], source: str) -> str:
        if generation_id not in self._generation_history:
            # Tenta encontrar por ontology_id se o generation_id falhar (comum na demo)
            found = False
            for gid, rec in self._generation_history.items():
                if rec.ontology["ontology_id"] == generation_id:
                    generation_id = gid
                    found = True
                    break
            if not found:
                raise ValueError(f"Geração {generation_id} não encontrada")

        fb_id = f"fb_{generation_id}_{hashlib.sha256(f'{sentiment}{time.time()}'.encode()).hexdigest()[:8]}"
        feedback = FeedbackEntry(fb_id, generation_id, feedback_type, sentiment, details, source)

        self._feedback_store[fb_id] = feedback
        self._generation_history[generation_id].feedback_entries.append(fb_id)
        return fb_id

    def extract_patterns(self, min_support: int = 3) -> List[LearnedPattern]:
        patterns = []
        by_domain = defaultdict(list)
        for record in self._generation_history.values():
            by_domain[record.spec["domain_name"]].append(record)

        for domain, records in by_domain.items():
            if len(records) < min_support: continue

            # Lógica simplificada de extração
            high_privacy_specs = [r for r in records if r.spec.get("constraints", {}).get("high_privacy")]
            high_privacy_fails = [r for r in high_privacy_specs if r.ontology["consistency_status"] != "valid"]

            # Se houver falhas em domínios de alta privacidade, gera um padrão
            if high_privacy_specs and (len(high_privacy_fails) / len(high_privacy_specs) >= 0.2):
                p = LearnedPattern(
                    pattern_id=f"p_hp_{domain}",
                    description="Risco de inconsistência em domínios de alta privacidade",
                    condition={"constraints.high_privacy": True},
                    action={"consistency_threshold": 0.98},
                    confidence=0.85,
                    support_count=len(records),
                    validated=True
                )
                patterns.append(p)
                self._learned_patterns[p.pattern_id] = p
        return patterns

    def optimize_parameters(self, domain_name: str) -> OptimizedParameters:
        records = [r for r in self._generation_history.values() if r.spec["domain_name"] == domain_name]

        # Simula otimização bayesiana sem numpy
        best_params = {k: v["default"] for k, v in self.OPTIMIZABLE_PARAMETERS.items()}
        if len(records) >= self.LEARNING_THRESHOLDS["min_feedback_entries_for_learning"]:
            best_params["consistency_threshold"] = 0.97

        optimized = OptimizedParameters(
            domain_name=domain_name,
            parameters=best_params,
            optimization_score=0.92,
            validation_count=len(records)
        )
        self._optimized_parameters[domain_name] = optimized
        return optimized

    def apply_learned_patterns(self, spec: DomainOntologySpec) -> DomainOntologySpec:
        for pattern in self._learned_patterns.values():
            if pattern.validated and self._evaluate_condition(pattern.condition, spec):
                if "consistency_threshold" in pattern.action:
                    spec.constraints["consistency_threshold"] = pattern.action["consistency_threshold"]
        return spec

    def _evaluate_condition(self, condition: Dict, spec: DomainOntologySpec) -> bool:
        # Avaliador de caminho simplificado
        for k, v in condition.items():
            if k == "constraints.high_privacy":
                if spec.constraints.get("high_privacy") != v: return False
        return True

    async def enable_meta_learning(self) -> bool:
        """O Forge gera uma ontologia para aprimorar seu próprio aprendizado."""
        spec = DomainOntologySpec(
            domain_name="RecursiveLearning",
            description="Ontologia de auto-aprimoramento",
            base_uri="http://cathedral.ark/ontology",
            entities=["LearningStrategy", "MetaLearner"],
            constraints={"high_privacy": True}
        )

        result = await self.forge.forge_from_ontology(spec)
        logging.info("[RecursiveLearning] Meta-aprendizado aplicado.")
        return True

    def generate_learning_report(self, domain_name: Optional[str] = None) -> Dict:
        return {
            "total_generations": len(self._generation_history),
            "patterns_count": len(self._learned_patterns),
            "optimized_domains": list(self._optimized_parameters.keys())
        }
