import trimesh
import numpy as np
import os
import argparse

def generate_gsu_lattice_export(output_path='results/gsu_torsion_lattice.stl'):
    LAMBDA_DELTA = 3722.0 / 2705.0
    LAYERS = 12
    SEGMENTS = 16
    M_REF = 5
    spacingY = 2.5
    startY = -((LAYERS - 1) * spacingY) / 2

    points = []

    # 1. Generate Coordinates
    for l in range(LAYERS):
        phaseShift = ((l * M_REF) % 181) / 181.0 * np.pi * 2.0
        radius = 9.0 + 2.0 * np.sin(l * LAMBDA_DELTA)
        y = startY + (l * spacingY)

        layer_points = []
        for s in range(SEGMENTS):
            theta = (s / SEGMENTS) * np.pi * 2.0 + phaseShift
            x = radius * np.cos(theta)
            z = radius * np.sin(theta)
            layer_points.append([x, y, z])
        points.append(layer_points)

    strut_radius = 0.12
    meshes = []

    def create_cylinder_between(p1, p2, radius=0.12):
        vector = p2 - p1
        length = np.linalg.norm(vector)
        if length < 1e-6:
            return None

        cylinder = trimesh.creation.cylinder(radius=radius, height=length)
        z_axis = np.array([0, 0, 1])
        dir_vector = vector / length

        cross_prod = np.cross(z_axis, dir_vector)
        cross_norm = np.linalg.norm(cross_prod)
        if cross_norm > 1e-6:
            axis = cross_prod / cross_norm
            angle = np.arccos(np.dot(z_axis, dir_vector))
            matrix = trimesh.transformations.rotation_matrix(angle, axis)
        else:
            if np.dot(z_axis, dir_vector) < 0:
                matrix = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
            else:
                matrix = np.eye(4)

        midpoint = (p1 + p2) / 2.0
        translation = trimesh.transformations.translation_matrix(midpoint)

        matrix = np.dot(translation, matrix)
        cylinder.apply_transform(matrix)
        return cylinder

    # 2. Define Structural Connections (Struts)
    for l in range(LAYERS):
        for s in range(SEGMENTS):
            current = np.array(points[l][s])
            nextInRing = np.array(points[l][(s + 1) % SEGMENTS])

            cyl = create_cylinder_between(current, nextInRing, strut_radius)
            if cyl: meshes.append(cyl)

            if l < LAYERS - 1:
                above = np.array(points[l + 1][s])
                aboveNext = np.array(points[l + 1][(s + 1) % SEGMENTS])

                cyl1 = create_cylinder_between(current, above, strut_radius)
                cyl2 = create_cylinder_between(current, aboveNext, strut_radius)
                if cyl1: meshes.append(cyl1)
                if cyl2: meshes.append(cyl2)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined = trimesh.util.concatenate(meshes)
    combined.export(output_path)
    print(f"Exported lattice to {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, default='results/gsu_torsion_lattice.stl')
    args = parser.parse_args()
    generate_gsu_lattice_export(args.output)
