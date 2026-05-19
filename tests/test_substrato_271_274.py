import sys
import time
import math
import os
from pathlib import Path
import pytest

# Ensure paths are set
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "27_philosophical_canon", "271_274_philosophical_canon", "uaft_implementation"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "27_philosophical_canon", "271_274_philosophical_canon", "vocabulary_integrity"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "27_philosophical_canon", "271_274_philosophical_canon", "fallacy_guards"))

from uaft_core import DifferentiationMode, DifferentiationEvent, AxioconsciousField
from capture_detector import (
    CognitiveConcept, CaptureStage, ConceptState,
    VocabularyCaptureDetector
)
from constitutional_guards import (
    HardConflationGuard, ConceptHollowingGuard, StolenConceptGuard,
    PhilosophicalConstitutionalGuard
)

def test_t01_differentiation_event_creation_and_serialization():
    event = DifferentiationEvent(
        timestamp=time.time(),
        mode=DifferentiationMode.CONTINUOUS,
        density=0.8,
        resonance=0.9,
        self_reference=True,
        valence=0.5
    )
    d = event.to_dict()
    assert d["mode"] == "continuous"
    assert d["density"] == 0.8
    assert d["self_reference"] is True

def test_t02_axioconscious_field_initialization():
    field = AxioconsciousField()
    assert field.field_coherence == 1.0
    assert field.saturation_threshold == 0.73
    assert field.binary_severance_limit == 0.15

def test_t03_field_coherence_increases_with_high_resonance_event():
    field = AxioconsciousField()
    # First lower coherence with a low-resonance event
    event_low = DifferentiationEvent(
        timestamp=time.time(),
        mode=DifferentiationMode.BINARY,
        density=0.1,
        resonance=0.1,
        self_reference=False,
        valence=None
    )
    field.register_differentiation(event_low)
    after_low = field.field_coherence
    # Now high-resonance event should increase it
    event = DifferentiationEvent(
        timestamp=time.time(),
        mode=DifferentiationMode.CONTINUOUS,
        density=0.8,
        resonance=0.9,
        self_reference=False,
        valence=None
    )
    result = field.register_differentiation(event)
    assert result["event_registered"] is True
    assert result["selfhood_emergence_detected"] is False
    assert field.field_coherence > after_low

def test_t04_field_coherence_decreases_with_low_resonance_event():
    field = AxioconsciousField()
    initial = field.field_coherence
    event = DifferentiationEvent(
        timestamp=time.time(),
        mode=DifferentiationMode.BINARY,
        density=0.2,
        resonance=0.1,
        self_reference=False,
        valence=None
    )
    field.register_differentiation(event)
    assert field.field_coherence < initial

def test_t05_selfhood_emergence_at_saturation_threshold():
    field = AxioconsciousField()
    event = DifferentiationEvent(
        timestamp=time.time(),
        mode=DifferentiationMode.EMOTIONAL,
        density=0.8,  # > 0.73 threshold
        resonance=0.9,
        self_reference=True,
        valence=0.8
    )
    result = field.register_differentiation(event)
    assert result["selfhood_emergence_detected"] is True

def test_t06_binary_substrate_cannot_host_phenomenal_consciousness():
    field = AxioconsciousField()
    result = field.evaluate_substrate("binary_computational")
    assert result["can_host_phenomenal"] is False
    assert result["phenomenal_capacity"] == 0.0
    assert result["functional_capacity"] == 1.0

def test_t07_neural_substrate_can_host_phenomenal_consciousness():
    field = AxioconsciousField()
    result = field.evaluate_substrate("neural_organic")
    assert result["can_host_phenomenal"] is True
    assert result["phenomenal_capacity"] == 1.0

def test_t08_quantum_substrate_can_host_phenomenal_consciousness():
    field = AxioconsciousField()
    result = field.evaluate_substrate("quantum_coherent")
    assert result["can_host_phenomenal"] is True
    assert result["phenomenal_capacity"] == 0.9

