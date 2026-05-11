# core/topology/README.md — NUMERICAL LIMITATIONS
"""
## Numerical Limitations of Topological Charge Computation

The discrete lattice formula for skyrmion charge has finite-grid errors:

| Grid Resolution | Typical |Q-1| | Recommended Use |
|----------------|-------------------|-----------------|
| 128×128        | < 0.04            | Prototyping     |
| 256×256        | < 0.02            | Validation      |
| 512×512        | < 0.01            | Production      |
| 1024×1024      | < 0.005           | High-precision  |

### Noise Robustness

Topological protection is asymptotic; finite discretization + noise yields:

| Amplitude Noise | ΔQ (typical) | Viability |
|----------------|--------------|-----------|
| ≤ 5%           | < 0.03       | ✅ Excellent |
| 5-10%          | 0.03-0.15    | ⚠️ Acceptable with averaging |
| 10-20%         | 0.15-0.50    | ❌ Marginal; requires filtering |
| > 20%          | > 0.50       | ❌ Unreliable; topological identification fails |

### API Guarantees

- `compute_skyrmion_charge()`: Returns Q with |Q - Q_true| < 0.15 for BP skyrmions on 128×128+ grids
- `generate_texture_bp()`: Produces textures with |Q - target| < 0.15 after calibration
- `classify_skyrmion_type()`: Correct for noise ≤ 5%; may misclassify at higher noise

For experimental work, always:
1. Use grid ≥ 256×256 for Q computation
2. Apply spatial averaging to measured n(x,y) before Q calculation
3. Report numerical tolerance alongside Q values
"""
