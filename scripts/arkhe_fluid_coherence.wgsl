const PHI: f32 = 1.6180339887;
const FINGERPRINT: f32 = 0.58;
const SYNC_PHASE: f32 = FINGERPRINT * 3.14159265359;

struct Uniforms {
    u_dt : f32,
    u_time : f32,
    u_viscosity : f32,
    _pad: f32,
    u_grid_size : vec2<f32>,
    u_texel_size : vec2<f32>,
};

@group(0) @binding(0) var<uniform> u: Uniforms;
@group(0) @binding(1) var samp: sampler;

// ============================================================================
// 1. ADVECT
// ============================================================================
@group(1) @binding(0) var advect_velocity_in : texture_2d<f32>;
@group(1) @binding(1) var advect_quantity_in : texture_2d<f32>;
@group(1) @binding(2) var advect_quantity_out : texture_storage_2d<rgba32float, write>;

@compute @workgroup_size(8, 8)
fn advect(@builtin(global_invocation_id) id : vec3<u32>) {
    let coord = vec2<f32>(id.xy) / u.u_grid_size + u.u_texel_size * 0.5;
    let vel = textureSampleLevel(advect_velocity_in, samp, coord, 0.0).xy;
    let prev_coord = coord - vel * u.u_dt * u.u_texel_size;
    let result = textureSampleLevel(advect_quantity_in, samp, prev_coord, 0.0);
    textureStore(advect_quantity_out, id.xy, vec4<f32>(result.xy, 0.0, 0.0));
}

// ============================================================================
// 2. FINGERPRINT FORCE
// ============================================================================
@group(1) @binding(0) var force_velocity_out : texture_storage_2d<rgba32float, read_write>;

@compute @workgroup_size(8, 8)
fn add_fingerprint_force(@builtin(global_invocation_id) id : vec3<u32>) {
    let uv = (vec2<f32>(id.xy) + 0.5) / u.u_grid_size;
    let center = uv - vec2<f32>(0.5);
    let radius = length(center);
    if (radius < 0.15) {
        let dir = vec2<f32>(-center.y, center.x) / (radius + 1e-6);
        let strength = 0.01 * exp(-radius * 10.0) * cos(SYNC_PHASE + u.u_time * 0.58);
        let current = textureLoad(force_velocity_out, id.xy).xy;
        textureStore(force_velocity_out, id.xy, vec4<f32>(current + dir * strength, 0.0, 0.0));
    }
}

// ============================================================================
// 3. DIFFUSE
// ============================================================================
@group(1) @binding(0) var diff_current_in : texture_2d<f32>;
@group(1) @binding(1) var diff_current_out : texture_storage_2d<rgba32float, write>;

@compute @workgroup_size(8, 8)
fn diffuse(@builtin(global_invocation_id) id : vec3<u32>) {
    let center = textureLoad(diff_current_in, id.xy, 0).xy;
    let size = vec2<i32>(u.u_grid_size);
    let idx = vec2<i32>(id.xy);

    let left   = textureLoad(diff_current_in, vec2<i32>((idx.x - 1 + size.x) % size.x, idx.y), 0).xy;
    let right  = textureLoad(diff_current_in, vec2<i32>((idx.x + 1) % size.x, idx.y), 0).xy;
    let bottom = textureLoad(diff_current_in, vec2<i32>(idx.x, (idx.y - 1 + size.y) % size.y), 0).xy;
    let top    = textureLoad(diff_current_in, vec2<i32>(idx.x, (idx.y + 1) % size.y), 0).xy;

    let laplacian = left + right + bottom + top - 4.0 * center;
    let alpha = u.u_dt * u.u_viscosity / (u.u_texel_size.x * u.u_texel_size.x);
    let result = (center + alpha * laplacian) / (1.0 + 4.0 * alpha);
    textureStore(diff_current_out, id.xy, vec4<f32>(result, 0.0, 0.0));
}

// ============================================================================
// 4a. COMPUTE DIVERGENCE
// ============================================================================
@group(1) @binding(0) var div_velocity_in : texture_2d<f32>;
@group(1) @binding(1) var div_divergence_out : texture_storage_2d<r32float, write>;