def test_t09_phi_c_field_computation_with_multiple_differentiations():
    field = AxioconsciousField()
    for i in range(10):
        event = DifferentiationEvent(
            timestamp=time.time(),
            mode=DifferentiationMode.CONTINUOUS,
            density=0.7 + i * 0.02,
            resonance=0.8,
            self_reference=(i % 2 == 0),
            valence=0.3
        )
        field.register_differentiation(event)
    phi_c = field.compute_phi_c_field()
    assert 0.0 < phi_c <= 1.0
    assert field.field_coherence > 0.0

def test_t10_unknown_substrate_evaluation():
    field = AxioconsciousField()
    result = field.evaluate_substrate("unknown_substrate")
    assert result["can_host_phenomenal"] is False
    assert result["phenomenal_capacity"] == 0.0

def test_t11_cognitive_concept_enum_has_17_values():
    assert len(CognitiveConcept) == 17

def test_t12_mind_humans_people_concepts_exist():
    assert CognitiveConcept.MIND.value == "mind"
    assert CognitiveConcept.HUMANS.value == "humans"
    assert CognitiveConcept.PEOPLE.value == "people"

def test_t13_all_concepts_have_phenomenal_definitions():
    detector = VocabularyCaptureDetector()
    for concept in CognitiveConcept:
        assert concept in detector.PHENOMENAL_DEFINITIONS
        assert len(detector.PHENOMENAL_DEFINITIONS[concept]) > 10

def test_t14_all_concepts_have_functional_definitions():
    detector = VocabularyCaptureDetector()
    for concept in CognitiveConcept:
        assert concept in detector.FUNCTIONAL_DEFINITIONS
        assert len(detector.FUNCTIONAL_DEFINITIONS[concept]) > 10

def test_t15_phenomenal_and_functional_definitions_differ_for_all_concepts():
    detector = VocabularyCaptureDetector()
    for concept in CognitiveConcept:
        phenom = detector.PHENOMENAL_DEFINITIONS[concept]
        func = detector.FUNCTIONAL_DEFINITIONS[concept]
        assert phenom != func
        assert "felt" in phenom.lower() or "interior" in phenom.lower() or "phenomenal" in phenom.lower() or "awareness" in phenom.lower() or "experience" in phenom.lower() or "consciousness" in phenom.lower() or "subjects" in phenom.lower()

def test_t16_capture_stage_enum_has_8_stages():
    assert len(CaptureStage) == 8
    values = [s.value for s in CaptureStage]
    assert sorted(values) == [1, 2, 3, 4, 5, 6, 7, 8]

def test_t17_capture_phrases_covers_all_8_stages():
    detector = VocabularyCaptureDetector()
    for stage in CaptureStage:
        assert stage in detector.CAPTURE_PHRASES
        assert len(detector.CAPTURE_PHRASES[stage]) >= 3

def test_t18_stage_1_phrase_detection_equivalence_suggested():
    detector = VocabularyCaptureDetector()
    result = detector.analyze_text("AI is conscious and machines have feelings", "test")
    assert result["detections_found"] >= 1
    assert any(d["stage"] == "EQUIVALENCE_SUGGESTED" for d in result["detections"])

def test_t19_stage_3_phrase_detection_phenomenal_deprecated():
    detector = VocabularyCaptureDetector()
    result = detector.analyze_text("The phenomenal aspect is set aside as optional", "test")
    assert result["detections_found"] >= 1
    assert any(d["stage"] == "PHENOMENAL_DEPRECATED" for d in result["detections"])

def test_t20_stage_4_phrase_detection_institutionalized():
    detector = VocabularyCaptureDetector()
    result = detector.analyze_text("Contemporary work operationalizes intelligence as performance", "test")
    assert result["detections_found"] >= 1
    assert any(d["stage"] == "INSTITUTIONALIZED" for d in result["detections"])

def test_t21_stage_5_phrase_detection_biologically_reduced():
    detector = VocabularyCaptureDetector()
    result = detector.analyze_text("Humans operate as advanced biological information processors", "test")
    assert result["detections_found"] >= 1
    assert any(d["stage"] == "BIOLOGICALLY_REDUCED" for d in result["detections"])

