import pytest
import numpy as np
from datetime import datetime, timezone
from skills import ArkheMaxTokiIntegration, CellularState, MaxTokiAdapter

def test_maxtoki_nv_to_transcriptome():
    adapter = MaxTokiAdapter()
    nv_data = np.random.normal(0.5, 0.1, 168)
    transcriptome = adapter.nv_to_transcriptome(nv_data, 'cochlea')
    assert transcriptome.shape == (20271,)
    assert np.isclose(transcriptome.mean(), 0.0, atol=1e-7)
    assert np.isclose(transcriptome.std(), 1.0, atol=1e-7)

def test_maxtoki_predict_aging_trajectory():
    adapter = MaxTokiAdapter()
    current_state = CellularState(
        timestamp=datetime.now(),
        lambda_coherence=0.48,
        transcriptome_vector=np.zeros(20271),
        biological_age=30.0,
        tissue_type='cochlea'
    )
    trajectory = adapter.predict_aging_trajectory(current_state, interventions=["silence_P4HA1"])
    assert len(trajectory.predicted_states) == 6
    assert "silence_P4HA1" in trajectory.intervention_effects
    assert trajectory.intervention_effects["silence_P4HA1"] == -5.0

def test_maxtoki_predict_otof_recovery():
    adapter = MaxTokiAdapter()
    current_state = CellularState(
        timestamp=datetime.now(),
        lambda_coherence=0.45,
        transcriptome_vector=np.zeros(20271),
        biological_age=5.0,
        tissue_type='cochlea'
    )
    prediction = adapter.predict_otof_recovery(current_state)
    assert 'recovery_curve' in prediction
    assert len(prediction['recovery_curve']) == 6
    assert prediction['expected_full_recovery_days'] == 120

def test_maxtoki_screen_patient_eligibility():
    integration = ArkheMaxTokiIntegration()
    # High eligibility case
    patient_nv_data_high = np.random.normal(0.48, 0.01, 168)
    screening_high = integration.screen_patient_eligibility(patient_nv_data_high)
    assert 'eligible' in screening_high
    assert 'eligibility_score' in screening_high

    # Low eligibility case (already high lambda)
    patient_nv_data_low = np.random.normal(0.95, 0.01, 168)
    screening_low = integration.screen_patient_eligibility(patient_nv_data_low)
    assert screening_low['eligibility_score'] < 50.0 # Improvement is small

def test_maxtoki_generate_smart_contract_data():
    integration = ArkheMaxTokiIntegration()
    patient_nv_data = np.random.normal(0.48, 0.05, 168)
    screening = integration.screen_patient_eligibility(patient_nv_data)
    data = integration.generate_smart_contract_data(screening)
    assert 'maxtoki_prediction' in data
    assert 'milestones' in data
    assert len(data['milestones']) == 3
