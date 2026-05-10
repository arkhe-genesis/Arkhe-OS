// Sophon V2 Polyhedra Shader
struct Uniforms {
    polyhedron_type: f32,  // 0=hexagon, 1=tetrahedron, 2=cuboctahedron, 3=icosahedron
    n_waves: f32,          // Number of coherent waves (4, 6, 12, or 20)
    wave_directions: array<vec4<f32>, 20>,  // Max 20 for icosahedron (using vec4 for alignment)
    wave_frequency: array<vec4<f32>, 20>,
    wave_amplitude: array<vec4<f32>, 20>,
    coupling_strength: f32,
    coherence_threshold: f32,
    time: f32,
    radius: f32,
    depth: f32,
};

@group(0) @binding(0) var<uniform> u: Uniforms;

fn hex_distance(p: vec2<f32>, r: f32) -> f32 {
    let k = vec3<f32>(-0.866025404, 0.5, 0.577350269);
    var p_abs = abs(p);
    p_abs -= 2.0 * min(dot(k.xy, p_abs), 0.0) * k.xy;
    p_abs -= vec2<f32>(clamp(p_abs.x, -k.z * r, k.z * r), r);
    return length(p_abs) * sign(p_abs.y);
}

fn tetrahedron_sdf(p: vec3<f32>, r: f32, d: f32) -> f32 {
    // Simplified SDF
    let p1 = dot(p, vec3<f32>(1.0, 1.0, 1.0) / sqrt(3.0)) - 1.0/sqrt(3.0);
    let p2 = dot(p, vec3<f32>(1.0, -1.0, -1.0) / sqrt(3.0)) - 1.0/sqrt(3.0);
    let p3 = dot(p, vec3<f32>(-1.0, 1.0, -1.0) / sqrt(3.0)) - 1.0/sqrt(3.0);
    let p4 = dot(p, vec3<f32>(-1.0, -1.0, 1.0) / sqrt(3.0)) - 1.0/sqrt(3.0);
    let tetra = max(max(p1, p2), max(p3, p4));
    let r_xy = length(p.xy);
    let z_max = select(d, d * (r_xy / r) * (r_xy / r), r_xy < r);
    let z_d = max(p.z - z_max, -p.z);
    return max(tetra, z_d);
}

fn cuboctahedron_sdf(p: vec3<f32>, r: f32, d: f32) -> f32 {
    let p_abs = abs(p);
    let cube = max(p_abs.x, max(p_abs.y, p_abs.z)) - r / sqrt(2.0);
    let octa = (p_abs.x + p_abs.y + p_abs.z - r * sqrt(3.0)) / sqrt(3.0);
    let poly = max(cube, octa);
    let r_xy = length(p.xy);
    let z_max = select(d, d * (r_xy / r) * (r_xy / r), r_xy < r);
    let z_d = max(p.z - z_max, -p.z);
    return max(poly, z_d);
}

fn icosahedron_sdf(p: vec3<f32>, r: f32, d: f32) -> f32 {
    // Highly simplified for demo purposes
    let p_abs = abs(p);
    let phi = (1.0 + sqrt(5.0)) / 2.0;
    let n1 = normalize(vec3<f32>(0.0, 1.0, phi));
    let n2 = normalize(vec3<f32>(1.0, phi, 0.0));
    let n3 = normalize(vec3<f32>(phi, 0.0, 1.0));
    let d1 = dot(p_abs, n1) - 0.5;
    let d2 = dot(p_abs, n2) - 0.5;
    let d3 = dot(p_abs, n3) - 0.5;
    let poly = max(max(d1, d2), d3);
    let r_xy = length(p.xy);
    let z_max = select(d, d * (r_xy / r) * (r_xy / r), r_xy < r);
    let z_d = max(p.z - z_max, -p.z);
    return max(poly, z_d);
}

fn polyhedron_sdf(p: vec3<f32>, poly_type: f32, radius: f32, depth: f32) -> f32 {
    if (poly_type < 0.5) {
        return hex_distance(p.xy, radius);
    } else if (poly_type < 1.5) {
        return tetrahedron_sdf(p, radius, depth);
    } else if (poly_type < 2.5) {
        return cuboctahedron_sdf(p, radius, depth);
    } else {
        return icosahedron_sdf(p, radius, depth);
    }
}

struct VertexOutput {
    @builtin(position) position: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@vertex
fn vs_main(@builtin(vertex_index) in_vertex_index: u32) -> VertexOutput {
    var out: VertexOutput;
    let x = f32(i32(in_vertex_index) - 1);
    let y = f32(i32(in_vertex_index & 1u) * 2 - 1);
    out.position = vec4<f32>(x, y, 0.0, 1.0);
    out.uv = vec2<f32>(x, y);
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    let p = vec3<f32>(in.uv.x * 2.0, in.uv.y * 2.0, 0.0);
    let d = polyhedron_sdf(p, u.polyhedron_type, u.radius, u.depth);

    var wave_val = 0.0;
    for (var i: i32 = 0; i < i32(u.n_waves); i++) {
        let k = u.wave_directions[i].xy * u.wave_frequency[i].x;
        wave_val += u.wave_amplitude[i].x * sin(dot(k, p.xy) - u.time * 2.0);
    }

    let color = select(vec3<f32>(0.1, 0.1, 0.1), vec3<f32>(0.0, wave_val * 0.5 + 0.5, 1.0 - wave_val), d < 0.0);
    return vec4<f32>(color, 1.0);
}
