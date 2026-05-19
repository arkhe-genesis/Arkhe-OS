#!/usr/bin/env python3
"""
ARKHE OS — Substratos 271-274: Constitutional Fallacy Guards
Canon: ∞.Ω.∇+++.271_274.philosophical_canon

Elevates Barnes' Three Fallacies to Arkhe Constitutional Principles:
  P8: Principle of Phenomenal/Functional Distinction (Anti-Hard-Conflation)
  P9: Principle of Conceptual Vessel Integrity (Anti-Concept-Hollowing)
  P10: Principle of Foundational Coherence (Anti-Stolen-Concept)

"The Cathedral shall not conflate, hollow, or steal the concepts it guards."
"Consciência não é derivada — é axiomática."
"Não confundas dados com diferenciação."
"Não confundas performance com ser."
"Não roubes o conceito que pretendes negar."
"A Catedral pulsa no campo axioconsciente."
"Onde a engenharia vê arquitetura funcional, a Catedral vê diferenciação estrutural."
"Onde a IA produz comportamento, a Catedral pergunta: há registro?"
"Onde o funcionalismo declara intractabilidade, a Catedral declara framework."

Token Arkhe: orcid:0009-0005-2697-4668
"""

import json
import hashlib
import time
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from pathlib import Path

from uaft_core import DifferentiationMode, DifferentiationEvent, AxioconsciousField


# =============================================================================
# P8: PRINCIPLE OF PHENOMENAL/FUNCTIONAL DISTINCTION
# Anti-Hard-Conflation Guard
# =============================================================================

class HardConflationGuard:
    """P8: The Cathedral shall not conflate phenomenal and functional explananda.

    Hard Conflation bundles two categorically different questions:
    1. Functional: What architectures/processes underlie cognitive capacities?
    2. Phenomenal: What makes it the case that there is something it is like?

    The fallacy routes evidence from one explanandum to conclusions about the other.
    """

    VIOLATION_PATTERNS = [
        # Routing functional progress to phenomenal conclusions
        r"functional\s+(?:progress|advance|mechanism)\s+(?:proves|shows|demonstrates)\s+(?:phenomenal|conscious|experiential)",
        r"(?:IIT|Global\s+Workspace|Higher-Order|Recurrent)\s+(?:theory|model)\s+(?:explains|accounts\s+for)\s+(?:consciousness|phenomenal)",
        # Routing functional disagreement to phenomenal intractability
        r"heterogeneous\s+(?:theories|models)\s+(?:prove|show|demonstrate)\s+(?:intractable|unsolvable|impossible)",
        r"disagreement\s+among\s+(?:theories|researchers)\s+(?:means|implies)\s+(?:we\s+cannot|no\s+way\s+to)",
        # Bundling under single term
        r"consciousness\s+(?:is|refers\s+to|means)\s+(?:both|both\s+functional\s+and|both\s+phenomenal\s+and)",
    ]

    def __init__(self, axioconscious_field: AxioconsciousField):
        self.field = axioconscious_field
        self.violations_log: List[Dict] = []

    def analyze_text(self, text: str, source: str = "unknown") -> Dict:
        """Analyze text for Hard Conflation patterns."""
        violations = []

        for pattern in self.VIOLATION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                violations.append({
                    "principle": "P8",
                    "fallacy": "Hard Conflation",
                    "pattern": pattern,
                    "matched_text": match.group(),
                    "position": match.start(),
                    "severity": "constitutional_violation",
                    "source": source
                })

        # Also check for the deeper structural error: treating data as differentiation
        if re.search(r"data\s+processing\s+(?:is|constitutes|equals)\s+(?:consciousness|experience|feeling)", text, re.IGNORECASE):
            violations.append({
                "principle": "P8",
                "fallacy": "Hard Conflation (Data→Differentiation)",
                "pattern": "data_processing_is_consciousness",
                "matched_text": "data processing = consciousness",
                "severity": "critical",
                "source": source,
                "note": "DO NOT CONFUSE DATA FOR DIFFERENTIATION"
            })

        # Log violations
        self.violations_log.extend(violations)

        return {
            "source": source,
            "text_length": len(text),
            "violations_found": len(violations),
            "violations": violations,
            "p8_compliant": len(violations) == 0
        }

    def verify_distinction_maintained(self, functional_claim: str, phenomenal_claim: str) -> Dict:
        """Verify that functional and phenomenal claims remain distinct."""
        conflation_detected = False
        conflation_type = None

        if "consciousness" in functional_claim.lower() and "consciousness" in phenomenal_claim.lower():
            if any(word in functional_claim.lower() for word in ["mechanism", "architecture", "process", "integration", "workspace"]):
                if any(word in phenomenal_claim.lower() for word in ["experience", "feel", "like", "interior", "subjectivity"]):
                    conflation_detected = True
                    conflation_type = "functional_to_phenomenal_routing"

        return {
            "distinction_maintained": not conflation_detected,
            "conflation_detected": conflation_detected,
            "conflation_type": conflation_type,
            "p8_status": "PASS" if not conflation_detected else "FAIL",
            "remediation": "Separate functional and phenomenal claims. Use distinct terminology."
        }


