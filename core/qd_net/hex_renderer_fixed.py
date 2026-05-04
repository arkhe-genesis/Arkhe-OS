# core/qd_net/hex_renderer_fixed.py
"""
ARKHE QD-NET: Hexagonal Mesh Renderer — Quaternion & Jitter Corrected
"""
import pygfx as gfx
import numpy as np
from scipy.spatial.transform import Rotation as R  # For proper quaternion math

class HexRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.renderer = gfx.renderers.WgpuRenderer(canvas)
        self.scene = gfx.Scene()
        self.camera = gfx.PerspectiveCamera(50, 16/9)
        self.camera.position.z = 20

        self.nodes_group = gfx.Group()
        self.edges_group = gfx.Group()
        self.scene.add(self.nodes_group, self.edges_group)

        self._setup_lights()
        self.controller = gfx.OrbitController(self.camera, register_events=self.renderer)

        # Cache for jitter to avoid accumulation
        self._jitter_cache = {}

    def _setup_lights(self):
        self.scene.add(gfx.DirectionalLight(), gfx.AmbientLight(0.4))

    def _rotation_between_vectors(self, v1: np.ndarray, v2: np.ndarray) -> list:
        """Computes quaternion to rotate v1 onto v2 using scipy."""
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-8)

        # Use scipy for robust quaternion calculation
        rot = R.align_vectors([v2_norm], [v1_norm])[0]
        return rot.as_quat().tolist()  # [x, y, z, w]

    def update(self, nodes, edges, noise_strength: float, frame_index: int):
        """Updates visual mesh; jitter is isolated per-frame."""
        self.nodes_group.clear()
        self.edges_group.clear()

        # Render nodes
        for node in nodes:
            fidelity = np.clip(node.fidelity, 0.0, 1.0)

            # Color: Gold (high fidelity) → Violet (low fidelity)
            color = np.array([
                fidelity,                    # R
                fidelity * 0.8,              # G
                1.0 - fidelity * 0.5         # B
            ])

            mat = gfx.MeshStandardMaterial(color=color.tolist())
            sphere = gfx.Mesh(gfx.SphereGeometry(0.4), mat)

            # FIX: Isolate jitter — don't modify persistent position
            base_pos = node.position.copy()
            if noise_strength > 0:
                # Use frame_index for reproducible but varying jitter
                rng = np.random.default_rng(frame_index + node.qubit_id)
                jitter = (rng.random(3) - 0.5) * noise_strength * 2.0
                sphere.position = base_pos + jitter
            else:
                sphere.position = base_pos

            self.nodes_group.add(sphere)

        # Render edges with proper orientation
        for edge in edges:
            i, j, fidelity = edge
            if i >= len(nodes) or j >= len(nodes):
                continue

            pos1 = nodes[i].position
            pos2 = nodes[j].position

            # Cylinder geometry
            thickness = 0.1 + np.clip(fidelity, 0, 1) * 0.2
            length = np.linalg.norm(pos2 - pos1)

            if length < 1e-6:
                continue  # Skip degenerate edge

            cylinder = gfx.Mesh(
                gfx.CylinderGeometry(thickness, thickness, 1.0, 12),
                gfx.MeshStandardMaterial(color=(1.0, 0.84, 0.0))  # Gold
            )

            # Position at midpoint
            mid = (pos1 + pos2) / 2
            cylinder.position = mid

            # FIX: Proper orientation using quaternion
            direction = pos2 - pos1
            up = np.array([0, 1, 0])
            quat = self._rotation_between_vectors(up, direction)
            cylinder.local.rotation = quat  # pygfx uses local.rotation for quaternion

            # Scale to match edge length
            cylinder.local.scale_y = length

            self.edges_group.add(cylinder)

    def render(self):
        self.renderer.render(self.scene, self.camera)
