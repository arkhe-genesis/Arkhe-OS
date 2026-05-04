"""
Substrato 90: Sophon Shader Integration — Real-time Coherence Visualization
Maps network coherence metrics to WGSL shader parameters for Pygfx/wgpu rendering.
"""
import numpy as np
import pygfx as gfx
from prometheus_api_client import PrometheusConnect

class SophonShaderVisualizer:
    """Real-time visualization of Sophon network coherence via warped fractal sphere."""

    def __init__(self, prometheus_url: str, shader_path: str = "shaders/sophon.wgsl"):
        self.prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        self.shader_path = shader_path
        self._load_shader()
        self._setup_pygfx()

    def _load_shader(self):
        """Load WGSL shader code."""
        with open(self.shader_path, "r") as f:
            self.wgsl_code = f.read()

    def _setup_pygfx(self):
        """Initialize Pygfx renderer with Sophon shader."""
        self.renderer = gfx.renderers.WgpuRenderer()
        self.scene = gfx.Scene()
        self.camera = gfx.PerspectiveCamera(70, 16/9)
        self.camera.position.z = 3.5

        # Create full-screen quad for shader
        geometry = gfx.plane_geometry(2, 2)
        material = gfx.Material(
            vertex_shader="",  # Default vertex shader
            fragment_shader=self.wgsl_code,
            uniform_buffers={
                "Uniforms": gfx.Buffer(np.zeros(32, dtype=np.float32))
            }
        )
        self.mesh = gfx.Mesh(geometry, material)
        self.scene.add(self.mesh)

    def fetch_coherence_metrics(self) -> dict:
        """Fetch real-time coherence metrics from Prometheus."""
        queries = {
            "coherence_distance": 'avg(sophon_coherence_distance{job="sophon-nodes"})',
            "delivery_rate": 'avg(sophon_delivery_rate{job="sophon-nodes"})',
            "cache_hit_rate": 'avg(sophon_jones_cache_hit_rate{job="sophon-nodes"})',
            "ber": 'avg(sophon_bit_error_rate{job="sophon-nodes", transducer_enabled="true"})',
        }

        metrics = {}
        for name, query in queries.items():
            try:
                result = self.prom.custom_query(query=query)
                metrics[name] = float(result[0]["value"][1])
            except:
                metrics[name] = None  # Fallback to default
        return metrics

    def metrics_to_shader_params(self, metrics: dict) -> np.ndarray:
        """Map network metrics to shader uniform parameters."""
        params = np.zeros(32, dtype=np.float32)

        # Time and resolution (updated in render loop)
        params[0] = 0.0  # time (set per-frame)
        params[1:3] = [1920, 1080]  # resolution (set per-frame)

        # Base parameters
        params[4] = 1.0  # speed
        params[5] = 1.0  # sphere_size

        # Map coherence distance to warp amplitude (inverse: lower coherence → more deformation)
        coh_dist = metrics.get("coherence_distance", 0.3)
        if coh_dist is None: coh_dist = 0.3
        params[6] = np.clip(1.0 - coh_dist / 0.5, 0.2, 1.0)  # warp_amp

        # Map delivery rate to warp falloff (higher delivery → smoother surface)
        delivery = metrics.get("delivery_rate", 0.97)
        if delivery is None: delivery = 0.97
        params[7] = np.clip(0.8 + delivery * 0.5, 1.0, 2.0)  # warp_falloff

        # Map cache hit rate to warp frequency (higher hit rate → finer details)
        cache_hit = metrics.get("cache_hit_rate", 0.81)
        if cache_hit is None: cache_hit = 0.81
        params[8] = np.clip(4.0 + cache_hit * 4.0, 4.0, 8.0)  # warp_freq

        # Fixed parameters
        params[9] = 10.0  # warp_steps
        params[10] = -0.4  # warp_velocity
        params[11] = 0.6  # noise_contrast

        # Color triad: map BER to color1 (higher BER → shift from blue to red)
        ber = metrics.get("ber", 1e-5)
        if ber is None: ber = 1e-5
        ber_normalized = np.clip(-np.log10(ber + 1e-10) / 5.0, 0, 1)  # 1e-5→1.0, 1e-4→0.0
        params[12:15] = np.array([ber_normalized, 0.164 * (1 - ber_normalized), 1.0])  # color1
        params[16:19] = np.array([1.0, 0.0, 0.5])  # color2 (fixed)
        params[20:23] = np.array([0.0, 1.0, 0.8])  # color3 (fixed)

        return params

    def render_frame(self):
        """Render a single frame with updated metrics."""
        # Fetch latest metrics
        metrics = self.fetch_coherence_metrics()

        # Update shader uniforms
        uniform_params = self.metrics_to_shader_params(metrics)
        uniform_params[0] = self.renderer.get_elapsed_time()  # Update time
        uniform_params[1:3] = self.renderer.get_logical_size()  # Update resolution

        # Write to GPU buffer
        self.mesh.material.uniform_buffers["Uniforms"].data[:] = uniform_params
        self.mesh.material.uniform_buffers["Uniforms"].update_range(0, 1)

        # Render
        self.renderer.render(self.scene, self.camera)
