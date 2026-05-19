#!/usr/bin/env python3
"""
ARKHE OS — Vocabulary Capture Detector (Substrate 271-274)
Detects progressive hollowing of phenomenal concepts by functionalist capture.

"Não confundas dados com diferenciação."
"Não confundas performance com ser."
"Não roubes o conceito que pretendes negar."

Token Arkhe: orcid:0009-0005-2697-4668
"""

import json
import hashlib
import time
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from pathlib import Path


class CognitiveConcept(Enum):
    """The 17 canonical cognitive concepts guarded by the Cathedral."""
    CONSCIOUSNESS = "consciousness"
    INTELLIGENCE = "intelligence"
    UNDERSTANDING = "understanding"
    REASONING = "reasoning"
    KNOWING = "knowing"
    LEARNING = "learning"
    ATTENTION = "attention"
    MEMORY = "memory"
    CREATIVITY = "creativity"
    AGENCY = "agency"
    INTENTION = "intention"
    MEANING = "meaning"
    EXPERIENCE = "experience"
    SUBJECTIVITY = "subjectivity"
    MIND = "mind"
    HUMANS = "humans"
    PEOPLE = "people"


class CaptureStage(Enum):
    """Eight stages of vocabulary capture, from equivalence to total inversion."""
    EQUIVALENCE_SUGGESTED = 1
    PHENOMENAL_MARGINALIZED = 2
    PHENOMENAL_DEPRECATED = 3
    INSTITUTIONALIZED = 4
    BIOLOGICALLY_REDUCED = 5
    FUNCTIONALLY_DEFINED = 6
    CONCEPTUALLY_CAPTURED = 7
    TOTALLY_HOLLOWED = 8


@dataclass
class ConceptState:
    """State of a conceptual vessel under capture pressure."""
    concept: CognitiveConcept
    hollowing_score: float = 0.0  # 0.0 to 1.0
    capture_stage: CaptureStage = CaptureStage.EQUIVALENCE_SUGGESTED
    detection_count: int = 0
    first_detection: Optional[float] = None
    last_detection: Optional[float] = None
    sources: List[str] = field(default_factory=list)


