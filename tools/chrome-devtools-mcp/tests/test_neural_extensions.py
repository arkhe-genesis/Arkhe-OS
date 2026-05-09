import torch
import numpy as np
from arkhe_os.rendering.mcv_neural_extensions import EnhancedCoherenceMonitor
from arkhe_os.ai.coherence_cnn_classifier import CoherenceState
from arkhe_os.generative.conditional_coherence_generator import GenerationCondition

def test_full_neural_pipeline():
    monitor = EnhancedCoherenceMonitor(
        resolution=(256, 256),
        device='cpu',
        enable_classification=True,
        enable_generation=True,
        enable_bci=True,
        bci_protocol='simulator'
    )
    test_time = 13.8
    test_phi_c = 0.87
    test_condition = GenerationCondition(
        current_phi_c=test_phi_c,
        target_phi_c=0.92,
        time_horizon_gyr=2.0,
        zone_context="Interior",
        mission_criticality=0.85,
        external_perturbations={'solar_flare': 0.3},
        creativity_temperature=0.6
    )
    result = monitor.analyze_and_perceive(
        time=test_time,
        phi_c_value=test_phi_c,
        condition=test_condition,
        perceive_via_bci=True
    )
    assert result['frame_rendered'], "Frame não renderizado"
    assert 'classification' in result, "Classificação não executada"
    return True

if __name__ == "__main__":
    test_full_neural_pipeline()
    print("ALL TESTS PASSED")
