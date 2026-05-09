import pytest
import sys
import os

# Add the project root and the new module directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../cathedral-neuro/src')))

from cathedral_neuro.bioscience.human_embedded_system import HumanEmbeddedSystem
from cathedral_neuro.bioscience.soul_transcription import SoulTranscripter, SoulInstaller

def test_human_embedded_system_feedback():
    hes = HumanEmbeddedSystem(initial_soul=1.0, initial_mind=0.8, initial_body=0.9)
    hes.process_feedback_cycle()
    status = hes.get_system_status()

    assert status["soul_energy_flux"] > 0
    assert status["mind_coherence_index"] <= 1.0
    assert status["body_homeostasis_level"] <= 1.0
    assert len(hes.feedback_history) == 1

def test_soul_transcription_and_installation():
    citizen_did = "did:arkhe:test-citizen"
    transcripter = SoulTranscripter(citizen_did)

    # Capture
    transcripter.capture_photons(duration_ms=100)
    assert len(transcripter.buffer) == 100

    # Seal
    artifact = transcripter.verify_and_seal()
    assert artifact.origin_did == citizen_did
    assert artifact.artifact_id.startswith("SOUL-")

    # Install
    substrate = "Arkhe-Simulation-Core"
    plan = SoulInstaller.prepare_installation(artifact, substrate)
    assert plan["status"] == "READY_FOR_INSTALL"
    assert plan["artifact_id"] == artifact.artifact_id

    result = SoulInstaller.execute_installation(plan)
    assert result["result"] == "SUCCESS"
    assert result["coherence_stabilized"] is True

def test_immortality_simulation():
    hes = HumanEmbeddedSystem(initial_soul=0.5, initial_mind=0.5, initial_body=0.5)
    final_status = hes.simulate_immortality_stabilization(cycles=10)

    # Coherence should improve due to positive external stimulus in simulation
    assert final_status["overall_coherence"] > 0.5