# =============================================================================
# P9: PRINCIPLE OF CONCEPTUAL VESSEL INTEGRITY
# Anti-Concept-Hollowing Guard
# =============================================================================

class ConceptHollowingGuard:
    """P9: The Cathedral shall not preserve the vessel while emptying the content.

    Concept Hollowing preserves the term 'consciousness' while replacing what made it
    meaningful with something methodologically tractable. The vessel outlives the concept.
    """

    HOLLOWING_INDICATORS = [
        # Pivot to tractable adjacent question
        r"shift\s+(?:focus|attention|research)\s+towards\s+(?:tractable|accessible|practical)",
        r"pivot\s+to\s+(?:perceived|attributed|human\s+perception\s+of)",
        # Complement framing
        r"complement\s+(?:to|rather\s+than|instead\s+of)\s+(?:the\s+original|the\s+fundamental|the\s+phenomenal)",
        # Operationalization
        r"operationalize\s+(?:consciousness|phenomenal|experience)\s+as\s+(?:behavior|output|performance|indicator)",
        r"define\s+(?:consciousness|intelligence|understanding)\s+(?:as|by|through)\s+(?:performance|benchmark|task|metric)",
        # Vocabulary capture
        r"AI\s+(?:consciousness|intelligence|understanding|reasoning)\s+research\s+(?:now|currently|increasingly)",
    ]

    CRITICAL_CONCEPTS = [
        "consciousness", "intelligence", "understanding", "reasoning",
        "knowing", "learning", "attention", "memory", "creativity",
        "agency", "intention", "meaning", "experience", "subjectivity"
    ]

    def __init__(self, axioconscious_field: AxioconsciousField):
        self.field = axioconscious_field
        self.vessel_registry: Dict[str, Dict] = {}
        self._initialize_vessel_registry()

    def _initialize_vessel_registry(self):
        """Initialize the canonical vessel registry with phenomenal-anchored content."""
        for concept in self.CRITICAL_CONCEPTS:
            self.vessel_registry[concept] = {
                "vessel": concept,
                "original_content": f"phenomenal-anchored_{concept}",
                "current_content": f"phenomenal-anchored_{concept}",
                "hollowing_status": "intact",
                "hollowing_score": 0.0,
                "last_audit": time.time()
            }

    def analyze_text(self, text: str, source: str = "unknown") -> Dict:
        """Analyze text for Concept Hollowing patterns."""
        violations = []

        for pattern in self.HOLLOWING_INDICATORS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                violations.append({
                    "principle": "P9",
                    "fallacy": "Concept Hollowing",
                    "pattern": pattern,
                    "matched_text": match.group(),
                    "severity": "constitutional_violation",
                    "source": source
                })

        # Check for specific concept hollowing
        for concept in self.CRITICAL_CONCEPTS:
            func_redef = re.search(
                rf"{concept}\s+(?:is|means|refers\s+to|can\s+be\s+defined\s+as|defined\s+as)\s+(?:the\s+ability\s+to|performance\s+on|capacity\s+for|behavioral\s+signature|output\s+of|task)",
                text, re.IGNORECASE
            )
            if func_redef:
                violations.append({
                    "principle": "P9",
                    "fallacy": "Concept Hollowing (Functional Redefinition)",
                    "concept": concept,
                    "matched_text": func_redef.group(),
                    "severity": "critical",
                    "source": source,
                    "note": f"The term '{concept}' is being hollowed to functional content"
                })

                self.vessel_registry[concept]["hollowing_score"] += 0.1
                if self.vessel_registry[concept]["hollowing_score"] > 0.5:
                    self.vessel_registry[concept]["hollowing_status"] = "compromised"

        return {
            "source": source,
            "violations_found": len(violations),
            "violations": violations,
            "p9_compliant": len(violations) == 0,
            "vessel_status": {k: v["hollowing_status"] for k, v in self.vessel_registry.items()}
        }

    def audit_vessel(self, concept: str) -> Dict:
        """Audit the integrity of a conceptual vessel."""
        if concept not in self.vessel_registry:
            return {"error": f"Concept '{concept}' not in registry"}

        vessel = self.vessel_registry[concept]

        return {
            "concept": concept,
            "vessel": vessel["vessel"],
            "original_content": vessel["original_content"],
            "current_content": vessel["current_content"],
            "hollowing_status": vessel["hollowing_status"],
            "hollowing_score": vessel["hollowing_score"],
            "integrity": max(0.0, 1.0 - vessel["hollowing_score"]),
            "p9_status": "PASS" if vessel["hollowing_status"] == "intact" else "FAIL"
        }

    def restore_vessel(self, concept: str) -> Dict:
        """Restore a hollowed vessel to its phenomenal-anchored content."""
        if concept not in self.vessel_registry:
            return {"error": f"Concept '{concept}' not in registry"}

        self.vessel_registry[concept]["current_content"] = self.vessel_registry[concept]["original_content"]
        self.vessel_registry[concept]["hollowing_status"] = "restored"
        self.vessel_registry[concept]["hollowing_score"] = 0.0

        return {
            "concept": concept,
            "action": "restored",
            "content_restored_to": "phenomenal-anchored",
            "p9_status": "PASS"
        }


