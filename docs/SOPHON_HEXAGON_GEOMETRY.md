# Sophon Hexagon V2 Geometry

This document outlines the extension of the Substrate 90 visualizer from a pure Hexagon to include arbitrary Sacred Polyhedra (Tetrahedron, Cuboctahedron, Icosahedron).

## Bidirectional Controls

The Bidirectional UI component (`core/visualization/bidirectional_ui.py`) exposes:
1. Wave Amplitude Balance (Shader Only)
2. Mode Coupling Strength (Shader Only)
3. Coherence Alert Threshold (Shader + Network Threshold)
4. Delivery Rate Threshold (Network Only)

## Sacred Polyhedra Extension

`core/geometry/sacred_polyhedra.py` provides classes to generate configurations for:
- Tetrahedron: 4 coherent wave modes
- Hexagon: 6 coherent wave modes
- Cuboctahedron: 12 coherent wave modes
- Icosahedron: 20 coherent wave modes
