import pytest
import numpy as np
from arkhe_moire.materials_2d_db import MATERIALS_2D_CATALOG, MaterialClass
from arkhe_moire.spin_valley_simulator import SpinValleySimulator, SpinValleyState, MaterialsMapper

def test_materials_db():
    assert "WSe2" in MATERIALS_2D_CATALOG
    assert "CrI3" in MATERIALS_2D_CATALOG
    assert "BaTiO3_2D" in MATERIALS_2D_CATALOG

    cri3 = MATERIALS_2D_CATALOG["CrI3"]
    assert cri3.material_class == MaterialClass.MAGNETIC_2D

    batio3 = MATERIALS_2D_CATALOG["BaTiO3_2D"]
    assert batio3.material_class == MaterialClass.PEROVSKITE

def test_materials_mapper():
    mapper = MaterialsMapper()
    best_spin = mapper.find_best_for_application("spintronics", min_phi_c=0.90)
    assert len(best_spin) > 0
    names = [x[0] for x in best_spin]
    assert "Chromium Triiodide" in names

def test_spin_valley_simulator():
    wse2 = MATERIALS_2D_CATALOG["WSe2"]
    sim = SpinValleySimulator(wse2, angle_degrees=1.1)

    # Check dispersion
    k_points = np.array([[0, 0], [0.5, 0.5]])
    dispersion = sim.compute_spin_valley_dispersion(k_points)
    assert dispersion.shape == (2, 4)

    # Check map
    cmap = sim.generate_coherence_map((1.0, 10.0), n_points=5)
    assert cmap["material"] == "Tungsten Diselenide"
    assert len(cmap["angles"]) == 5
    assert len(cmap["temperatures"]) == 5

def test_qnc_optimization():
    cri3 = MATERIALS_2D_CATALOG["CrI3"]
    sim = SpinValleySimulator(cri3, angle_degrees=1.5)

    angles = sim.optimize_critical_angles_qnc()
    assert isinstance(angles, list)
    assert len(angles) > 0
    # ensure it finds roughly 1.5 and 4.2
    found_1_5 = any(abs(a - 1.5) < 0.2 for a in angles)
    assert found_1_5
