import pytest
from arkhe_os.ethics.ai_governance import AIEthicsGovernanceEngine, IntegratedTriagePipeline

def test_ai_ethics_governance_engine():
    engine = AIEthicsGovernanceEngine()

    # Mock NAFLD triage predictions
    predictions_fair = [
        {"patient_id": "1", "demographics": {"sex": "M"}, "prediction": True},
        {"patient_id": "2", "demographics": {"sex": "M"}, "prediction": False},
        {"patient_id": "3", "demographics": {"sex": "F"}, "prediction": True},
        {"patient_id": "4", "demographics": {"sex": "F"}, "prediction": False},
    ]

    predictions_unfair = [
        {"patient_id": "1", "demographics": {"sex": "M"}, "prediction": True},
        {"patient_id": "2", "demographics": {"sex": "M"}, "prediction": True},
        {"patient_id": "3", "demographics": {"sex": "F"}, "prediction": False},
        {"patient_id": "4", "demographics": {"sex": "F"}, "prediction": False},
    ]

    # Mock model traces
    trace_explainable = {
        "feature_importance": {"phi_c": 0.4, "age": 0.3, "bmi": 0.3}
    }

    trace_opaque = {
        "feature_importance": {"phi_c": 0.05, "age": 0.45, "bmi": 0.5}
    }

    # 1. Test passing case
    report_pass = engine.evaluate_model_compliance(
        model_id="model_nafld_v1",
        predictions=predictions_fair,
        model_trace=trace_explainable
    )

    assert report_pass.passed is True
    assert report_pass.fairness_score == 1.0  # 50% vs 50%
    assert report_pass.explainability_score >= 0.9
    assert "fairness_proof" in report_pass.zk_proofs
    assert "explainability_proof" in report_pass.zk_proofs

    # 2. Test failing fairness
    report_fail_fairness = engine.evaluate_model_compliance(
        model_id="model_nafld_v2",
        predictions=predictions_unfair,
        model_trace=trace_explainable
    )
    assert report_fail_fairness.passed is False
    assert report_fail_fairness.fairness_score < 0.8
    assert "fairness_proof" not in report_fail_fairness.zk_proofs
    assert "explainability_proof" in report_fail_fairness.zk_proofs

    # 3. Test failing explainability
    report_fail_expl = engine.evaluate_model_compliance(
        model_id="model_nafld_v3",
        predictions=predictions_fair,
        model_trace=trace_opaque
    )
    assert report_fail_expl.passed is False
    assert report_fail_expl.explainability_score < 0.9
    assert "explainability_proof" not in report_fail_expl.zk_proofs

def test_integrated_triage_pipeline():
    engine = AIEthicsGovernanceEngine()
    # Mock Vault and Simulator
    vault = object()
    simulator = object()

    pipeline = IntegratedTriagePipeline(engine, vault, simulator)

    predictions_fair = [
        {"patient_id": "1", "demographics": {"sex": "M"}, "prediction": True},
        {"patient_id": "2", "demographics": {"sex": "M"}, "prediction": False},
        {"patient_id": "3", "demographics": {"sex": "F"}, "prediction": True},
        {"patient_id": "4", "demographics": {"sex": "F"}, "prediction": False},
    ]
    trace_explainable = {
        "feature_importance": {"phi_c": 0.4, "age": 0.3, "bmi": 0.3}
    }

    # Pipeline should pass and return APPROVED status
    result = pipeline.run_compliant_triage("model_v1", predictions_fair, trace_explainable)
    assert result["status"] == "APPROVED"
    assert result["report"]["passed"] is True

    predictions_unfair = [
        {"patient_id": "1", "demographics": {"sex": "M"}, "prediction": True},
        {"patient_id": "2", "demographics": {"sex": "M"}, "prediction": True},
        {"patient_id": "3", "demographics": {"sex": "F"}, "prediction": False},
        {"patient_id": "4", "demographics": {"sex": "F"}, "prediction": False},
    ]

    # Pipeline should raise ValueError on unethical model
    with pytest.raises(ValueError, match="Ethics Audit Failed"):
        pipeline.run_compliant_triage("model_v2", predictions_unfair, trace_explainable)
