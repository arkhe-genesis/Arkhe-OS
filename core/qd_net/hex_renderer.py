# core/qd_net/hex_renderer.py
"""
ARKHE QD-NET: Hexagonal Mesh Renderer
Visualizes the cluster state topology via Pygfx/WGPU.
"""
import pygfx as gfx
import numpy as np
from wgpu.utils import get_default_device

class HexRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.renderer = gfx.renderers.WgpuRenderer(canvas)
        self.scene = gfx.Scene()
        self.camera = gfx.PerspectiveCamera(50, 16/9)
        self.camera.position.z = 20

        # Visual elements
        self.nodes_group = gfx.Group()
        self.edges_group = gfx.Group()
        self.scene.add(self.nodes_group)
        self.scene.add(self.edges_group)

        self._setup_lights()
        self._create_controller()

    def _setup_lights(self):
        light = gfx.DirectionalLight()
        light.position.set(0, 0, 10)
        self.scene.add(light, gfx.AmbientLight(0.4))

    def _create_controller(self):
        self.controller = gfx.OrbitController(self.camera, register_events=self.renderer)

    def update(self, nodes, edges, noise_strength):
        """Updates the visual mesh based on cluster state data."""

        # Clear previous geometry
        self.nodes_group.clear()
        self.edges_group.clear()

        # 1. Render Nodes (Spheres with color based on fidelity)
        for node in nodes:
            fidelity = max(0.0, min(1.0, node.fidelity))

            # Color mapping: Gold (1.0) -> Violet (0.0) based on noise/fidelity
            color_r = fidelity
            color_g = fidelity * 0.8
            color_b = 1.0 - fidelity * 0.5

            mat = gfx.MeshStandardMaterial(color=(color_r, color_g, color_b))
            sphere = gfx.Mesh(gfx.SphereGeometry(0.4), mat)
            sphere.position = node.position

            # Noise deformation: Jitter position if noise is high
            if noise_strength > 0:
                sphere.position += (np.random.rand(3) - 0.5) * noise_strength * 2.0

            self.nodes_group.add(sphere)

        # 2. Render Edges (Cylinders with thickness based on entanglement strength)
        for edge in edges:
            n1, n2, fidelity = edge
            # Find node positions
            pos1 = nodes[n1].position if n1 < len(nodes) else np.array([0,0,0])
            pos2 = nodes[n2].position if n2 < len(nodes) else np.array([0,0,0])

            # Thickness proportional to fidelity
            thickness = 0.1 + fidelity * 0.2

            mat = gfx.MeshStandardMaterial(color=(1.0, 0.84, 0.0)) # Golden

            cylinder = gfx.Mesh(gfx.CylinderGeometry(thickness, thickness, 1.0, 12), mat)

            # Calculate midpoint and orientation
            mid = (pos1 + pos2) / 2
            direction = pos2 - pos1
            length = np.linalg.norm(direction)

            if length > 0:
                cylinder.position = mid
                cylinder.scale.y = length
                # Align cylinder to direction vector
                up = np.array([0, 1, 0])
                dir_norm = direction / length
                rot_mat = self._rotation_matrix_between(up, dir_norm)
                cylinder.rotation = self._quaternion_from_matrix(rot_mat)

                self.edges_group.add(cylinder)

    def _rotation_matrix_between(self, v1, v2):
        """Computes rotation matrix to align vector v1 to v2."""
        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 / np.linalg.norm(v2)
        v = np.cross(v1, v2)
        c = np.dot(v1, v2)
        if c == -1: return np.eye(3) * -1 # 180 degree flip
        s = np.linalg.norm(v)
        kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        return np.eye(3) + kmat + np.dot(kmat, kmat) * ((1 - c) / (s**2))

    def _quaternion_from_matrix(self, m):
        """Converts rotation matrix to quaternion (simplified for pygfx)."""
        # Using pygfx/wgpu-py quaternions or scipy if available, or manual.
        # Actually in pygfx math, we usually create a Matrix4 and get rotation from it,
        # or use scipy.spatial.transform.Rotation
        import math
        # simplistic conversion
        t = np.trace(m)
        if t > 0:
            s = math.sqrt(t + 1.0) * 2.0
            qw = 0.25 * s
            qx = (m[2, 1] - m[1, 2]) / s
            qy = (m[0, 2] - m[2, 0]) / s
            qz = (m[1, 0] - m[0, 1]) / s
        elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
            s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
            qw = (m[2, 1] - m[1, 2]) / s
            qx = 0.25 * s
            qy = (m[0, 1] + m[1, 0]) / s
            qz = (m[0, 2] + m[2, 0]) / s
        elif m[1, 1] > m[2, 2]:
            s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
            qw = (m[0, 2] - m[2, 0]) / s
            qx = (m[0, 1] + m[1, 0]) / s
            qy = 0.25 * s
            qz = (m[1, 2] + m[2, 1]) / s
        else:
            s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
            qw = (m[1, 0] - m[0, 1]) / s
            qx = (m[0, 2] + m[2, 0]) / s
            qy = (m[1, 2] + m[2, 1]) / s
            qz = 0.25 * s
        return [qx, qy, qz, qw]

    def render(self):
        self.renderer.render(self.scene, self.camera)
