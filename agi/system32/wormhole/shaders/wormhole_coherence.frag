// wormhole_coherence.frag — Advanced GLSL Shader for WORMHOLE.agi
// Substrate 324.1: Visual Coherence Rendering
#version 450 core

// Uniforms injetados pelo runtime AGI
uniform float u_time;                 // Tempo global (segundos)
uniform float u_phi_coherence;        // Valor atual de Φ_C [0,1]
uniform vec3 u_garganta_center;       // Centro da garganta no espaço 3D
uniform float u_garganta_radius;      // Raio da garganta
uniform float u_retrocausal_strength; // Força do efeito retrocausal [0,1]
uniform int u_lod_level;              // Nível de detalhe (0=high, 3=low)
uniform sampler2D texture0;           // Textura base

// Outputs
layout(location = 0) out vec4 frag_color;

// Constantes para mapeamento de coerência
const vec3 COLOR_LOW_COH = vec3(0.2, 0.2, 0.8);   // Azul para baixa coerência
const vec3 COLOR_HIGH_COH = vec3(0.9, 0.2, 0.2);  // Vermelho para alta coerência
const float MIN_DISTORTION = 0.01;
const float MAX_DISTORTION = 0.15;

// Função de suavização temporal para evitar flicker
float temporal_smooth(float current_value, float prev_value, float alpha) {
    return mix(prev_value, current_value, alpha);
}

// Mapeamento Φ_C → cor em espaço HSV
vec3 coherence_to_color(float phi) {
    // Hue: 240° (azul) → 0° (vermelho) conforme Φ_C aumenta
    float hue = 240.0 * (1.0 - phi);
    float saturation = 0.8 + 0.2 * phi;
    float value = 0.6 + 0.4 * phi;

    // Converter HSV → RGB
    float h = hue / 60.0;
    float i = floor(h);
    float f = h - i;
    float p = value * (1.0 - saturation);
    float q = value * (1.0 - saturation * f);
    float t = value * (1.0 - saturation * (1.0 - f));

    if (i == 0.0) return vec3(value, t, p);
    if (i == 1.0) return vec3(q, value, p);
    if (i == 2.0) return vec3(p, value, t);
    if (i == 3.0) return vec3(p, q, value);
    if (i == 4.0) return vec3(t, p, value);
    return vec3(value, p, q); // i == 5
}

// Distorção baseada em gradiente de coerência (simulado)
vec2 apply_curvature_distortion(vec2 uv, float phi, vec2 frag_coord) {
    // Simular gradiente de Φ_C radialmente a partir do centro
    vec2 to_center = uv - vec2(0.5, 0.5);
    float dist = length(to_center);

    // Gradiente simulado: maior perto das bordas da garganta
    float gradient_magnitude = smoothstep(0.0, 1.0, dist) * (1.0 - phi);

    // Aplicar distorção proporcional ao gradiente
    float distortion = mix(MIN_DISTORTION, MAX_DISTORTION, gradient_magnitude);
    vec2 distortion_vec = normalize(to_center) * distortion * sin(u_time * 2.0);

    return uv + distortion_vec;
}

// Partículas retrocausais: movimento "para trás no tempo"
vec3 generate_retrocausal_particles(vec2 uv, float phi, float time) {
    vec3 particle_color = vec3(0.0);

    // Parâmetros de partículas (adaptativos por LOD)
    int num_particles = u_lod_level == 0 ? 64 : (u_lod_level == 1 ? 32 : 16);
    float particle_size = u_lod_level == 0 ? 0.02 : (u_lod_level == 1 ? 0.04 : 0.08);

    for (int i = 0; i < num_particles; i++) {
        // Seed determinística por índice de partícula
        float seed = float(i) * 12.9898 + 78.233;
        float rand = fract(sin(seed) * 43758.5453);

        // Posição base da partícula (círculo ao redor da garganta)
        float angle = rand * 6.28318;
        float radius = u_garganta_radius * (0.8 + 0.4 * rand);
        vec2 base_pos = vec2(cos(angle), sin(angle)) * radius;

        // Movimento retrocausal: oscilação com fase invertida no tempo
        float retro_phase = sin(3.0 * (10.0 - time) + rand * 6.28318);
        vec2 offset = vec2(cos(angle + retro_phase), sin(angle + retro_phase)) * 0.1;

        // Posição final da partícula
        vec2 particle_pos = base_pos + offset;

        // Transformar para o espaço UV ([0,1]) assumindo garganta no centro
        vec2 particle_uv = vec2(0.5) + particle_pos;

        // Verificar se fragmento atual está sobre a partícula
        float dist_to_particle = distance(uv, particle_uv);
        if (dist_to_particle < particle_size) {
            // Intensidade da partícula baseada em Φ_C e proximidade
            float intensity = (1.0 - dist_to_particle / particle_size) * phi * u_retrocausal_strength;
            // Cor da partícula: branco com toque de ciano para efeito quântico
            vec3 particle_col = vec3(0.8, 1.0, 1.0) * intensity;
            particle_color += particle_col;
        }
    }

    return particle_color;
}

// Função principal de fragmento
void main() {
    // Coordenadas de textura normalizadas [0,1]
    ivec2 texSize = textureSize(texture0, 0);
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 uv = vec2(fragCoord.x / float(texSize.x), fragCoord.y / float(texSize.y));

    // Aplicar distorção de curvatura baseada em Φ_C
    vec2 distorted_uv = apply_curvature_distortion(uv, u_phi_coherence, gl_FragCoord.xy);

    // Amostrar cor base (poderia ser textura da garganta, gradiente, etc.)
    vec3 base_color = coherence_to_color(u_phi_coherence);

    // Adicionar partículas retrocausais
    vec3 particle_color = generate_retrocausal_particles(distorted_uv, u_phi_coherence, u_time);

    // Combinar cores: base + partículas (com blend aditivo)
    vec3 final_color = base_color + particle_color;

    // Aplicar vinheta suave nas bordas para foco na garganta
    float vignette = 1.0 - smoothstep(0.0, 1.0, length(uv - vec2(0.5)) * 1.5);
    final_color *= vignette;

    // Output final com alpha = 1.0 (opaco)
    frag_color = vec4(final_color, 1.0);
}