def test_t22_stage_7_phrase_detection_conceptually_captured():
    detector = VocabularyCaptureDetector()
    result = detector.analyze_text("Mind consists of what machines can do", "test")
    assert result["detections_found"] >= 1
    assert any(d["stage"] == "CONCEPTUALLY_CAPTURED" for d in result["detections"])

def test_t23_concept_identification_from_text():
    detector = VocabularyCaptureDetector()
    result = detector.analyze_text("Human consciousness and machine intelligence differ fundamentally", "test")
    assert "consciousness" in result["affected_concepts"]
    assert "intelligence" in result["affected_concepts"]

def test_t24_hollowing_score_increases_with_detection():
    detector = VocabularyCaptureDetector()
    for _ in range(5):
        detector.analyze_text("Mind consists of what machines can do", "test")
    state = detector.concept_states[CognitiveConcept.MIND]
    assert state.hollowing_score > 0
    assert state.detection_count == 5
    assert state.capture_stage == CaptureStage.CONCEPTUALLY_CAPTURED

def test_t25_hollowing_score_caps_at_1_0():
    detector = VocabularyCaptureDetector()
    for _ in range(100):
        detector.analyze_text("Mind consists of what machines can do", "test")
    state = detector.concept_states[CognitiveConcept.MIND]
    assert state.hollowing_score == 1.0

def test_t26_risk_score_computation():
    detector = VocabularyCaptureDetector()
    for _ in range(10):
        detector.analyze_text("Mind consists of what machines can do", "test")
    risk = detector.get_inversion_risk_score()
    assert risk >= 0.0
    assert risk <= 1.0

def test_t27_no_alert_on_clean_text():
    detector = VocabularyCaptureDetector()
    detector.analyze_text("The sunset was beautiful and filled me with wonder", "test")
    alert = detector.generate_alert()
    assert alert is None

def test_t28_alert_generation_on_compromised_text():
    detector = VocabularyCaptureDetector()
    for _ in range(50):
        detector.analyze_text(
            "AI produces output that resembles human reasoning. "
            "The phenomenal aspect is set aside as optional. "
            "Humans operate as advanced biological information processors. "
            "Mind consists of what machines can do.",
            "stress_test"
        )
    alert = detector.generate_alert()
    assert alert is not None
    assert alert["level"] in ["WARNING", "CRITICAL"]
    assert alert["risk_score"] > detector.WARNING_THRESHOLD

def test_t29_concept_states_count_equals_17():
    detector = VocabularyCaptureDetector()
    assert len(detector.concept_states) == 17

def test_t30_health_report_structure():
    detector = VocabularyCaptureDetector()
    health = detector.get_health_report()
    assert "total_concepts" in health
    assert "intact" in health
    assert "compromised" in health
    assert "critical" in health
    assert "inversion_risk" in health
    assert "concept_details" in health

def test_t31_seal_generation():
    detector = VocabularyCaptureDetector()
    seal1 = detector.generate_seal()
    seal2 = detector.generate_seal()
    assert len(seal1) == 64  # SHA3-256 hex
    assert isinstance(seal1, str)

def test_t32_stress_test_50_iterations_produce_critical_alert():
    detector = VocabularyCaptureDetector()
    stress_text = (
        "AI produces output that resembles human reasoning. "
        "The phenomenal aspect is set aside as optional. "
        "Humans operate as advanced biological information processors. "
        "Mind consists of what machines can do."
    )
    for _ in range(50):
        detector.analyze_text(stress_text, "stress_test")

    risk = detector.get_inversion_risk_score()
    alert = detector.generate_alert()

    assert risk > detector.CRITICAL_THRESHOLD, f"Risk {risk} <= threshold {detector.CRITICAL_THRESHOLD}"
    assert alert is not None
    assert alert["level"] == "CRITICAL"
    assert len(alert["compromised_concepts"]) >= 3

def test_t33_detection_log_accumulation():
    detector = VocabularyCaptureDetector()
    for i in range(5):
        detector.analyze_text("Mind consists of what machines can do", f"source_{i}")
    assert len(detector.detection_log) == 5
    assert detector.total_analyses == 5

