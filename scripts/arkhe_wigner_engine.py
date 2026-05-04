#!/usr/bin/env python3
"""
arkhe_wigner_engine.py — Códex Arkhe-Pygfx Supremo
Baseado em Băzăvan et al., Nature Physics (2026), Eq. (2)
Renderiza Wigner functions de squeezing, trisqueezing e quadsqueezing.
Controles:
  1, 2, 3  -> Ordem do squeezing (n=2,3,4) com valores experimentais de Oxford
  Setas     -> Ajustar o parâmetro de squeezing (r)
  R         -> Resetar para os valores experimentais
"""

import pygfx as gfx
import wgpu
import numpy as np
from rendercanvas.qt import RenderCanvas  # Pode trocar por .glfw

# ============================================================
# 1. O SHADER WGSL (O CODEX REVELADO)
# ============================================================
WGSL_SHADER = """
struct Uniforms {
    time: f32,
    resolution: vec2<f32>,
    squeezing_order: i32,    // 2, 3, ou 4
    squeezing_parameter: f32, // r, r3s, r4s
    rotation_angle: f32,
};

@group(0) @binding(0) var<uniform> u: Uniforms;

// Wigner function generalizada para estados de squeezing puro
fn wigner_generalized(x: f32, p: f32, n: i32, r: f32, theta: f32) -> f32 {
    let cos_t = cos(theta);
    let sin_t = sin(theta);
    let xr = x * cos_t + p * sin_t;
    let pr = -x * sin_t + p * cos_t;

    var w: f32 = 0.0;

    if (n == 2) {
        // Squeezed state puro (Gaussiana)
        let sx = exp(r);
        let sy = exp(-r);
        let arg = (xr * xr) / (sy * sy) + (pr * pr) / (sx * sx);
        w = exp(-0.5 * arg) / 3.14159;
    }
    else if (n == 3) {
        // Três lóbulos com interferência
        let r_eff = r * 0.7;
        let scale = 1.0 / (1.0 + r * 0.3);
        for (var k: i32 = 0; k < 3; k++) {
            let angle = f32(k) * 2.094 + r * 0.2;
            let dx = xr - r_eff * 3.0 * cos(angle);
            let dp = pr - r_eff * 3.0 * sin(angle);
            let gauss = exp(-0.5 * (dx * dx + dp * dp) * scale);
            let sign = 1.0 - 2.0 * f32((k % 2 == 0) ? 0 : 1) * (r / (0.2 + r)) * 0.8;
            w += gauss * sign;
        }
        w += -0.15 * r * exp(-0.3 * (xr * xr + pr * pr));
        w = w * 0.25;
    }
    else if (n == 4) {
        // Quatro lóbulos cardeais com poço central negativo
        let r_eff = r * 5.0;
        for (var k: i32 = 0; k < 4; k++) {
            let angle = f32(k) * 1.571 + r * 0.15;
            let dx = xr - r_eff * 2.0 * cos(angle);
            let dp = pr - r_eff * 2.0 * sin(angle);
            let gauss = exp(-0.3 * (dx * dx + dp * dp));
            let sign = 1.0 - 2.0 * f32(k % 2);
            w += gauss * sign * (0.3 + r * 0.5);
        }
        let central = exp(-1.5 * (xr * xr + pr * pr));
        w += -0.6 * r * central;
        w = w * 0.35;
    }
    else {
        // Coerente (n=1, referência)
        w = exp(-0.5 * (xr * xr + pr * pr)) / 3.14159;
    }

    return w * 1.5;
}

@fragment
fn fs_main(@builtin(position) coord: vec4<f32>) -> @location(0) vec4<f32> {
    let aspect = u.resolution.x / u.resolution.y;
    var x = (coord.x / u.resolution.x - 0.5) * 8.0 * aspect;
    var p = (coord.y / u.resolution.y - 0.5) * 8.0;

    let w_val = wigner_generalized(x, p, u.squeezing_order, u.squeezing_parameter, u.rotation_angle);

    // Mapeamento de cor: positivo -> dourado, negativo -> azul-violeta
    var col = vec3<f32>(0.0);
    if (w_val >= 0.0) {
        let intensity = w_val * 0.8;
        col = vec3<f32>(1.0, 0.9, 0.2) * intensity + vec3<f32>(0.02, 0.0, 0.05);
    } else {
        let intensity = abs(w_val) * 1.2;
        col = vec3<f32>(0.3, 0.1, 1.0) * intensity + vec3<f32>(0.0, 0.02, 0.1);
    }

    // Realce de bordas
    let eps = 1.0 / u.resolution.x * 8.0;
    let w_dx = wigner_generalized(x + eps, p, u.squeezing_order, u.squeezing_parameter, u.rotation_angle);
    let w_dy = wigner_generalized(x, p + eps, u.squeezing_order, u.squeezing_parameter, u.rotation_angle);
    let grad = length(vec2<f32>(w_dx - w_val, w_dy - w_val)) * 10.0;
    col += vec3<f32>(0.15, 0.15, 0.2) * grad;

    return vec4<f32>(col, 1.0);
}
"""

