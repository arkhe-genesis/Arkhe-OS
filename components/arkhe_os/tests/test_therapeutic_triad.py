import pytest

def test_redox_federation():
    from arkhe_os.crypto.fhe.redox_federation import RedoxFederationFHE
    federation = RedoxFederationFHE(security_level=128)
    # Just checking initialization runs
    assert federation.params is not None

def test_meta_therapeutic_learner():
    from arkhe_os.therapeutic.meta_learning import MetaTherapeuticLearner, InterventionRecord
    learner = MetaTherapeuticLearner()
    record = InterventionRecord(
        intervention_id="int_1",
        target_pair="NAD/NADH",
        predicted_phi_delta=0.05,
        actual_phi_delta=0.08
    )
    learner.record_outcome(record)
    assert learner.efficacy_weights["int_1"] > 1.0

def test_global_redox_atlas():
    from arkhe_os.federated.global_redox_atlas import GlobalRedoxCoherenceAtlas
    atlas = GlobalRedoxCoherenceAtlas()

    # Needs 3 to trigger consensus
    atlas.submit_federated_data("inst_A", "liver", "healthy", "adult", 0.8, 0.01, 100, "sig")
    atlas.submit_federated_data("inst_B", "liver", "healthy", "adult", 0.85, 0.015, 150, "sig")
    atlas.submit_federated_data("inst_C", "liver", "healthy", "adult", 0.82, 0.012, 120, "sig")

    atlas.trigger_consensus_round()

    entry = atlas.query_atlas("liver", "healthy", "adult")
    assert entry is not None
    assert entry.sample_size == 370
    assert 0.8 < entry.phi_c_mean < 0.85