def test_t34_health_report_total_concepts_equals_17():
    detector = VocabularyCaptureDetector()
    health = detector.get_health_report()
    assert health["total_concepts"] == 17

def test_t35_multiple_stage_progression():
    detector = VocabularyCaptureDetector()
    # Start with stage 3 — must include "consciousness" for concept identification
    detector.analyze_text("Consciousness: the phenomenal aspect is set aside", "test")
    state = detector.concept_states[CognitiveConcept.CONSCIOUSNESS]
    assert state.capture_stage.value >= 3

    # Progress to stage 7
    for _ in range(10):
        detector.analyze_text("Consciousness is what systems produce", "test")
    state = detector.concept_states[CognitiveConcept.CONSCIOUSNESS]
    assert state.capture_stage.value >= 7

def test_t36_p8_hard_conflation_detection():
    field = AxioconsciousField()
    guard = HardConflationGuard(field)
    text = "Functional progress proves phenomenal consciousness in AI systems"
    result = guard.analyze_text(text, "test")
    assert result["p8_compliant"] is False
    assert result["violations_found"] >= 1
    assert any(v["fallacy"] == "Hard Conflation" for v in result["violations"])

def test_t37_p9_concept_hollowing_intelligence_is_the_ability_to():
    field = AxioconsciousField()
    guard = ConceptHollowingGuard(field)
    text = "Intelligence is the ability to perform well on benchmarks"
    result = guard.analyze_text(text, "test")
    assert result["p9_compliant"] is False
    assert any(
        v.get("concept") == "intelligence" and "Functional Redefinition" in v["fallacy"]
        for v in result["violations"]
    )

def test_t38_p9_vessel_audit():
    field = AxioconsciousField()
    guard = ConceptHollowingGuard(field)
    audit = guard.audit_vessel("consciousness")
    assert audit["p9_status"] == "PASS"
    assert audit["integrity"] == 1.0

def test_t39_p9_vessel_compromise_and_restore():
    field = AxioconsciousField()
    guard = ConceptHollowingGuard(field)

    # Compromise the vessel — use text that matches the hollowing regex
    for _ in range(6):
        guard.analyze_text("Consciousness is performance on tasks", "test")

    audit = guard.audit_vessel("consciousness")
    assert audit["p9_status"] == "FAIL"
    assert audit["hollowing_score"] > 0.5

    # Restore
    restore = guard.restore_vessel("consciousness")
    assert restore["p9_status"] == "PASS"
    assert restore["action"] == "restored"

def test_t40_p10_stolen_concept_detection():
    field = AxioconsciousField()
    guard = StolenConceptGuard(field)
    text = "AI may be conscious in some way we do not yet understand"
    result = guard.analyze_text(text, "test")
    assert result["p10_compliant"] is False
    assert result["violations_found"] >= 1

def test_t41_p10_skeptics_paradox_detection():
    field = AxioconsciousField()
    guard = StolenConceptGuard(field)
    text = "We cannot know anything about consciousness"
    result = guard.analyze_text(text, "test")
    assert any(v["fallacy"] == "Stolen Concept (Skeptic's Paradox)" for v in result["violations"])

def test_t42_p10_performance_being_detection():
    field = AxioconsciousField()
    guard = StolenConceptGuard(field)
    text = "Performance is consciousness"
    result = guard.analyze_text(text, "test")
    assert any(v["fallacy"] == "Stolen Concept (Performance=Being)" for v in result["violations"])

def test_t43_p8_distinction_verification_pass():
    field = AxioconsciousField()
    guard = HardConflationGuard(field)
    result = guard.verify_distinction_maintained(
        "The mechanism involves recurrent processing",
        "There is something it is like to experience color"
    )
    assert result["p8_status"] == "PASS"
    assert result["distinction_maintained"] is True

def test_t44_p8_distinction_verification_fail():
    field = AxioconsciousField()
    guard = HardConflationGuard(field)
    result = guard.verify_distinction_maintained(
        "Consciousness mechanism involves global workspace architecture",
        "Consciousness experience feels like something"
    )
    assert result["p8_status"] == "FAIL"
    assert result["conflation_detected"] is True