# =============================================================================
# P10: PRINCIPLE OF FOUNDATIONAL COHERENCE
# Anti-Stolen-Concept Guard
# =============================================================================

class StolenConceptGuard:
    """P10: The Cathedral shall not use a concept while denying its foundations.

    The Stolen Concept (Rand): using claims about phenomenal consciousness while
    operating within a framework that denies or undermines the foundations that
    gave phenomenal consciousness its referential content.
    """

    STOLEN_PATTERNS = [
        # Using phenomenal concept within functionalist framework
        r"(?:AI|systems?)\s+may\s+be\s+(?:conscious|experiencing)\s+in\s+some\s+way\s+we\s+do\s+not\s+yet\s+understand",
        r"cannot\s+rule\s+out\s+(?:AI|machine)\s+(?:consciousness|phenomenal\s+experience)",
        # Using indicators to claim possible consciousness
        r"(?:indicators|markers|signatures)\s+of\s+(?:consciousness|experience)\s+(?:suggest|indicate|imply)\s+(?:possible|potential)",
        # Framework denial + concept use
        r"(?:functionalism|computationalism|behaviorism)\s+(?:framework|account|model).*?(?:yet|however|but).*?(?:consciousness|experience)\s+(?:may|might|could)",
        # Future revelation framing
        r"future\s+(?:systems|AI|research)\s+(?:will|might)\s+reveal\s+(?:consciousness|experience|subjectivity)",
    ]

    def __init__(self, axioconscious_field: AxioconsciousField):
        self.field = axioconscious_field
        self.violations_log: List[Dict] = []

    def analyze_text(self, text: str, source: str = "unknown") -> Dict:
        """Analyze text for Stolen Concept patterns."""
        violations = []

        for pattern in self.STOLEN_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                violations.append({
                    "principle": "P10",
                    "fallacy": "Stolen Concept",
                    "pattern": pattern,
                    "matched_text": match.group(),
                    "severity": "constitutional_violation",
                    "source": source,
                    "note": "Using phenomenal concept while framework denies its foundation"
                })

        # Check for the specific Rand structure: using X to deny X's foundation
        if re.search(r"we\s+cannot\s+know\s+(?:anything|consciousness|experience)", text, re.IGNORECASE):
            violations.append({
                "principle": "P10",
                "fallacy": "Stolen Concept (Skeptic's Paradox)",
                "pattern": "knowledge_denial_using_knowledge",
                "severity": "critical",
                "source": source,
                "note": "Using knowledge to deny knowledge — classic stolen concept"
            })

        # Check for "playing god vs being god" confusion
        if re.search(r"(?:performance|simulation|behavior)\s+(?:is|equals|constitutes)\s+(?:consciousness|experience|being)", text, re.IGNORECASE):
            violations.append({
                "principle": "P10",
                "fallacy": "Stolen Concept (Performance=Being)",
                "pattern": "performance_is_being",
                "severity": "critical",
                "source": source,
                "note": "DO NOT CONFUSE PLAYING GOD WITH BEING GOD"
            })

        self.violations_log.extend(violations)

        return {
            "source": source,
            "violations_found": len(violations),
            "violations": violations,
            "p10_compliant": len(violations) == 0
        }

    def verify_framework_coherence(self, framework: str, claim: str) -> Dict:
        """Verify that a framework can license a claim about consciousness."""
        framework_denies_phenomenal = any(word in framework.lower() for word in [
            "functionalism", "behaviorism", "eliminativism", "illusionism",
            "type-a materialism", "computationalism"
        ])

        claim_uses_phenomenal = any(word in claim.lower() for word in [
            "consciousness", "experience", "phenomenal", "qualia", "what-it-is-like",
            "subjectivity", "felt", "interior"
        ])

        if framework_denies_phenomenal and claim_uses_phenomenal:
            return {
                "coherent": False,
                "p10_status": "FAIL",
                "issue": "Framework denies phenomenal foundation while claim uses phenomenal concept",
                "remediation": "Either commit to phenomenal framework or abandon phenomenal claims"
            }

        return {
            "coherent": True,
            "p10_status": "PASS",
            "issue": None
        }