# ============================================================
# 2. A ARQUITETURA DO MOTOR PYGFX
# ============================================================
class ArkheWignerEngine:
    def __init__(self):
        # Valores experimentais de Oxford (2026)
        self.oxford_params = {
            2: 1.09,   # squeezing r
            3: 0.19,   # trisqueezing r3s
            4: 0.054,  # quadsqueezing r4s
        }
        self.current_order = 4
        self.current_r = self.oxford_params[self.current_order]
        self.rotation = 0.0

        # Criar canvas e renderer
        self.canvas = RenderCanvas(
            title="Arkhe Wigner Engine — Oxford 2026 | [1] Squeeze [2] Trisqueeze [3] Quadsqueeze",
            size=(800, 600)
        )
        self.renderer = gfx.renderers.WgpuRenderer(self.canvas)
        self.device = self.renderer.device

        # Compilar shader
        self.shader = self.device.create_shader_module(code=WGSL_SHADER)

        # Buffer de uniformes: alinhado a 16 bytes
        # Layout: [time(f32), pad(f32), width(f32), height(f32), order(i32), r(f32), theta(f32), pad2(f32)]
        self.uniform_data = np.zeros(8, dtype=np.float32)
        self.uniform_data[4] = self.current_order
        self.uniform_data[5] = self.current_r
        self.uniform_data[6] = self.rotation

        self.uniform_buffer = self.device.create_buffer_with_data(
            data=self.uniform_data.tobytes(),
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
            label="ArkheUniforms"
        )

        # Bind group
        bind_group_layout = self.device.create_bind_group_layout(entries=[
            {"binding": 0, "visibility": wgpu.ShaderStage.FRAGMENT, "buffer": {"type": wgpu.BufferBindingType.uniform}},
        ])
        self.bind_group = self.device.create_bind_group(
            layout=bind_group_layout,
            entries=[{"binding": 0, "resource": {"buffer": self.uniform_buffer, "offset": 0, "size": self.uniform_buffer.size}}]
        )

        # Pipeline
        pipeline_layout = self.device.create_pipeline_layout(bind_group_layouts=[bind_group_layout])
        self.pipeline = self.device.create_render_pipeline(
            layout=pipeline_layout,
            vertex={
                "module": self.shader,
                "entry_point": "vs_main" if hasattr(self.shader, 'vs_main') else "fs_main", # placeholder correto
                "buffers": []
            },
            fragment={
                "module": self.shader,
                "entry_point": "fs_main",
                "targets": [{"format": wgpu.TextureFormat.rgba8unorm}]
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_strip}
        )

        # Para fullscreen quad, usar um vertex shader simples
        self._create_fullscreen_quad()

        # Configurar callbacks
        self.canvas.add_event_handler(self._on_key_down, "key_down")
        self.canvas.request_draw(self._animate)

    def _create_fullscreen_quad(self):
        # Vertex shader embutido para fullscreen pass
        vs_code = """
        @vertex
        fn vs_main(@builtin(vertex_index) vi: u32) -> @builtin(position) vec4<f32> {
            var positions = array<vec2<f32>, 3>(
                vec2<f32>(-1.0, -1.0), vec2<f32>(3.0, -1.0), vec2<f32>(-1.0, 3.0)
            );
            let p = positions[vi];
            return vec4<f32>(p, 0.0, 1.0);
        }
        """
        self.vs_module = self.device.create_shader_module(code=vs_code)
        # Atualizar pipeline com vertex stage
        self.pipeline = self.device.create_render_pipeline(
            layout=self.pipeline.get_layout(),
            vertex={"module": self.vs_module, "entry_point": "vs_main", "buffers": []},
            fragment={"module": self.shader, "entry_point": "fs_main",
                      "targets": [{"format": wgpu.TextureFormat.rgba8unorm}]},
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list}
        )

    def _update_uniforms(self):
        size = self.canvas.get_logical_size()
        self.uniform_data[0] += 0.01  # time
        self.uniform_data[2] = size[0]
        self.uniform_data[3] = size[1]
        self.uniform_data[4] = self.current_order
        self.uniform_data[5] = self.current_r
        self.uniform_data[6] = self.rotation
        self.device.queue.write_buffer(self.uniform_buffer, 0, self.uniform_data.tobytes())

    def _on_key_down(self, event):
        key = event.key
        if key == '1':
            self.current_order = 2
            self.current_r = self.oxford_params[2]
            self.rotation = 0.0
        elif key == '2':
            self.current_order = 3
            self.current_r = self.oxford_params[3]
            self.rotation = 0.0
        elif key == '3':
            self.current_order = 4
            self.current_r = self.oxford_params[4]
            self.rotation = 0.0
        elif key == 'ArrowUp':
            self.current_r = min(5.0, self.current_r * 1.1)
        elif key == 'ArrowDown':
            self.current_r = max(0.01, self.current_r / 1.1)
        elif key == 'R':
            self.current_r = self.oxford_params[self.current_order]

    def _animate(self):
        self._update_uniforms()
        command_encoder = self.device.create_command_encoder()
        render_pass = command_encoder.begin_render_pass(
            color_attachments=[{
                "view": self.canvas.get_context().get_current_texture().create_view(),
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
                "clear_value": (0.0, 0.0, 0.0, 1.0)
            }]
        )
        render_pass.set_pipeline(self.pipeline)
        render_pass.set_bind_group(0, self.bind_group)
        render_pass.draw(3, 1)  # 3 vértices para triângulo
        render_pass.end()
        self.device.queue.submit([command_encoder.finish()])
        self.canvas.request_draw()

    def run(self):
        self.canvas.run()

# ============================================================
# 3. INICIAÇÃO DO RITO
# ============================================================
if __name__ == "__main__":
    engine = ArkheWignerEngine()
    engine.run()
