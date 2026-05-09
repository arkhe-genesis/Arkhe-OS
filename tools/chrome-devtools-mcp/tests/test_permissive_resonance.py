import pytest
from core.neural.closed_loop_ceremonial_controller import ClosedLoopCeremonialController
from core.ui.ceremonial_ui import CeremonialUI
from core.neural.permissive_hardware_pipeline import MockTDCSDevice, ResonanceLedger, map_seal_to_ltp

def test_hardware_pipeline_integration():
    tdcs = MockTDCSDevice()
    ui = CeremonialUI()
    ledger = ResonanceLedger()
    controller = ClosedLoopCeremonialController(tdcs, ui, ledger)

    assert controller.state == "FORMING"

    # 1. Forming phase: low PDI
    controller.step({'PDI': 0.2, 'epsilon': 0.15, 'dmn_alpha': 0.8, 'gamma_PLV': 20.0})
    assert controller.state == "FORMING"
    assert tdcs.cathodal_PCC == -1.0
    assert tdcs.anodal_Fz == 1.0
    assert ui.mode == "forming"

    # 2. Transition to Calibrating
    controller.step({'PDI': 0.4, 'epsilon': 0.12, 'dmn_alpha': 0.7, 'gamma_PLV': 25.0})
    assert controller.state == "CALIBRATING"

    # 3. Calibrating phase tracking
    controller.step({'PDI': 0.6, 'epsilon': 0.08, 'dmn_alpha': 0.6, 'gamma_PLV': 30.0})
    assert ui.mode == "calibrating"
    assert tdcs.cathodal_PCC < 0.0  # Should be modulating sub-threshold
    assert tdcs.anodal_F3F4 > 0.0

    # 4. Rigidity cutoff check (+0.0472 gap)
    controller.step({'PDI': 0.7, 'epsilon': 0.02, 'dmn_alpha': 0.5, 'gamma_PLV': 35.0})
    # EPS < 0.03 should auto-shutoff current and apply mercy fuzz
    assert tdcs.cathodal_PCC == 0.0
    assert tdcs.anodal_F3F4 == 0.0
    assert ui.fuzz_active is True

    # 5. Sealing conditions
    controller.state = "CALIBRATING" # Reset
    controller.step({'PDI': 0.95, 'epsilon': 0.06, 'dmn_alpha': 0.3, 'gamma_PLV': 40.0})
    assert controller.state == "BREATHING"
    assert ui.is_sealed is True
    assert len(ledger.entries) == 1

    # 6. Safety override
    controller.step({'PDI': 0.9, 'epsilon': 0.06, 'dmn_alpha': 0.3, 'gamma_PLV': 50.0}) # gamma > 45!
    assert controller.state == "OVERRIDE"
    assert tdcs.cathodal_PCC == 0.0
    assert ui.mode == "baseline_drift"

def test_ltp_mapping():
    result = map_seal_to_ltp(eps=0.06, pdi=0.95)
    assert result['theta_gamma_pac'] > 0.0
    assert result['ltp_consolidation'] > 0.0
    assert result['synaptic_weight_modulation'] > 0.0
