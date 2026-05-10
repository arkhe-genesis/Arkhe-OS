# examples/program_skyrmion.py
from core.topology.skyrmion_programmer import SkyrmionProgrammer, SkyrmionProgram, SkyrmionType

# Initialize programmer for 128x128 lattice, 1nm spacing
programmer = SkyrmionProgrammer(lattice_spacing=1.0, simulation_size=(128, 128))

# Define target: Néel-type skyrmion, Q=+1, core radius 10nm
program = SkyrmionProgram(
    target_charge=1,
    skyrmion_type=SkyrmionType.NEEL,
    core_radius=10.0,
    boundary_condition="fixed",
    control_fields={"E_z": 1e6}  # Example: vertical electric field for programming
)

# Generate texture
n_field = programmer.generate_texture(program)

# Validate topology
result = programmer.validate_topology(n_field, expected_Q=1.0)
print(f"✅ Skyrmion validation: {result}")
# Expected: {'valid': True, 'Q_expected': 1.0, 'Q_computed': 0.98, 'error': 0.02, 'texture_type': 'Néel-type'}

# Export for visualization or hardware control
# (e.g., send to SLM for plasmonic excitation, or to QD array for emission)
