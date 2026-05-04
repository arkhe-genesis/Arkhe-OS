# scripts/fea_ansys_setup.py
"""
FEA Setup for OR Lattice Mechanical Response Validation
Using Ansys Mechanical via PyAnsys/Mapdl
"""
import numpy as np
from pathlib import Path
try:
    from ansys.mapdl.core import launch_mapdl
    ANSYS_AVAILABLE = True
except ImportError:
    ANSYS_AVAILABLE = False
from core.or_lattice_specs import OR_SPEC

def create_or_lattice_ansys_model(spec: OR_SPEC, output_dir: str = 'fea/or_lattice_ansys'):
    """Create Ansys APDL script for OR lattice FEA."""
    print(f"🔧 Creating Ansys FEA setup: {output_dir}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate APDL commands
    apdl_commands = f"""
! ARKHE OR Lattice FEA Setup v∞.359.1
! Operational Relativity torsional lattice mechanical validation
! Material: {spec.material}

/PREP7

! Material properties
MP,EX,1,{spec.youngs_modulus}    ! Young's modulus (Pa)
MP,PRXY,1,{spec.poisson_ratio}   ! Poisson ratio
MP,DENS,1,{spec.density}         ! Density (kg/m³)

! Element type: BEAM188 for strut modeling
ET,1,BEAM188
KEYOPT,1,3,2  ! Cubic shape function for accurate torsion

! Section definition for struts (rectangular cross-section)
SECTYPE,1,BEAM,RECT
SECDATA,{spec.strut_thickness},{spec.strut_thickness}

! Node generation: rings with torsional offset
*DO,layer,0,{spec.n_layers-1}
  radius = {spec.ring_radius_base}
  z_pos = layer * {spec.ring_spacing}
  torsion_offset = {spec.lambda_delta} * layer

  *DO,node_idx,0,{spec.crystals_per_ring-1}
    angle = (2*3.14159*node_idx/{spec.crystals_per_ring}) + torsion_offset
    x_pos = radius * COS(angle)
    y_pos = radius * SIN(angle)

    ! Create node with unique ID
    node_id = layer * {spec.crystals_per_ring} + node_idx + 1
    N,node_id,x_pos,y_pos,z_pos
  *ENDDO
*ENDDO

! Element generation: H-type (horizontal, intra-ring)
*DO,layer,0,{spec.n_layers-1}
  *DO,node_idx,0,{spec.crystals_per_ring-1}
    n1 = layer * {spec.crystals_per_ring} + node_idx + 1
    n2 = layer * {spec.crystals_per_ring} + MOD(node_idx+1,{spec.crystals_per_ring}) + 1
    E,n1,n2
    EMODIF,_,MAT,1,REAL,1,TYPE,1
    ! Apply coupling weight as section property scaling
    EMODIF,_,SECOFFSET,{spec.weight_H}
  *ENDDO
*ENDDO

! Element generation: V-type (vertical, inter-ring)
*DO,layer,0,{spec.n_layers-2}
  *DO,node_idx,0,{spec.crystals_per_ring-1}
    n1 = layer * {spec.crystals_per_ring} + node_idx + 1
    n2 = (layer+1) * {spec.crystals_per_ring} + node_idx + 1
    E,n1,n2
    EMODIF,_,MAT,1,REAL,1,TYPE,1
    EMODIF,_,SECOFFSET,{spec.weight_V}
  *ENDDO
*ENDDO

! Element generation: D-type (diagonal, torsion cross)
offset_idx = INT({spec.crystals_per_ring} / {spec.torsion_period_layers})
*DO,layer,0,{spec.n_layers-2}
  *DO,node_idx,0,{spec.crystals_per_ring-1}
    n1 = layer * {spec.crystals_per_ring} + node_idx + 1
    n2_target = MOD(node_idx + offset_idx, {spec.crystals_per_ring})
    n2 = (layer+1) * {spec.crystals_per_ring} + n2_target + 1
    E,n1,n2
    EMODIF,_,MAT,1,REAL,1,TYPE,1
    EMODIF,_,SECOFFSET,{spec.weight_D}
  *ENDDO
*ENDDO

! Boundary conditions: fix base ring (layer 0)
*DO,node_idx,0,{spec.crystals_per_ring-1}
  n = node_idx + 1
  D,n,ALL,0  ! Fix all DOF at base
*ENDDO

! Apply torsional load at top ring to simulate CAPTURE regime
! Load magnitude derived from predicted coupling strength
torsion_load = 0.1 * {spec.weight_D}  ! Normalized torsional moment
*DO,node_idx,0,{spec.crystals_per_ring-1}
  n = ({spec.n_layers}-1) * {spec.crystals_per_ring} + node_idx + 1
  ! Apply moment about Z-axis (torsion)
  F,n,MZ,torsion_load
*ENDDO

! Solution setup
/SOLU
ANTYPE,STATIC
NLGEOM,ON  ! Large deflection for torsional response
SOLVE
FINISH

! Post-processing: extract torsional displacement distribution
/POST1
! Compute rotation at each node relative to base
*CFOPEN,'torsion_results.txt','TXT'
*VWRITE,'NodeID,Layer,Position,TorsionalRotation(rad)'
(A,/,A)
*DO,layer,0,{spec.n_layers-1}
  *DO,node_idx,0,{spec.crystals_per_ring-1}
    n = layer * {spec.crystals_per_ring} + node_idx + 1
    ! Extract rotational DOF (ROTZ)
    *GET,rot_z,NODE,n,ROT,Z
    *VWRITE,n,layer,node_idx,rot_z
    (I8,I4,I4,F12.6)
  *ENDDO
*ENDDO
*CFCLOSE

! Export deformed shape for visualization
/POST1
PLDISP,2
/GRAPHICS,FULL
EPLOT
"""

    # Save APDL script
    apdl_path = Path(output_dir) / 'or_lattice_analysis.inp'
    with open(apdl_path, 'w') as f:
        f.write(apdl_commands)

    print(f"✓ Ansys APDL script saved: {apdl_path}")
    return apdl_path

def run_ansys_simulation(apdl_path: str, results_dir: str = 'fea/results'):
    """Execute Ansys simulation if available."""
    if not ANSYS_AVAILABLE:
        print("⚠️  Ansys not available — simulation skipped")
        print("   To run: pip install ansys-mapdl-core")
        return None

    Path(results_dir).mkdir(parents=True, exist_ok=True)

    try:
        # Launch MAPDL
        mapdl = launch_mapdl(run_location=results_dir)

        # Load and execute APDL script
        mapdl.input(str(apdl_path))

        # Extract results
        # (Implementation depends on specific Ansys version/API)
        print("✓ Ansys simulation completed")

        mapdl.exit()
        return True

    except Exception as e:
        print(f"⚠️  Ansys simulation error: {e}")
        return False

if __name__ == '__main__':
    apdl_path = create_or_lattice_ansys_model(OR_SPEC)

    if ANSYS_AVAILABLE:
        success = run_ansys_simulation(apdl_path)
        if success:
            print(f"\n✅ FEA simulation complete — results in fea/results/")
    else:
        print(f"\n📋 Ansys setup created — run manually or install ansys-mapdl-core")
