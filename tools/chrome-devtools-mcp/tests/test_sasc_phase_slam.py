import pytest
import numpy as np
from src.physics.sasc_phase_slam import Heaviside3DScene, MarconiASICDesigner, PhaseCoherenceSLAM
from src.physics.sasc_em_engine import EMSpecification

def test_phase_slam_prediction():
    engine = Heaviside3DScene()
    geometry = np.random.rand(64, 64)
    result = engine.predict_scene(geometry, 60e9)

    assert "phase_reflection" in result
    assert "lambda2_field" in result
    assert result["frequency"] == 60e9

def test_asic_designer():
    engine = Heaviside3DScene()
    designer = MarconiASICDesigner(engine)
    spec = EMSpecification(frequency_range=(57e9, 64e9))

    design = designer.design_radar_array(spec)
    assert design["aperture_synthesis"] == "Sierpinski 4x4"
    assert design["layout"].shape == (64, 64)

def test_tzinor_antenna_design():
    engine = Heaviside3DScene()
    designer = MarconiASICDesigner(engine)
    spec = EMSpecification(frequency_range=(76e9, 81e9))

    design = designer.design_tzinor_array(spec)
    assert design["type"] == "Phased Array 8x8"
    assert design["range_estimate_km"] == 5.0

def test_slam_update():
    engine = Heaviside3DScene()
    slam = PhaseCoherenceSLAM(engine)
    geometry = np.zeros((64, 64))
    geometry[32, 32] = 1.0

    update = slam.update(geometry, 60e9)
    assert "local_coherence" in update
    assert "new_nodes_count" in update
    assert len(slam.state.graph_nodes) > 0
