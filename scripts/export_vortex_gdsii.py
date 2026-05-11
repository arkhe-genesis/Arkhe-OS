#!/usr/bin/env python3
"""
export_vortex_gdsii.py
Exports micro-vortex array layout to GDSII format for lithography.
"""
import gdspy
import numpy as np
from pathlib import Path

# Parâmetros da matriz (consistentes com simulação)
VORTEX_PARAMS = {
    'pitch': 1e-6,              # 1 μm
    'core_diameter': 300e-9,    # 300 nm
    'array_size': (10, 10),
    'layer_vortex': 1,          # GDSII layer for vortex structures
    'layer_boundary': 2,        # GDSII layer for alignment marks
}

def generate_vortex_polygon(x_center, y_center, core_d, n_segments=32):
    """Gera polígono aproximando perfil de vórtice para litografia."""
    # Perfil radial: anel com fase azimutal
    # Para litografia: aproximamos como anel com modulação de espessura
    angles = np.linspace(0, 2*np.pi, n_segments, endpoint=False)

    # Raio interno/externo do anel
    r_inner = core_d * 0.3
    r_outer = core_d * 0.7

    # Modulação azimutal simulando carga topológica m=1
    # Espessura varia como: t(θ) = t₀ + Δt·cos(θ)
    points = []
    for angle in angles:
        # Ponto interno
        r_in = r_inner
        x_in = x_center + r_in * np.cos(angle)
        y_in = y_center + r_in * np.sin(angle)
        points.append((x_in*1e6, y_in*1e6))  # Converter para μm para GDSII

        # Ponto externo com modulação
        r_out = r_outer * (1 + 0.1 * np.cos(angle))  # ±10% modulação
        x_out = x_center + r_out * np.cos(angle)
        y_out = y_center + r_out * np.sin(angle)
        points.append((x_out*1e6, y_out*1e6))

    return points

def create_vortex_array_gdsii(output_path='layouts/vortex_array_v340.2.gds'):
    """Cria layout GDSII da matriz de micro-vórtices."""
    print(f"🔧 Generating GDSII layout: {output_path}")

    # Inicializar biblioteca GDSII
    lib = gdspy.GdsLibrary(unit=1e-6, precision=1e-9)  # Units: μm, precision: nm
    cell = lib.new_cell('ARKHE_VORTEX_ARRAY_v340.2')

    # Gerar matriz de vórtices
    nx, ny = VORTEX_PARAMS['array_size']
    pitch = VORTEX_PARAMS['pitch'] * 1e6  # Converter para μm

    for i in range(nx):
        for j in range(ny):
            x_center = (i - nx/2 + 0.5) * pitch
            y_center = (j - ny/2 + 0.5) * pitch

            # Adicionar polígono do vórtice
            polygon = generate_vortex_polygon(
                x_center*1e-6, y_center*1e-6,  # Converter de volta para metros
                VORTEX_PARAMS['core_diameter']
            )
            cell.add(gdspy.Polygon(polygon, layer=VORTEX_PARAMS['layer_vortex']))

    # Adicionar marcas de alinhamento nos cantos
    mark_size = 5.0  # μm
    for corner in [(-25, -25), (25, -25), (-25, 25), (25, 25)]:
        cell.add(gdspy.Rectangle(
            (corner[0], corner[1]),
            (corner[0] + mark_size, corner[1] + mark_size),
            layer=VORTEX_PARAMS['layer_boundary']
        ))

    # Salvar arquivo GDSII
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(output_path)
    print(f"✓ GDSII layout saved: {output_path}")

    return output_path

if __name__ == '__main__':
    gds_path = create_vortex_array_gdsii()
    print(f"🔗 Ready for lithography: {gds_path}")