@compute @workgroup_size(8, 8)
fn compute_divergence(@builtin(global_invocation_id) id : vec3<u32>) {
    let size = vec2<i32>(u.u_grid_size);
    let idx = vec2<i32>(id.xy);

    let u_right = textureLoad(div_velocity_in, vec2<i32>((idx.x + 1) % size.x, idx.y), 0).x;
    let u_left  = textureLoad(div_velocity_in, vec2<i32>((idx.x - 1 + size.x) % size.x, idx.y), 0).x;
    let v_top   = textureLoad(div_velocity_in, vec2<i32>(idx.x, (idx.y + 1) % size.y), 0).y;
    let v_bottom= textureLoad(div_velocity_in, vec2<i32>(idx.x, (idx.y - 1 + size.y) % size.y), 0).y;

    let div = (u_right - u_left + v_top - v_bottom) / (2.0 * max(u.u_texel_size.x, u.u_texel_size.y));
    textureStore(div_divergence_out, id.xy, vec4<f32>(div, 0.0, 0.0, 0.0));
}

// ============================================================================
// 4b. PRESSURE SOLVE
// ============================================================================
@group(1) @binding(0) var press_pressure_in : texture_2d<f32>;
@group(1) @binding(1) var press_divergence_in : texture_2d<f32>;
@group(1) @binding(2) var press_pressure_out : texture_storage_2d<r32float, write>;

@compute @workgroup_size(8, 8)
fn pressure_solve(@builtin(global_invocation_id) id : vec3<u32>) {
    let div = textureLoad(press_divergence_in, id.xy, 0).x;
    let size = vec2<i32>(u.u_grid_size);
    let idx = vec2<i32>(id.xy);

    let left   = textureLoad(press_pressure_in, vec2<i32>((idx.x - 1 + size.x) % size.x, idx.y), 0).x;
    let right  = textureLoad(press_pressure_in, vec2<i32>((idx.x + 1) % size.x, idx.y), 0).x;
    let bottom = textureLoad(press_pressure_in, vec2<i32>(idx.x, (idx.y - 1 + size.y) % size.y), 0).x;
    let top    = textureLoad(press_pressure_in, vec2<i32>(idx.x, (idx.y + 1) % size.y), 0).x;

    // We use -div here as it matches typical Stam's stable fluids for convergence.
    // The prompt used 'div' but with typical poisson it is negative.
    let pressure = (-div + left + right + bottom + top) / 4.0;
    textureStore(press_pressure_out, id.xy, vec4<f32>(pressure, 0.0, 0.0, 0.0));
}

// ============================================================================
// 4c. SUBTRACT PRESSURE GRADIENT
// ============================================================================
@group(1) @binding(0) var sub_pressure_in : texture_2d<f32>;
@group(1) @binding(1) var sub_velocity_out : texture_storage_2d<rgba32float, read_write>;

@compute @workgroup_size(8, 8)
fn subtract_pressure_gradient(@builtin(global_invocation_id) id : vec3<u32>) {
    let size = vec2<i32>(u.u_grid_size);
    let idx = vec2<i32>(id.xy);

    let right = textureLoad(sub_pressure_in, vec2<i32>((idx.x + 1) % size.x, idx.y), 0).x;
    let left  = textureLoad(sub_pressure_in, vec2<i32>((idx.x - 1 + size.x) % size.x, idx.y), 0).x;
    let top   = textureLoad(sub_pressure_in, vec2<i32>(idx.x, (idx.y + 1) % size.y), 0).x;
    let bottom= textureLoad(sub_pressure_in, vec2<i32>(idx.x, (idx.y - 1 + size.y) % size.y), 0).x;

    let grad = vec2<f32>(right - left, top - bottom) / (2.0 * max(u.u_texel_size.x, u.u_texel_size.y));
    var vel = textureLoad(sub_velocity_out, id.xy).xy;
    vel -= grad;
    textureStore(sub_velocity_out, id.xy, vec4<f32>(vel, 0.0, 0.0));
}

// ============================================================================
// 5. VISUALIZATION (RENDER)
// ============================================================================
struct VertexOutput {
    @builtin(position) pos: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@vertex
fn vs_main(@builtin(vertex_index) vi: u32) -> VertexOutput {
    var out: VertexOutput;
    let x = f32(i32(vi % 2u) * 2 - 1);
    let y = f32(i32(vi / 2u) * 2 - 1);
    out.pos = vec4(x, y, 0.0, 1.0);
    out.uv = vec2(x * 0.5 + 0.5, y * 0.5 + 0.5);
    return out;
}

@group(1) @binding(0) var render_velocity_texture : texture_2d<f32>;

@fragment
fn fluid_visualizer(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
    let vel = textureSampleLevel(render_velocity_texture, samp, uv, 0.0).xy;
    let speed = length(vel);
    let angle = atan2(vel.y, vel.x) + speed * 2.0 * SYNC_PHASE;
    let gold = vec3<f32>(2.0, 1.5, 0.8);
    let blue = vec3<f32>(0.2, 0.5, 1.2);
    let color = mix(blue, gold, speed * 5.0);
    return vec4<f32>(color * (0.5 + 0.5 * speed), 1.0);
}
