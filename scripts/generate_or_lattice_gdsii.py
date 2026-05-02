#!/usr/bin/env python3
# scripts/generate_or_lattice_gdsii.py
"""
Generate GDSII layout for Operational Relativity torsional lattice.
Compatible with PEEK 3D printing or polymer MPW submission.
"""
import gdspy
import numpy as np
from pathlib import Path
from core.or_lattice_specs import OR_SPEC

def generate_ring_pattern(radius: float, n_nodes: int, layer_num: int,
                         spec: OR_SPEC) -> list[tuple[float, float, float]]:
    """Generate node positions for a single ring at given layer."""
    nodes = []
    base_angle = spec.lambda_delta * layer_num  # Torsion offset per layer

    for i in range(n_nodes):
        # Position on ring with modular phase encoding
        angle = (2 * np.pi * i / n_nodes) + base_angle
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = layer_num * spec.ring_spacing  # Vertical position
        nodes.append((x, y, z))

    return nodes

def generate_strut_gdsii(p1: tuple[float, float, float], p2: tuple[float, float, float],
                        thickness: float, layer: int) -> gdspy.Polygon:
    """Generate GDSII polygon for a strut between two nodes."""
    # 2D projection for GDSII (Z encoded in layer number or metadata)
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]

    # Compute perpendicular offset for strut thickness
    dx, dy = x2 - x1, y2 - y1
    length = np.sqrt(dx**2 + dy**2)
    if length < 1e-9:
        return None

    # Unit perpendicular vector
    nx, ny = -dy / length, dx / length
    offset = thickness / 2

    # Four corners of rectangular strut
    corners = [
        (x1 + nx * offset, y1 + ny * offset),
        (x1 - nx * offset, y1 - ny * offset),
        (x2 - nx * offset, y2 - ny * offset),
        (x2 + nx * offset, y2 + ny * offset),
    ]

    return gdspy.Polygon(corners, layer=layer)

def generate_or_lattice_gdsii(output_path: str = 'layouts/or_lattice_v359.gds'):
    """Generate complete GDSII layout for OR torsional lattice."""
    print(f"🔧 Generating OR Lattice GDSII: {output_path}")

    spec = OR_SPEC
    lib = gdspy.GdsLibrary(unit=1e-6, precision=1e-9)  # Units: μm
    cell = lib.new_cell('ARKHE_OR_LATTICE_v359')

    # Layer assignments for different strut types
    LAYER_H = 10  # Horizontal (intra-ring)
    LAYER_V = 11  # Vertical (inter-ring)
    LAYER_D = 12  # Diagonal (torsion cross)
    LAYER_NODE = 20  # Crystal mounting nodes
    LAYER_MARKER = 30  # Alignment markers

    # Generate nodes for all layers
    all_nodes = []
    for layer_num in range(spec.n_layers):
        radius = spec.ring_radius_base  # Could add tapering if needed
        nodes = generate_ring_pattern(radius, spec.crystals_per_ring, layer_num, spec)
        all_nodes.append(nodes)

        # Add node markers (crystal mounting points)
        for x, y, z in nodes:
            # Circular node for crystal mounting
            circle = gdspy.Round((x*1e6, y*1e6),
                               spec.crystal_node_size*1e6/2 - 10,  # Slight undersize for fit
                               spec.crystal_node_size*1e6/2,
                               number_of_points=32,
                               layer=LAYER_NODE)
            cell.add(circle)

    # Generate struts
    strut_count = {'H': 0, 'V': 0, 'D': 0}

    for layer_num in range(spec.n_layers):
        nodes = all_nodes[layer_num]

        # H-type: Horizontal struts within same ring
        for i in range(len(nodes)):
            p1 = nodes[i]
            p2 = nodes[(i + 1) % len(nodes)]  # Wrap around ring
            strut = generate_strut_gdsii(p1, p2, spec.strut_thickness, LAYER_H)
            if strut:
                cell.add(strut)
                strut_count['H'] += 1

        # V-type and D-type: Inter-ring connections (except last layer)
        if layer_num < spec.n_layers - 1:
            next_nodes = all_nodes[layer_num + 1]
            for i in range(len(nodes)):
                p1 = nodes[i]

                # V-type: Direct vertical connection (same angular position)
                p2_v = next_nodes[i]
                strut_v = generate_strut_gdsii(p1, p2_v, spec.strut_thickness, LAYER_V)
                if strut_v:
                    cell.add(strut_v)
                    strut_count['V'] += 1

                # D-type: Diagonal torsion cross (offset by torsion period fraction)
                offset_idx = int(spec.crystals_per_ring / spec.torsion_period_layers) % spec.crystals_per_ring
                p2_d = next_nodes[(i + offset_idx) % len(next_nodes)]
                strut_d = generate_strut_gdsii(p1, p2_d, spec.strut_thickness, LAYER_D)
                if strut_d:
                    cell.add(strut_d)
                    strut_count['D'] += 1

    # Add alignment markers at corners
    marker_size = 100  # μm
    for corner in [(-10000, -10000), (10000, -10000), (-10000, 10000), (10000, 10000)]:
        cell.add(gdspy.Rectangle(
            (corner[0], corner[1]),
            (corner[0] + marker_size, corner[1] + marker_size),
            layer=LAYER_MARKER
        ))

    # Add metadata as text in GDSII (for fabrication notes)
    metadata_text = f"ARKHE OR LATTICE v359\nλΔ={spec.lambda_delta:.4f} rad/layer\nPeriod={spec.torsion_period_layers:.2f} layers\nF181 modular\nH={spec.weight_H:.3f} V={spec.weight_V:.3f} D={spec.weight_D:.3f}"
    cell.add(gdspy.Text(metadata_text, 50, (0, -12000), layer=LAYER_MARKER))

    # Save GDSII
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(output_path)

    print(f"✓ GDSII saved: {output_path}")
    print(f"✓ Strut counts: H={strut_count['H']}, V={strut_count['V']}, D={strut_count['D']}")
    print(f"✓ Total nodes: {spec.total_crystals}")

    return output_path, strut_count

if __name__ == '__main__':
    gds_path, counts = generate_or_lattice_gdsii()
    print(f"\n🔗 Ready for MPW submission: {gds_path}")
