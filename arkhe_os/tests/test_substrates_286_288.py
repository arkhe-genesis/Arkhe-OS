import pytest
from arkhe_os.simulation.clinical_simulator import InSilicoClinicalTrialSimulator, VirtualPatient
from arkhe_os.therapeutic.intervention_planner import TherapeuticInterventionPlanner
from arkhe_os.therapeutic.meta_learning import MetaTherapeuticLearner
from arkhe_os.crypto.vault.patient_vault import RedoxDataVault
from arkhe_os.therapeutic.cross_species import CrossSpeciesMapper

def test_clinical_trial_simulator():
    planner = TherapeuticInterventionPlanner()
    meta_learner = MetaTherapeuticLearner()
    simulator = InSilicoClinicalTrialSimulator(planner, meta_learner)

    cohort = [
        VirtualPatient(patient_id="p1", baseline_redox_state={}, baseline_phi_c=0.6, demographics={"age": 40}),
        VirtualPatient(patient_id="p2", baseline_redox_state={}, baseline_phi_c=0.5, demographics={"age": 45}),
    ]

    outcomes = simulator.simulate_trial(cohort, "intervention_1")

    assert len(outcomes) == 2
    assert outcomes[0]["patient_id"] == "p1"
    assert "predicted_delta" in outcomes[0]
    assert "simulated_actual_delta" in outcomes[0]
    assert len(meta_learner.history) == 2

def test_patient_vault():
    vault = RedoxDataVault(patient_id="patient_xyz")

    # Store data
    vault.store_data("data_1", {"phi_c": 0.8}, "my_secret_key")

    # Owner retrieval
    retrieved = vault.retrieve_data("data_1", "patient_xyz", "my_secret_key")
    assert retrieved["phi_c"] == 0.8

    # Grant access
    vault.grant_access("data_1", "doctor_abc", "my_secret_key")

    # Doctor retrieval
    doctor_retrieved = vault.retrieve_data("data_1", "doctor_abc", "my_secret_key")
    assert doctor_retrieved["phi_c"] == 0.8

    # Unauthorized entity
    with pytest.raises(PermissionError):
        vault.retrieve_data("data_1", "hacker_123", "my_secret_key")

    # Invalid key
    with pytest.raises(ValueError):
        vault.retrieve_data("data_1", "patient_xyz", "wrong_key")

    audit_trail = vault.get_audit_trail()
    assert len(audit_trail) > 0
    assert audit_trail[0].action == "STORE"

def test_cross_species_mapper():
    mapper = CrossSpeciesMapper()

    # Map mouse to human
    human_phi = mapper.predict_human_efficacy("mouse", 0.1)
    assert human_phi is not None
    assert round(human_phi, 4) == 0.0850 # 0.1 * 0.85

    # Map human to human (identity)
    human_to_human = mapper.map_coherence("human", "human", 0.5)
    assert human_to_human == 0.5

    # Invalid species
    invalid = mapper.map_coherence("alien", "human", 0.5)
    assert invalid is None