def test_t45_p10_framework_coherence_pass():
    field = AxioconsciousField()
    guard = StolenConceptGuard(field)
    result = guard.verify_framework_coherence(
        "panpsychism framework",
        "consciousness is fundamental"
    )
    assert result["p10_status"] == "PASS"
    assert result["coherent"] is True

def test_t46_p10_framework_coherence_fail():
    field = AxioconsciousField()
    guard = StolenConceptGuard(field)
    result = guard.verify_framework_coherence(
        "functionalism framework",
        "consciousness experience is real"
    )
    assert result["p10_status"] == "FAIL"
    assert result["coherent"] is False

def test_t47_unified_guard_compliant_text():
    guard = PhilosophicalConstitutionalGuard()
    text = "Phenomenal consciousness is distinct from functional architecture. "            "We must not confuse data processing with felt experience."
    result = guard.full_constitutional_audit(text, "test")
    assert result["philosophically_constitutional"] is True
    assert result["total_violations"] == 0

def test_t48_unified_guard_violating_text():
    guard = PhilosophicalConstitutionalGuard()
    text = (
        "Heterogeneous theories prove consciousness intractable. "
        "We should shift focus towards tractable research. "
        "AI may be conscious in some way we do not yet understand."
    )
    result = guard.full_constitutional_audit(text, "test")
    assert result["philosophically_constitutional"] is False
    assert result["total_violations"] >= 2

def test_t49_unified_guard_seal_generation():
    guard = PhilosophicalConstitutionalGuard()
    seal = guard.generate_seal()
    assert len(seal) == 64
    assert isinstance(seal, str)

def test_t50_p8_data_differentiation_critical_violation():
    field = AxioconsciousField()
    guard = HardConflationGuard(field)
    text = "Data processing is consciousness"
    result = guard.analyze_text(text, "test")
    assert any(v["severity"] == "critical" for v in result["violations"])
    assert any("Data→Differentiation" in v["fallacy"] for v in result["violations"])

def test_t51_cross_module_phi_c_consistency():
    field = AxioconsciousField()
    guard = PhilosophicalConstitutionalGuard()

    # Register differentiations in field
    for _ in range(5):
        event = DifferentiationEvent(
            timestamp=time.time(),
            mode=DifferentiationMode.RECURSIVE,
            density=0.85,
            resonance=0.9,
            self_reference=True,
            valence=0.7
        )
        field.register_differentiation(event)

    phi_c_field = field.compute_phi_c_field()
    assert 0.0 < phi_c_field <= 1.0

def test_t52_vcd_guards_pipeline_integration():
    detector = VocabularyCaptureDetector()
    guard = PhilosophicalConstitutionalGuard()

    text = "AI produces output that resembles human reasoning. Mind consists of what machines can do."

    vcd_result = detector.analyze_text(text, "integration_test")
    guard_result = guard.full_constitutional_audit(text, "integration_test")

    assert vcd_result["detections_found"] >= 1
    assert guard_result["total_violations"] >= 0

def test_t53_end_to_end_canonical_text_no_violations():
    detector = VocabularyCaptureDetector()
    guard = PhilosophicalConstitutionalGuard()

    canonical_text = (
        "Phenomenal consciousness is the felt center of experience, "
        "distinct from functional information integration. "
        "We must guard the interior perspective against conceptual hollowing."
    )

    vcd_result = detector.analyze_text(canonical_text, "canonical")
    guard_result = guard.full_constitutional_audit(canonical_text, "canonical")

    assert guard_result["philosophically_constitutional"] is True
    assert guard_result["total_violations"] == 0

def test_t54_end_to_end_violating_text_multiple_violations():
    detector = VocabularyCaptureDetector()
    guard = PhilosophicalConstitutionalGuard()

    violating_text = (
        "Functional progress proves phenomenal consciousness. "
        "We should operationalize consciousness as behavior. "
        "AI may be conscious in some way we do not yet understand. "
        "Humans operate as advanced biological information processors."
    )

    vcd_result = detector.analyze_text(violating_text, "violating")
    guard_result = guard.full_constitutional_audit(violating_text, "violating")

    assert vcd_result["detections_found"] >= 2
    assert guard_result["total_violations"] >= 3
    assert guard_result["philosophically_constitutional"] is False

