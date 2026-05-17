import pytest
from arkhe_os.clinical_trial.clinical_trial_simulator import ClinicalTrialSimulator, CohortDefinition, InterventionDefinition, TrialPhase
from arkhe_os.patient_vault.patient_data_vault import PatientDataVault as RedoxDataVault
from arkhe_os.cross_species.coherence_mapper import CrossSpeciesMapper

def test_clinical_trial_simulator():
    class MetaLearner:
        def calibrate_trial_predictions(self, raw_results, historical_data):
            return raw_results

    meta_learner = MetaLearner()
    simulator = ClinicalTrialSimulator("dummy_path", meta_learner, "dummy_db_path")

    cohort = CohortDefinition(
        cohort_id="test_cohort",
        inclusion_criteria={"age": [40, 70]},
        exclusion_criteria={},
        sample_size=2
    )

    intervention = InterventionDefinition(
        intervention_id="intervention_1",
        name="test_intervention",
        type="small_molecule",
        mechanism="test_mech",
        dosing_regimen={"dose_mg": 100},
        target_redox_pairs=["NAD+/NADH"],
        expected_effect_profile={"NAD+/NADH": 5.0}
    )

    result = simulator.simulate_trial(cohort, intervention, TrialPhase.PHASE_II, n_virtual_patients=2)

    assert result.n_simulated_patients == 2
    assert "mean_delta_phi_c" in result.efficacy
    assert result.phase == TrialPhase.PHASE_II

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
