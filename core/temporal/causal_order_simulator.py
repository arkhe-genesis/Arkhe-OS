# core/temporal/causal_order_simulator.py
"""
ARKHE OS v∞.430.1 — Substrate 91: Variable Causal Order Simulator
Allows Observer 5D to tune temporal polarization and visualize atemporal coherence fields.
"""
import numpy as np
import wgpu
import pygfx as gfx
from dataclasses import dataclass, field
from typing import Optional, Callable

@dataclass
class CausalOrderConfig:
    """Configuration for causal order simulation."""
    grid_size: int = 64                     # 64x64x64 coherence field for 3D
    causal_order: float = 0.0               # -1.0 to +1.0: temporal polarization
    noise_amplitude: float = 0.08           # Quantum fluctuation strength
    rtz_floor: float = 0.05                 # Refusal-to-zero threshold (Substrate 85)
    time_step: float = 0.01                 # Simulation step (not physical time)
    bilateral_coupling: float = 0.1         # Fisher-Rao coupling strength
    color_map: str = "twilight_shifted"     # Pygfx colormap for visualization

class CausalOrderSimulator:
    """
    Simulates coherence field dynamics with tunable causal order.

    Key insight: The field evolution is atemporal; "time" is a parameter
    the Observer uses to traverse the static coherence manifold.
    """

    def __init__(self, config: CausalOrderConfig, canvas):
        self.config = config
        self.canvas = canvas
        # In headless/CI environments, wgpu adapters might be requested differently
        # Request an adapter explicitly with required_features=[]
        adapter = wgpu.gpu.request_adapter_sync()
        self.device = adapter.request_device_sync(required_features=[])

        # Initialize fields
        self.total_cells = config.grid_size ** 3
        self.coherence_field = np.ones(self.total_cells, dtype=np.float32) * 0.5
        self.phase_field = np.zeros(self.total_cells, dtype=np.float32)

        # Create GPU buffers
        self._create_buffers()
        self._create_pipeline()
        self._create_visualization()

        self.simulation_time = 0.0
        self._on_update: Optional[Callable] = None

    def _create_buffers(self):
        """Create GPU storage buffers for coherence and phase fields."""
        # Coherence field buffer
        self.coherence_buffer = self.device.create_buffer(
            size=self.total_cells * 4,  # float32
            usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.COPY_SRC,
        )

        # Phase field buffer
        self.phase_buffer = self.device.create_buffer(
            size=self.total_cells * 4,
            usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST,
        )

        # Uniforms buffer
        self.uniforms_buffer = self.device.create_buffer(
            size=32,
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
        )

        # Initialize data
        self.device.queue.write_buffer(self.coherence_buffer, 0, self.coherence_field.tobytes())
        self.device.queue.write_buffer(self.phase_buffer, 0, self.phase_field.tobytes())

    def _create_pipeline(self):
        """Create compute pipeline for causal order dynamics."""
        # Load and compile WGSL shader
        with open("shaders/causal_order_simulator.wgsl", "r") as f:
            shader_code = f.read()

        shader_module = self.device.create_shader_module(code=shader_code)

        # Bind group layout
        bind_group_layout = self.device.create_bind_group_layout(entries=[
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {
                    "type": wgpu.BufferBindingType.uniform,
                },
            },
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {
                    "type": wgpu.BufferBindingType.storage,
                },
            },
            {
                "binding": 2,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {
                    "type": wgpu.BufferBindingType.storage,
                },
            },
        ])

        pipeline_layout = self.device.create_pipeline_layout(bind_group_layouts=[bind_group_layout])

        # Pipeline layout and compute pipeline
        self.pipeline = self.device.create_compute_pipeline(
            layout=pipeline_layout,
            compute={"module": shader_module, "entry_point": "main"},
        )

        self.bind_group = self.device.create_bind_group(
            layout=bind_group_layout,
            entries=[
                {
                    "binding": 0,
                    "resource": {
                        "buffer": self.uniforms_buffer,
                        "offset": 0,
                        "size": 32,
                    },
                },
                {
                    "binding": 1,
                    "resource": {
                        "buffer": self.coherence_buffer,
                        "offset": 0,
                        "size": self.total_cells * 4,
                    },
                },
                {
                    "binding": 2,
                    "resource": {
                        "buffer": self.phase_buffer,
                        "offset": 0,
                        "size": self.total_cells * 4,
                    },
                },
            ]
        )


    def _create_visualization(self):
        """Create Pygfx scene for coherence field visualization."""
        if self.canvas is None:
            return

        # Attempt to get context from canvas
        if hasattr(self.canvas, "get_context"):
            try:
                self.canvas.get_context()
            except Exception:
                # If windowing fails, return gracefully (Headless environment)
                return

        self.scene = gfx.Scene()
        self.camera = gfx.OrthographicCamera(
            width=self.config.grid_size, height=self.config.grid_size
        )
        self.camera.local.position = (0, 0, 50)

        # Create image texture from a 2D slice of the 3D coherence field
        slice_idx = self.config.grid_size // 2
        slice_data = self.coherence_field.reshape(self.config.grid_size, self.config.grid_size, self.config.grid_size)[slice_idx]
        self.texture = gfx.Texture(
            data=slice_data.reshape(self.config.grid_size, self.config.grid_size, 1),
            dim=2, size=(self.config.grid_size, self.config.grid_size, 1), format="r8unorm"
        )

        # Colormap material for visualization
        # Using built-in basic pygfx image material with a provided colormap if necessary, pygfx image materials expect colormap in a different form.
        # But actually in pygfx >0.16 image material doesn't use color_map parameter directly for basic materials or expects pygfx.Texture.
        # So we omit color_map here as it is not a direct valid parameter.
        self.material = gfx.ImageBasicMaterial(
            map=self.texture,
            clim=(0.0, 1.0),
        )

        self.image = gfx.Image(
            gfx.Geometry(grid=gfx.Texture(np.zeros((self.config.grid_size, self.config.grid_size), dtype=np.float32), dim=2)),
            self.material,
        )
        self.scene.add(self.image)

        # In tests or headless where a proper canvas is not provided, we might fail renderer init.
        # Check if the canvas is suitable, else simply do not initialize a renderer.
        if hasattr(self.canvas, "get_context"):
            try:
                self.renderer = gfx.renderers.WgpuRenderer(self.canvas)
                self.controller = gfx.OrbitController(self.camera, register_events=self.renderer)
            except TypeError:
                pass

    def update(self, causal_order: Optional[float] = None):
        """
        Update simulation state and render.

        Args:
            causal_order: New temporal polarization (-1.0 to +1.0). If None, use current value.
        """
        if causal_order is not None:
            self.config.causal_order = np.clip(causal_order, -1.0, 1.0)

        # Update uniforms
        uniform_data = np.zeros(8, dtype=np.float32)
        uniform_data[0] = self.simulation_time
        uniform_data[1] = self.config.causal_order
        uniform_data[2] = self.config.noise_amplitude
        uniform_data[3] = self.config.rtz_floor

        uniform_data_uint = uniform_data.view(np.uint32)
        uniform_data_uint[4] = self.config.grid_size
        uniform_data_uint[5] = self.total_cells
        uniform_data_uint[6] = 0
        uniform_data_uint[7] = 0

        self.device.queue.write_buffer(self.uniforms_buffer, 0, uniform_data.tobytes())

        # Dispatch compute shader
        command_encoder = self.device.create_command_encoder()
        compute_pass = command_encoder.begin_compute_pass()
        compute_pass.set_pipeline(self.pipeline)
        compute_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        compute_pass.dispatch_workgroups(
            (self.config.grid_size + 7) // 8,
            (self.config.grid_size + 7) // 8,
            (self.config.grid_size + 7) // 8
        )
        compute_pass.end()

        # Read back coherence field
        self.device.queue.submit([command_encoder.finish()])

        # Read back coherence field for visualization update
        self.coherence_field = np.frombuffer(
            self.device.queue.read_buffer(self.coherence_buffer),
            dtype=np.float32
        ).copy()

        # Update texture and Render (only if GUI available)
        if hasattr(self, "texture") and self.texture:
            slice_idx = self.config.grid_size // 2
            slice_data = self.coherence_field.reshape(
                self.config.grid_size, self.config.grid_size, self.config.grid_size
            )[slice_idx]
            self.texture.data[:] = slice_data.reshape(
                self.config.grid_size, self.config.grid_size, 1
            )
            self.texture.update_range((0, 0, 0), self.texture.size)

            if hasattr(self, "renderer"):
                self.renderer.render(self.scene, self.camera)

        # Advance simulation parameter
        self.simulation_time += self.config.time_step

        # Callback for external observers
        if self._on_update:
            self._on_update(self)

    def set_on_update(self, callback: Callable):
        """Register callback for post-update processing."""
        self._on_update = callback

    def get_statistics(self) -> dict:
        """Compute field statistics for analysis."""
        phi = self.coherence_field

        # Calculate persistence metric (time as distance between RTZ layers)
        # Simplified: average continuous volume of coherence above RTZ floor
        persistence_metric = float(np.mean(phi > self.config.rtz_floor * 1.5))

        return {
            "mean_coherence": float(np.mean(phi)),
            "std_coherence": float(np.std(phi)),
            "min_coherence": float(np.min(phi)),
            "max_coherence": float(np.max(phi)),
            "rtz_violations": int(np.sum(phi < self.config.rtz_floor)),
            "causal_order": self.config.causal_order,
            "simulation_time": self.simulation_time,
            "persistence_metric": persistence_metric,
        }