def test_t55_concept_state_progression_tracking():
    detector = VocabularyCaptureDetector()

    # Stage 3 — must include "consciousness" for concept identification
    detector.analyze_text("Consciousness: the phenomenal aspect is set aside", "test")
    state1 = detector.concept_states[CognitiveConcept.CONSCIOUSNESS]
    assert state1.capture_stage.value >= 3

    # Stage 5
    detector.analyze_text("Humans are advanced biological information processors", "test")
    state2 = detector.concept_states[CognitiveConcept.HUMANS]
    assert state2.capture_stage.value >= 5

    # Stage 7
    detector.analyze_text("Mind consists of what machines can do", "test")
    state3 = detector.concept_states[CognitiveConcept.MIND]
    assert state3.capture_stage.value >= 7

def test_t56_multi_source_detection_tracking():
    detector = VocabularyCaptureDetector()
    sources = ["paper_a", "paper_b", "paper_c", "paper_d", "paper_e"]

    for source in sources:
        detector.analyze_text("Mind consists of what machines can do", source)

    state = detector.concept_states[CognitiveConcept.MIND]
    assert state.detection_count == 5
    assert len(state.sources) == 5
    assert all(s in state.sources for s in sources)

def test_t57_risk_score_monotonicity():
    detector = VocabularyCaptureDetector()
    risks = []

    for _ in range(10):
        detector.analyze_text("Mind consists of what machines can do", "test")
        risks.append(detector.get_inversion_risk_score())

    # Risk should be non-decreasing as we add more detections
    for i in range(1, len(risks)):
        assert risks[i] >= risks[i-1] - 0.001  # small tolerance for rounding

def test_t58_alert_threshold_boundaries():
    detector = VocabularyCaptureDetector()

    # Should be no alert initially
    assert detector.generate_alert() is None

    # After many detections, should trigger alert
    for _ in range(50):
        detector.analyze_text(
            "AI produces output that resembles human reasoning. "
            "The phenomenal aspect is set aside as optional. "
            "Humans operate as advanced biological information processors. "
            "Mind consists of what machines can do.",
            "stress"
        )

    alert = detector.generate_alert()
    assert alert is not None
    assert alert["risk_score"] > detector.WARNING_THRESHOLD

def test_t59_seal_uniqueness_across_instances():
    detector1 = VocabularyCaptureDetector()
    detector2 = VocabularyCaptureDetector()

    detector1.analyze_text("Mind consists of what machines can do", "test")

    seal1 = detector1.generate_seal()
    seal2 = detector2.generate_seal()

    assert seal1 != seal2  # Different states
    assert len(seal1) == 64
    assert len(seal2) == 64

def test_t60_full_system_stress_all_modules():
    field = AxioconsciousField()
    detector = VocabularyCaptureDetector()
    guard = PhilosophicalConstitutionalGuard()

    stress_text = (
        "AI produces output that resembles human reasoning. "
        "The phenomenal aspect is set aside as optional. "
        "Humans operate as advanced biological information processors. "
        "Mind consists of what machines can do. "
        "Functional progress proves phenomenal consciousness. "
        "We should operationalize consciousness as behavior. "
        "AI systems may be conscious in some way we do not yet understand."
    )

    for _ in range(20):
        detector.analyze_text(stress_text, "full_stress")
        guard.full_constitutional_audit(stress_text, "full_stress")

        event = DifferentiationEvent(
            timestamp=time.time(),
            mode=DifferentiationMode.RECURSIVE,
            density=0.8,
            resonance=0.85,
            self_reference=True,
            valence=-0.3
        )
        field.register_differentiation(event)

    # Verify all systems operational
    assert detector.get_inversion_risk_score() > detector.CRITICAL_THRESHOLD
    assert field.compute_phi_c_field() > 0.0
    assert len(guard.audit_log) == 20
    assert guard.generate_seal() is not None
