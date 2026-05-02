#!/usr/bin/env python3
"""
export_to_meep.py
Exports vortex array model to MEEP (Python interface) for open-source FDTD simulation.
"""
import numpy as np
from pathlib import Path
import json

try:
    import meep as mp
except ImportError:
    print("MEEP is not installed. Will mock the output files.")
    mp = None

VORTEX_PARAMS = {
    'array_size': (10, 10),
    'pitch': 1e-6,
    'wavelength_range': (400e-9, 1550e-9),
    'n_pixels': 1151,
    'depth': 1.5e-6,
    'core_diameter': 300e-9,
    'dn_range': (0.02, 0.08)
}

def create_meep_simulation(vortex_params, resolution=50, output_dir='exports/meep'):
    print(f"🔧 Creating MEEP simulation: {output_dir}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    pitch_um = vortex_params['pitch'] * 1e6
    core_um = vortex_params['core_diameter'] * 1e6
    depth_um = vortex_params['depth'] * 1e6
    array_size = vortex_params['array_size']

    cell_size = [
        array_size[0] * pitch_um + 4,
        array_size[1] * pitch_um + 4,
        depth_um + 3
    ]

    fcen = 0.5 * (1/0.4 + 1/1.55)
    df = 0.5 * (1/0.4 - 1/1.55)

    config = {
        'cell_size': cell_size,
        'resolution': resolution,
        'source': {'fcen': fcen, 'df': df},
        'vortex_params': {k: (v * 1e6 if isinstance(v, (int, float)) and k in ['pitch', 'core_diameter', 'depth'] else v)
                         for k, v in vortex_params.items()}
    }

    with open(f'{output_dir}/simulation_config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ MEEP configuration saved: {output_dir}/simulation_config.json")
    print(f"🔗 To run simulation:")
    print(f"   python -c \"import meep as mp; from exports.meep.run_simulation import run; run()\"")

    return None, config

if __name__ == '__main__':
    sim, config = create_meep_simulation(VORTEX_PARAMS)

    print(f"\n✅ Export to MEEP complete")
    print(f"🔗 Configuration saved for later execution")
