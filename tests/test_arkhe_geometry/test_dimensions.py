import pytest
from arkhe.geometry.dimensions import (
    Point0D, Line1D, Circle2D, Sphere3D, Tesseract4D,
    Hypersphere5D, Hypercube6D, Torus7D, E8Lattice, Pringle9D,
    DimensionalManifold
)

def test_point():
    p = Point0D(1.0)
    assert p.dimension == 0
    assert p.phi_measure() == 0.0

def test_line():
    l = Line1D([0.0, 1.0])
    assert l.dimension == 1
    assert l.phi_measure() == 0.5

def test_circle():
    c = Circle2D()
    assert c.dimension == 2
    assert c.phi_measure() == 0.5
    c.step()
    assert c.current_phase == 1

def test_sphere():
    s = Sphere3D(radius=2.0, psi_field=[0.5, 0.5])
    assert s.dimension == 3
    assert s.phi_measure() == 1.0

def test_manifold():
    m = DimensionalManifold()
    census = m.phi_census()
    assert "0D_Point" in census
    assert "9D_Pringle" in census
    m.evolve()
    assert len(m.line.points) == 2
    anchors = m.anchor_all()
    assert len(anchors) == 10
    assert all(a.startswith("9018.block#") for a in anchors)
