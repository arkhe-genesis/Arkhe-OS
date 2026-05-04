# scripts/prepare_combined_mpw_submission.py
"""
Prepare combined MPW submission: Vortex Matrix + OR Lattice
Single shuttle submission for integrated ARKHE prototype.
"""
import shutil
import json
from pathlib import Path
from datetime import datetime
from core.or_lattice_specs import OR_SPEC

def prepare_combined_mpw_package(
    vortex_gds: str = 'layouts/vortex_array_v340.2.gds',
    or_lattice_gds: str = 'layouts/or_lattice_v359.gds',
    output_dir: str = 'mpw_submission/arkhe_combined_v359',
    foundry: str = 'AIM_Photonics'
):
    """Prepare complete MPW submission package with both components."""
    print(f"📦 Preparing combined MPW package: {output_dir}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Copy GDSII files
    shutil.copy2(vortex_gds, output_path / 'vortex_matrix.gds')
    shutil.copy2(or_lattice_gds, output_path / 'or_lattice.gds')

    # Create combined specification document
    spec_doc = {
        'arkhe_version': 'v∞.359.1',
        'submission_date': datetime.now().isoformat(),
        'foundry': foundry,
        'components': {
            'vortex_matrix': {
                'description': '10×10 μm micro-vortex array for spectral sensing',
                'gds_file': 'vortex_matrix.gds',
                'material': 'PMMA',
                'feature_size_min': '300 nm',
                'total_area': '10×10 μm²'
            },
            'or_lattice': {
                'description': 'Operational Relativity torsional lattice (12 layers × 64 crystals)',
                'gds_file': 'or_lattice.gds',
                'material': 'PEEK or polymer alternative',
                'feature_size_min': '100 μm',
                'total_dimensions': f'{OR_SPEC.max_radius*2:.1f} mm × {OR_SPEC.total_height:.1f} mm',
                'key_parameters': {
                    'lambda_delta': OR_SPEC.lambda_delta,
                    'torsion_period_layers': OR_SPEC.torsion_period_layers,
                    'prime_field': OR_SPEC.prime_field,
                    'strut_weights': {'H': OR_SPEC.weight_H, 'V': OR_SPEC.weight_V, 'D': OR_SPEC.weight_D}
                }
            }
        },
        'integration_notes': [
            'Vortex matrix to be coupled to crystal nodes on OR lattice via evanescent waveguide',
            'Alignment markers on both components enable post-fabrication registration',
            'Material compatibility: PMMA vortex on PEEK lattice requires adhesive bonding or monolithic polymer option'
        ],
        'testing_protocol': {
            'optical': 'Spectral response validation via tunable laser + spectrometer',
            'mechanical': 'Torsional response validation via FEA correlation (CAPTURE regime)',
            'integrated': 'Closed-loop homeostasis validation with ArkheVision feedback'
        }
    }

    with open(output_path / 'combined_specification.json', 'w') as f:
        json.dump(spec_doc, f, indent=2)

    # Create README for foundry
    readme = f"""# ARKHE Combined MPW Submission v∞.359.1

## Components
1. **Vortex Matrix** (`vortex_matrix.gds`): 10×10 μm micro-vortex array for spectral sensing
2. **OR Lattice** (`or_lattice.gds`): 12-layer torsional lattice with 768 crystal nodes

## Fabrication Notes
- Vortex matrix: PMMA, femtosecond laser writing, Δn=0.02-0.08
- OR lattice: PEEK (or polymer alternative), minimum feature 100 μm
- Alignment: Use corner markers (layer 30) for post-fab registration

## Key Parameters
- λΔ = {OR_SPEC.lambda_delta:.4f} rad/layer (torsion rate)
- Torsion period = {OR_SPEC.torsion_period_layers:.2f} layers
- F181 modular arithmetic for phase encoding
- Strut weights: H={OR_SPEC.weight_H:.3f}, V={OR_SPEC.weight_V:.3f}, D={OR_SPEC.weight_D:.3f}

## Testing
1. Optical: Measure spectral response of vortex matrix (400-1550 nm)
2. Mechanical: Validate torsional distribution matches CAPTURE regime prediction
3. Integrated: Closed-loop homeostasis with ArkheVision feedback

## Contact
Rafael Oliveira | ORCID: 0009-0005-2697-4668
"""

    with open(output_path / 'README.md', 'w') as f:
        f.write(readme)

    # Copy supporting files
    for file in ['core/or_lattice_specs.py', 'scripts/validate_or_lattice_drc.py']:
        src = Path(file)
        if src.exists():
            dst = output_path / 'scripts' / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    print(f"✓ Combined MPW package prepared: {output_path}")
    print(f"✓ Files included:")
    for f in output_path.rglob('*'):
        if f.is_file():
            print(f"   • {f.relative_to(output_path)}")

    return output_path

if __name__ == '__main__':
    # Check if GDSII files exist
    vortex_gds = 'layouts/vortex_array_v340.2.gds'
    or_gds = 'layouts/or_lattice_v359.gds'

    if Path(vortex_gds).exists() and Path(or_gds).exists():
        package_path = prepare_combined_mpw_package(vortex_gds, or_gds)
        print(f"\n🎯 Combined MPW package ready for submission: {package_path}")
        print(f"🔗 Next: Submit to {OR_SPEC.mpw_foundry} before {OR_SPEC.shuttle_deadline}")
    else:
        print(f"⚠️  Missing GDSII files:")
        if not Path(vortex_gds).exists():
            print(f"   • {vortex_gds}")
        if not Path(or_gds).exists():
            print(f"   • {or_gds}")
        print(f"   Generate GDSII files first using generate_or_lattice_gdsii.py")
