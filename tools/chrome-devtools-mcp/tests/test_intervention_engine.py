from core.integration.tdcs.intervention_engine import compute_intervention_parameters, InterventionCommand
from core.lattice.meta_lattice import MultiModalPhaseAlignedStateVector

def test_intervention_engine():
    mmpasv = MultiModalPhaseAlignedStateVector(collaborative_phase=1.0, participant_phases={"p1": 1.0})

    # Test safety override
    cmd = compute_intervention_parameters(mmpasv, {"gamma_spike": True}, 0.5, 0.05, 1.0)
    assert cmd.state == "EMERGENCY_CUTOFF"

    # Test mercy gap rigidity
    cmd = compute_intervention_parameters(mmpasv, {}, 0.5, 0.02, 1.0)
    assert cmd.state == "PAUSED"

    # Test mercy gap scatter
    cmd = compute_intervention_parameters(mmpasv, {}, 0.5, 0.12, 1.0)
    assert cmd.state == "PAUSED"

    # Test permissive dissolution (0.4 <= pdi < 0.85)
    cmd = compute_intervention_parameters(mmpasv, {}, 0.5, 0.05, 1.0)
    assert cmd.state == "ACTIVE"
    assert cmd.ramp == 0.05

    # Test threshold / seal support
    cmd = compute_intervention_parameters(mmpasv, {}, 0.9, 0.05, 1.0)
    assert cmd.state == "SEAL_SUPPORT"