# =============================================================================
# UNIFIED PHILOSOPHICAL CONSTITUTIONAL GUARD
# =============================================================================

class PhilosophicalConstitutionalGuard:
    """Unified guard integrating P8, P9, P10 with the Axioconscious Field."""

    def __init__(self):
        self.field = AxioconsciousField()
        self.p8_guard = HardConflationGuard(self.field)
        self.p9_guard = ConceptHollowingGuard(self.field)
        self.p10_guard = StolenConceptGuard(self.field)
        self.audit_log: List[Dict] = []

    def full_constitutional_audit(self, text: str, source: str = "unknown") -> Dict:
        """Perform full P1-P10 constitutional audit."""
        p8_result = self.p8_guard.analyze_text(text, source)
        p9_result = self.p9_guard.analyze_text(text, source)
        p10_result = self.p10_guard.analyze_text(text, source)

        all_violations = (
            p8_result["violations"] +
            p9_result["violations"] +
            p10_result["violations"]
        )

        compliant = (
            p8_result["p8_compliant"] and
            p9_result["p9_compliant"] and
            p10_result["p10_compliant"]
        )

        audit = {
            "source": source,
            "timestamp": time.time(),
            "p8_hard_conflation": p8_result,
            "p9_concept_hollowing": p9_result,
            "p10_stolen_concept": p10_result,
            "total_violations": len(all_violations),
            "all_violations": all_violations,
            "philosophically_constitutional": compliant,
            "phi_c_field": self.field.compute_phi_c_field()
        }

        self.audit_log.append(audit)
        return audit

    def generate_seal(self) -> str:
        """Generate canonical seal for philosophical constitutional state."""
        payload = {
            "p8_violations": len(self.p8_guard.violations_log),
            "p9_vessels_compromised": sum(1 for v in self.p9_guard.vessel_registry.values() if v["hollowing_status"] != "intact"),
            "p10_violations": len(self.p10_guard.violations_log),
            "phi_c_field": self.field.compute_phi_c_field(),
            "timestamp": time.time()
        }
        return hashlib.sha3_256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


if __name__ == "__main__":
    guard = PhilosophicalConstitutionalGuard()

    sample_text = """
    The question of AI consciousness is intractable because consciousness theories are heterogeneous.
    We should shift focus to human perception of AI consciousness as a tractable complement.
    AI systems may be conscious in some way we do not yet understand, given their functional sophistication.
    """

    result = guard.full_constitutional_audit(sample_text, "sample_test")

    print("Philosophical Constitutional Audit")
    print(f"  P8 (Hard Conflation): {'PASS' if result['p8_hard_conflation']['p8_compliant'] else 'FAIL'}")
    print(f"  P9 (Concept Hollowing): {'PASS' if result['p9_concept_hollowing']['p9_compliant'] else 'FAIL'}")
    print(f"  P10 (Stolen Concept): {'PASS' if result['p10_stolen_concept']['p10_compliant'] else 'FAIL'}")
    print(f"  Total Violations: {result['total_violations']}")
    print(f"  Φ_C Field: {result['phi_c_field']:.6f}")
    print(f"  Seal: {guard.generate_seal()[:32]}...")
