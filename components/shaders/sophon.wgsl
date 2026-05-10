// Sophon Shader - Warped Fractal Sphere (WGSL)
// Parâmetros espelhados do GUI Three.js

struct Uniforms {
    time: f32,
    resolution: vec2<f32>,
    speed: f32,
    sphere_size: f32,
    warp_amp: f32,
    warp_falloff: f32,
    warp_freq: f32,
    warp_steps: f32,
    warp_velocity: f32,
    noise_contrast: f32,
    color1: vec3<f32>, // ex: #002aff -> (0.0, 0.164, 1.0)
    color2: vec3<f32>,
    color3: vec3<f32>,
};

@group(0) @binding(0) var<uniform> u: Uniforms;

// Função de ruído simplificada (hash 3D)
fn hash(p: vec3<f32>) -> f32 {
    let h = fract(sin(dot(p, vec3<f32>(127.1, 311.7, 74.7))) * 43758.5453);
    return h;
}

fn noise(p: vec3<f32>) -> f32 {
    let i = floor(p);
    let f = fract(p);
    let u = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(mix(hash(i+vec3<f32>(0.0,0.0,0.0)), hash(i+vec3<f32>(1.0,0.0,0.0)), u.x),
            mix(hash(i+vec3<f32>(0.0,1.0,0.0)), hash(i+vec3<f32>(1.0,1.0,0.0)), u.x), u.y),
        mix(mix(hash(i+vec3<f32>(0.0,0.0,1.0)), hash(i+vec3<f32>(1.0,0.0,1.0)), u.x),
            mix(hash(i+vec3<f32>(0.0,1.0,1.0)), hash(i+vec3<f32>(1.0,1.0,1.0)), u.x), u.y), u.z);
}

fn fbm(p: vec3<f32>) -> f32 {
    var value = 0.0;
    var amplitude = 1.0;
    var frequency = 1.0;
    for (var i = 0; i < 5; i++) {
        value += amplitude * noise(p * frequency);
        frequency *= 2.0;
        amplitude *= 0.5;
    }
    return value;
}

// Mapeamento da esfera deformada
fn map(p: vec3<f32>, t: f32) -> f32 {
    // Centro da esfera
    let center = vec3<f32>(0.0, 0.0, 0.0);
    // Distância até o centro (esfera base)
    var d = length(p - center) - u.sphere_size;

    // Deslocamento por warp (ruído fractal dependente do tempo)
    let warp_t = t * u.warp_velocity * u.speed;
    let warp_noise = fbm(p * u.warp_freq + vec3<f32>(warp_t));
    let displacement = warp_noise * u.warp_amp;

    // Aplicar envelope de falloff (mais deformação perto da superfície)
    let envelope = exp(-abs(d) * u.warp_falloff);
    d -= displacement * envelope;

    return d;
}

// Traçado de raio (ray marching)
fn ray_march(ro: vec3<f32>, rd: vec3<f32>, t: f32) -> vec4<f32> {
    var t_dist = 0.0;
    var hit = 0.0;
    var pos: vec3<f32>;
    var d: f32;
    let max_steps = i32(u.warp_steps);

    for (var i = 0; i < max_steps; i++) {
        pos = ro + rd * t_dist;
        d = map(pos, t);
        if (d < 0.001) {
            hit = 1.0;
            break;
        }
        t_dist += d;
        if (t_dist > 10.0) { break; }
    }

    if (hit == 0.0) { discard; }

    // Cálculo do normal via gradiente
    let eps = 0.001;
    let n = normalize(vec3<f32>(
        map(pos + vec3<f32>(eps, 0.0, 0.0), t) - map(pos - vec3<f32>(eps, 0.0, 0.0), t),
        map(pos + vec3<f32>(0.0, eps, 0.0), t) - map(pos - vec3<f32>(0.0, eps, 0.0), t),
        map(pos + vec3<f32>(0.0, 0.0, eps), t) - map(pos - vec3<f32>(0.0, 0.0, eps), t)
    ));

    // Cor baseada no normal e na profundidade
    let view_dir = normalize(ro - pos);
    let fresnel = 1.0 - abs(dot(n, view_dir));
    let depth = t_dist / 10.0;

    // Interpolação entre as três cores
    var col = mix(u.color1, u.color2, fresnel * 0.7 + depth * 0.3);
    col = mix(col, u.color3, fbm(pos * 2.0 + vec3<f32>(t * 0.2)) * 0.5);

    // Adicionar contraste de ruído nos realces
    let spec = pow(fresnel, 4.0) * fbm(pos * 3.0 + vec3<f32>(t * 0.1));
    col += vec3<f32>(spec * u.noise_contrast);

    return vec4<f32>(col, 1.0);
}

@fragment
fn fs_main(@builtin(position) coord: vec4<f32>) -> @location(0) vec4<f32> {
    let uv = (coord.xy / u.resolution) * 2.0 - 1.0;
    let aspect = u.resolution.x / u.resolution.y;

    // Câmera: posição fixa, olhando para a origem
    let ro = vec3<f32>(0.0, 0.0, 3.5);
    let rd = normalize(vec3<f32>(uv.x * aspect, uv.y, -1.0));

    let t = u.time * u.speed;
    return ray_march(ro, rd, t);
}