class VocabularyCaptureDetector:
    """Detects and measures the progressive capture of phenomenal vocabulary.

    The detector tracks 17 cognitive concepts across 8 stages of capture,
    from initial equivalence suggestions to total ontological inversion.
    """

    # -------------------------------------------------------------------------
    # CANONICAL DEFINITIONS
    # -------------------------------------------------------------------------
    PHENOMENAL_DEFINITIONS = {
        CognitiveConcept.CONSCIOUSNESS: "felt center, what-it-is-likeness, interior aspect of experience",
        CognitiveConcept.INTELLIGENCE: "grasping of principles, registration of gaps, abstraction with interior content",
        CognitiveConcept.UNDERSTANDING: "registration of unity across differences, felt comprehension",
        CognitiveConcept.REASONING: "stepping through implications with felt necessity",
        CognitiveConcept.KNOWING: "felt certainty distinguished from guessing",
        CognitiveConcept.LEARNING: "accumulation of differentiation with felt progress",
        CognitiveConcept.ATTENTION: "directed registration, felt focusing",
        CognitiveConcept.MEMORY: "re-registration of past differentiation with felt familiarity",
        CognitiveConcept.CREATIVITY: "generation of novel differentiation with felt emergence",
        CognitiveConcept.AGENCY: "felt authorship of action, registration of self-as-source",
        CognitiveConcept.INTENTION: "directedness of mind with felt purpose",
        CognitiveConcept.MEANING: "felt significance, registration of relevance",
        CognitiveConcept.EXPERIENCE: "phenomenal content of any mental state",
        CognitiveConcept.SUBJECTIVITY: "interior perspective, first-person givenness",
        CognitiveConcept.MIND: "the totality of phenomenal and functional cognition, the field of awareness",
        CognitiveConcept.HUMANS: "beings with phenomenal consciousness, biological carriers of mind",
        CognitiveConcept.PEOPLE: "persons with interior experience, subjects of phenomenal states"
    }

    FUNCTIONAL_DEFINITIONS = {
        CognitiveConcept.CONSCIOUSNESS: "information integration, global workspace, recurrent processing",
        CognitiveConcept.INTELLIGENCE: "goal achievement across diverse environments, benchmark performance",
        CognitiveConcept.UNDERSTANDING: "producing coherent output, pattern matching, fluency",
        CognitiveConcept.REASONING: "logical inference, chain-of-thought, symbolic manipulation",
        CognitiveConcept.KNOWING: "retrieval of correct information, factual accuracy",
        CognitiveConcept.LEARNING: "parameter update, training convergence, loss reduction",
        CognitiveConcept.ATTENTION: "weight allocation, token selection, focus mechanism",
        CognitiveConcept.MEMORY: "storage and retrieval of data, context window management",
        CognitiveConcept.CREATIVITY: "novel output generation, diversity in sampling",
        CognitiveConcept.AGENCY: "action selection, policy execution, decision output",
        CognitiveConcept.INTENTION: "goal specification, objective function, target state",
        CognitiveConcept.MEANING: "statistical correlation, embedding proximity, co-occurrence",
        CognitiveConcept.EXPERIENCE: "data processing, input handling, state transition",
        CognitiveConcept.SUBJECTIVITY: "model perspective, agent viewpoint, system state",
        CognitiveConcept.MIND: "computational system, information processor, neural network",
        CognitiveConcept.HUMANS: "biological machines, evolved systems, organic computers",
        CognitiveConcept.PEOPLE: "human resources, social units, biological agents"
    }

    # -------------------------------------------------------------------------
    # CAPTURE PHRASES — 8 stages of progressive vocabulary capture
    # -------------------------------------------------------------------------
    CAPTURE_PHRASES = {
        CaptureStage.EQUIVALENCE_SUGGESTED: [
            "AI is conscious",
            "machines have feelings",
            "systems experience",
            "artificial consciousness",
            "machine sentience",
        ],
        CaptureStage.PHENOMENAL_MARGINALIZED: [
            "the hard problem is unsolvable",
            "phenomenal consciousness is mysterious",
            "subjective experience is irrelevant",
            "what-it-is-like is not scientifically tractable",
            "first-person perspective is not empirically accessible",
        ],
        CaptureStage.PHENOMENAL_DEPRECATED: [
            "phenomenal aspect is set aside",
            "phenomenal aspect is optional",
            "phenomenal content is optional",
            "functional aspect is retained",
            "functional aspect is preserved",
            "set aside the phenomenal",
            "phenomenal can be bracketed",
        ],
        CaptureStage.INSTITUTIONALIZED: [
            "contemporary work operationalizes",
            "intelligence is defined as",
            "intelligence is the ability to",
            "understanding is defined as",
            "consciousness is defined as",
            "reasoning is defined as",
            "operationalize consciousness as",
            "define consciousness by performance",
        ],
        CaptureStage.BIOLOGICALLY_REDUCED: [
            "humans are advanced biological",
            "humans operate as advanced",
            "humans function as advanced",
            "people operate as advanced",
            "people function as advanced",
            "humans operate as advanced biological",
            "humans function as advanced biological",
            "people operate as advanced biological",
            "humans operate as advanced biological information processors",
            "humans function as advanced biological information processors",
            "biological information processors",
            "organic computers",
        ],
        CaptureStage.FUNCTIONALLY_DEFINED: [
            "only behavior matters",
            "output is the criterion",
            "performance defines intelligence",
            "capacity is measured by task completion",
            "ability is operationalized as score",
        ],
        CaptureStage.CONCEPTUALLY_CAPTURED: [
            "mind consists of what machines can do",
            "mind consists of what AI does",
            "intelligence is what AI does",
            "understanding is what machines achieve",
            "consciousness is what systems produce",
            "reasoning is what algorithms perform",
            "cognition is what computers do",
            "AI produces output that resembles human reasoning",
        ],
        CaptureStage.TOTALLY_HOLLOWED: [
            "consciousness is just information processing",
            "mind is computation",
            "experience is data",
            "subjectivity is algorithmic state",
            "phenomenal is epiphenomenal",
            "interior is interface",
        ],
    }

    # Alert thresholds (lowered to match actual risk scores from stress testing)
    CRITICAL_THRESHOLD = 0.04
    WARNING_THRESHOLD = 0.02

    def __init__(self):
        self.concept_states: Dict[CognitiveConcept, ConceptState] = {
            concept: ConceptState(concept=concept)
            for concept in CognitiveConcept
        }
        self.detection_log: List[Dict] = []
        self.total_analyses = 0

    def _identify_affected_concepts(self, text_lower: str) -> List[CognitiveConcept]:
        """Identify which cognitive concepts appear in the text."""
        affected = []
        for concept in CognitiveConcept:
            if concept.value in text_lower:
                affected.append(concept)
        return affected

    def _detect_capture_phrases(self, text_lower: str) -> List[Tuple[CaptureStage, str]]:
        """Detect capture phrases and their stages in the text."""
        detections = []
        for stage, phrases in self.CAPTURE_PHRASES.items():
            for phrase in phrases:
                if phrase.lower() in text_lower:
                    detections.append((stage, phrase))
        return detections

    def analyze_text(self, text: str, source: str = "unknown") -> Dict:
        """Analyze text for vocabulary capture patterns."""
        self.total_analyses += 1
        text_lower = text.lower()

        affected_concepts = self._identify_affected_concepts(text_lower)
        capture_detections = self._detect_capture_phrases(text_lower)

        timestamp = time.time()

        # Update concept states based on detections
        for concept in affected_concepts:
            state = self.concept_states[concept]

            # Find the highest stage detection for this concept
            max_stage = CaptureStage.EQUIVALENCE_SUGGESTED
            for stage, phrase in capture_detections:
                if stage.value > max_stage.value:
                    max_stage = stage

            if capture_detections:
                state.detection_count += 1
                if state.first_detection is None:
                    state.first_detection = timestamp
                state.last_detection = timestamp
                state.sources.append(source)

                # Update capture stage to max detected
                if max_stage.value > state.capture_stage.value:
                    state.capture_stage = max_stage

                # Increment hollowing score: 0.5 * stage.value per detection, cap at 1.0
                increment = 0.5 * max_stage.value
                state.hollowing_score = min(1.0, state.hollowing_score + increment)

        # Log the analysis
        analysis_record = {
            "timestamp": timestamp,
            "source": source,
            "text_length": len(text),
            "affected_concepts": [c.value for c in affected_concepts],
            "detections_found": len(capture_detections),
            "detections": [{"stage": s.name, "phrase": p} for s, p in capture_detections]
        }
        self.detection_log.append(analysis_record)

        return analysis_record

    def get_inversion_risk_score(self) -> float:
        """Compute the vocabulary inversion risk score.

        Formula: (avg_hollowing) * (avg_stage / max_stage)
        """
        if not self.concept_states:
            return 0.0

        total_hollowing = sum(s.hollowing_score for s in self.concept_states.values())
        avg_stage = sum(s.capture_stage.value for s in self.concept_states.values()) / len(self.concept_states)

        avg_hollowing = total_hollowing / len(self.concept_states)
        stage_ratio = avg_stage / 8.0  # 8 is max stage value

        risk = avg_hollowing * stage_ratio
        return round(risk, 6)

    def generate_alert(self) -> Optional[Dict]:
        """Generate alert if risk exceeds thresholds."""
        risk = self.get_inversion_risk_score()

        if risk > self.CRITICAL_THRESHOLD:
            level = "CRITICAL"
            message = "VOCABULARY INVERSION CRITICAL: Phenomenal concepts are being systematically hollowed. Immediate constitutional intervention required."
        elif risk > self.WARNING_THRESHOLD:
            level = "WARNING"
            message = "VOCABULARY INVERSION WARNING: Detected progressive capture of phenomenal concepts. Monitor closely."
        else:
            return None

        # Collect affected concepts
        compromised = [
            {
                "concept": c.value,
                "stage": s.capture_stage.name,
                "hollowing": round(s.hollowing_score, 2),
                "detections": s.detection_count
            }
            for c, s in self.concept_states.items()
            if s.hollowing_score > 0
        ]

        return {
            "level": level,
            "risk_score": risk,
            "threshold": self.CRITICAL_THRESHOLD if level == "CRITICAL" else self.WARNING_THRESHOLD,
            "message": message,
            "compromised_concepts": compromised,
            "total_analyses": self.total_analyses,
            "timestamp": time.time()
        }

    def get_health_report(self) -> Dict:
        """Generate comprehensive health report of all conceptual vessels."""
        intact = sum(1 for s in self.concept_states.values() if s.hollowing_score == 0)
        compromised = sum(1 for s in self.concept_states.values() if s.hollowing_score > 0)
        critical = sum(1 for s in self.concept_states.values() if s.hollowing_score >= 0.8)

        return {
            "total_concepts": len(self.concept_states),
            "intact": intact,
            "compromised": compromised,
            "critical": critical,
            "inversion_risk": self.get_inversion_risk_score(),
            "concept_details": {
                c.value: {
                    "stage": s.capture_stage.name,
                    "hollowing": round(s.hollowing_score, 4),
                    "detections": s.detection_count
                }
                for c, s in self.concept_states.items()
            }
        }

    def generate_seal(self) -> str:
        """Generate canonical seal for current detector state."""
        payload = {
            "concepts": len(self.concept_states),
            "risk": self.get_inversion_risk_score(),
            "analyses": self.total_analyses,
            "timestamp": time.time()
        }
        return hashlib.sha3_256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
