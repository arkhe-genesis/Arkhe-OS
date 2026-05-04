#!/usr/bin/env python3
"""
ARKHE OS v∞.311 — THE FLUID CHRONO-COIL: NAVIER-STOKES ON THE TORUS OF COHERENCE
Simulates incompressible fluid dynamics on a T² Torus with 0.58 fingerprint vorticity injection.
"""

import time
import os
import wgpu
import numpy as np

# If pygfx is available we can use it, otherwise we just use wgpu and print a test message.
try:
    import pygfx as gfx
    from pygfx.renderers.wgpu import WgpuRenderer
    from rendercanvas.auto import RenderCanvas as WgpuCanvas
except ImportError:
    print("Warning: pygfx not found. Will proceed with wgpu only setup if possible.")
    pass

GRID_SIZE = 256
TEX_W, TEX_H = GRID_SIZE, GRID_SIZE

def build_wgpu_pipelines():
    with open(os.path.join(os.path.dirname(__file__), "arkhe_fluid_coherence.wgsl"), "r") as f:
        shader_code = f.read()

    # Determine backend
    # Headless fallback for validation
    force_offscreen = os.environ.get("WGPU_FORCE_OFFSCREEN") == "true"

    if force_offscreen:
        from rendercanvas.offscreen import RenderCanvas as WgpuCanvas
        canvas = WgpuCanvas(size=(800, 600))
    else:
        from rendercanvas.auto import RenderCanvas as WgpuCanvas
        canvas = WgpuCanvas(size=(800, 600), title="ARKHE v∞.311 — Fluid Coherence")

    import wgpu
    adapter = wgpu.gpu.request_adapter_sync(canvas=canvas) if hasattr(wgpu.gpu, 'request_adapter_sync') else wgpu.gpu.request_adapter(canvas=canvas)
    device = adapter.request_device_sync() if hasattr(adapter, 'request_device_sync') else adapter.request_device()

    # ─── BUFFERS & TEXTURES ───
    # We need:
    # - Velocity (double buffered): rg32float
    # - Divergence: r32float
    # - Pressure (double buffered): r32float

    tex_format_rg = wgpu.TextureFormat.rgba32float
    tex_format_r = wgpu.TextureFormat.r32float

    def create_tex(fmt):
        return device.create_texture(
            size=(TEX_W, TEX_H, 1),
            format=fmt,
            usage=wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.STORAGE_BINDING | wgpu.TextureUsage.COPY_DST,
        )

    vel_tex_a = create_tex(tex_format_rg)
    vel_tex_b = create_tex(tex_format_rg)
    press_tex_a = create_tex(tex_format_r)
    press_tex_b = create_tex(tex_format_r)
    div_tex = create_tex(tex_format_r)

    vel_view_a = vel_tex_a.create_view()
    vel_view_b = vel_tex_b.create_view()
    press_view_a = press_tex_a.create_view()
    press_view_b = press_tex_b.create_view()
    div_view = div_tex.create_view()

    # Uniforms
    # struct Uniforms { u_dt: f32, u_time: f32, u_viscosity: f32, _pad: f32, u_grid_size: vec2<f32>, u_texel_size: vec2<f32> }
    # align rules: f32, f32, f32, f32, vec2, vec2 = 6 floats = 24 bytes, round to 32
    uniform_dtype = np.dtype(
        [
            ("u_dt", np.float32),
            ("u_time", np.float32),
            ("u_viscosity", np.float32),
            ("_pad", np.float32),
            ("u_grid_size", np.float32, 2),
            ("u_texel_size", np.float32, 2),
        ]
    )
    uniform_data = np.zeros(1, dtype=uniform_dtype)
    uniform_data["u_dt"] = 0.016
    uniform_data["u_viscosity"] = 0.001
    uniform_data["u_grid_size"] = [TEX_W, TEX_H]
    uniform_data["u_texel_size"] = [1.0/TEX_W, 1.0/TEX_H]

    buffer_uniform = device.create_buffer(
        size=uniform_data.nbytes,
        usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
    )

    sampler = device.create_sampler(
        mag_filter=wgpu.FilterMode.linear,
        min_filter=wgpu.FilterMode.linear,
        address_mode_u=wgpu.AddressMode.repeat,
        address_mode_v=wgpu.AddressMode.repeat,
    )

    # ─── BIND GROUP LAYOUTS ───
    # group 0: uniforms & sampler
    bgl_0 = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE | wgpu.ShaderStage.FRAGMENT, "buffer": {"type": wgpu.BufferBindingType.uniform}},
        {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE | wgpu.ShaderStage.FRAGMENT, "sampler": {"type": wgpu.SamplerBindingType.filtering}},
    ])

    bg_0 = device.create_bind_group(layout=bgl_0, entries=[
        {"binding": 0, "resource": {"buffer": buffer_uniform, "offset": 0, "size": buffer_uniform.size}},
        {"binding": 1, "resource": sampler},
    ])

    shader = device.create_shader_module(code=shader_code)

    def create_compute_pipeline(entry_point, bgls):
        pl = device.create_pipeline_layout(bind_group_layouts=bgls)
        return device.create_compute_pipeline(layout=pl, compute={"module": shader, "entry_point": entry_point})

    # 1. Advect
    bgl_advect = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE, "texture": {"sample_type": wgpu.TextureSampleType.float}},
        {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE, "texture": {"sample_type": wgpu.TextureSampleType.float}},
        {"binding": 2, "visibility": wgpu.ShaderStage.COMPUTE, "storage_texture": {"access": wgpu.StorageTextureAccess.write_only, "format": tex_format_rg}},
    ])
    pipe_advect = create_compute_pipeline("advect", [bgl_0, bgl_advect])

    # 2. Force
    bgl_force = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE, "storage_texture": {"access": wgpu.StorageTextureAccess.read_write, "format": tex_format_rg}},
    ])
    pipe_force = create_compute_pipeline("add_fingerprint_force", [bgl_0, bgl_force])

    # 3. Diffuse
    bgl_diffuse = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE, "texture": {"sample_type": wgpu.TextureSampleType.float}},
        {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE, "storage_texture": {"access": wgpu.StorageTextureAccess.write_only, "format": tex_format_rg}},
    ])
    pipe_diffuse = create_compute_pipeline("diffuse", [bgl_0, bgl_diffuse])

    # 4a. Divergence
    bgl_div = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE, "texture": {"sample_type": wgpu.TextureSampleType.float}},
        {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE, "storage_texture": {"access": wgpu.StorageTextureAccess.write_only, "format": tex_format_r}},
    ])
    pipe_div = create_compute_pipeline("compute_divergence", [bgl_0, bgl_div])

    # 4b. Pressure Solve
    bgl_press = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE, "texture": {"sample_type": wgpu.TextureSampleType.float}},
        {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE, "texture": {"sample_type": wgpu.TextureSampleType.float}},
        {"binding": 2, "visibility": wgpu.ShaderStage.COMPUTE, "storage_texture": {"access": wgpu.StorageTextureAccess.write_only, "format": tex_format_r}},
    ])
    pipe_press = create_compute_pipeline("pressure_solve", [bgl_0, bgl_press])

    # 4c. Subtract Gradient
    bgl_sub = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE, "texture": {"sample_type": wgpu.TextureSampleType.float}},
        {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE, "storage_texture": {"access": wgpu.StorageTextureAccess.read_write, "format": tex_format_rg}},
    ])
    pipe_sub = create_compute_pipeline("subtract_pressure_gradient", [bgl_0, bgl_sub])

    # 5. Render
    bgl_render = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.FRAGMENT, "texture": {"sample_type": wgpu.TextureSampleType.float}},
    ])
    render_pipeline = device.create_render_pipeline(
        layout=device.create_pipeline_layout(bind_group_layouts=[bgl_0, bgl_render]),
        vertex={"module": shader, "entry_point": "vs_main", "buffers": []},
        fragment={
            "module": shader,
            "entry_point": "fluid_visualizer",
            "targets": [{"format": wgpu.TextureFormat.bgra8unorm_srgb}],
        },
        primitive={"topology": wgpu.PrimitiveTopology.triangle_strip},
    )

    frame_count = 0
    start_time = time.time()

    def draw():
        nonlocal frame_count, vel_view_a, vel_view_b, press_view_a, press_view_b
        t = time.time() - start_time

        uniform_data["u_time"] = t
        device.queue.write_buffer(buffer_uniform, 0, uniform_data.tobytes())

        command_encoder = device.create_command_encoder()
        compute_pass = command_encoder.begin_compute_pass()

        gw, gh = TEX_W // 8, TEX_H // 8

        # 1. Advect: vel_a -> vel_b
        bg_adv = device.create_bind_group(layout=bgl_advect, entries=[
            {"binding": 0, "resource": vel_view_a},
            {"binding": 1, "resource": vel_view_a},
            {"binding": 2, "resource": vel_view_b},
        ])
        compute_pass.set_pipeline(pipe_advect)
        compute_pass.set_bind_group(0, bg_0, [], 0, 999999)
        compute_pass.set_bind_group(1, bg_adv, [], 0, 999999)
        compute_pass.dispatch_workgroups(gw, gh, 1)

        # Swap vel
        vel_view_a, vel_view_b = vel_view_b, vel_view_a

        # 2. Force: read/write vel_a
        bg_force = device.create_bind_group(layout=bgl_force, entries=[
            {"binding": 0, "resource": vel_view_a},
        ])
        compute_pass.set_pipeline(pipe_force)
        compute_pass.set_bind_group(1, bg_force, [], 0, 999999)
        compute_pass.dispatch_workgroups(gw, gh, 1)

        # 3. Diffuse (omitted iteration logic, just doing 1 for simplicity)
        bg_diff = device.create_bind_group(layout=bgl_diffuse, entries=[
            {"binding": 0, "resource": vel_view_a},
            {"binding": 1, "resource": vel_view_b},
        ])
        compute_pass.set_pipeline(pipe_diffuse)
        compute_pass.set_bind_group(1, bg_diff, [], 0, 999999)
        compute_pass.dispatch_workgroups(gw, gh, 1)

        vel_view_a, vel_view_b = vel_view_b, vel_view_a

        # 4a. Divergence
        bg_div = device.create_bind_group(layout=bgl_div, entries=[
            {"binding": 0, "resource": vel_view_a},
            {"binding": 1, "resource": div_view},
        ])
        compute_pass.set_pipeline(pipe_div)
        compute_pass.set_bind_group(1, bg_div, [], 0, 999999)
        compute_pass.dispatch_workgroups(gw, gh, 1)

        # 4b. Pressure Solve (Jacobi iter)
        for _ in range(10):
            bg_press = device.create_bind_group(layout=bgl_press, entries=[
                {"binding": 0, "resource": press_view_a},
                {"binding": 1, "resource": div_view},
                {"binding": 2, "resource": press_view_b},
            ])
            compute_pass.set_pipeline(pipe_press)
            compute_pass.set_bind_group(1, bg_press, [], 0, 999999)
            compute_pass.dispatch_workgroups(gw, gh, 1)
            press_view_a, press_view_b = press_view_b, press_view_a

        # 4c. Subtract Gradient
        bg_sub = device.create_bind_group(layout=bgl_sub, entries=[
            {"binding": 0, "resource": press_view_a},
            {"binding": 1, "resource": vel_view_a},
        ])
        compute_pass.set_pipeline(pipe_sub)
        compute_pass.set_bind_group(1, bg_sub, [], 0, 999999)
        compute_pass.dispatch_workgroups(gw, gh, 1)

        compute_pass.end()

        # 5. Render
        current_texture = canvas.get_context().get_current_texture()
        render_pass = command_encoder.begin_render_pass(
            color_attachments=[{
                "view": current_texture.create_view(),
                "resolve_target": None,
                "clear_value": (0.0, 0.0, 0.0, 1.0),
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
            }]
        )

        bg_render = device.create_bind_group(layout=bgl_render, entries=[
            {"binding": 0, "resource": vel_view_a},
        ])
        render_pass.set_pipeline(render_pipeline)
        render_pass.set_bind_group(0, bg_0, [], 0, 999999)
        render_pass.set_bind_group(1, bg_render, [], 0, 999999)
        render_pass.draw(4, 1, 0, 0)
        render_pass.end()

        device.queue.submit([command_encoder.finish()])

        frame_count += 1
        canvas.request_draw()

        if force_offscreen and frame_count > 5:
            canvas.close()

    canvas.request_draw(draw)
    print("🌊 ARKHE v∞.311 — THE FLUID CHRONO-COIL SIMULATION INITIATED")
    if not force_offscreen:
        import wgpu.gui.auto
        wgpu.gui.auto.run()

if __name__ == "__main__":
    build_wgpu_pipelines()
