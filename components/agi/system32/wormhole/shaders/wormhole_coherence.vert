// wormhole_coherence.vert — Vertex Shader para WORMHOLE.agi
#version 450 core

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec2 a_texcoord;

out vec2 v_texcoord;
out float v_depth;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform float u_phi_coherence;  // Para ajustar geometria baseado em coerência
uniform float u_time;           // Tempo global

void main() {
    // Posição base
    vec4 pos = vec4(a_position, 1.0);

    // Ajuste sutil de vértices baseado em Φ_C (para "pulsar" a garganta)
    if (u_phi_coherence > 0.8) {
        // Alta coerência: garganta mais estável, menos distorção
        pos.xy *= 0.98 + 0.02 * sin(u_time * 5.0);
    } else if (u_phi_coherence < 0.5) {
        // Baixa coerência: garganta mais instável, mais oscilação
        pos.xy *= 0.95 + 0.1 * sin(u_time * 10.0);
    }

    // Aplicar transformação de modelo/visão/projeção
    gl_Position = u_projection * u_view * u_model * pos;

    // Passar coordenadas de textura para fragment shader
    v_texcoord = a_texcoord;

    // Profundidade para efeitos de pós-processamento
    v_depth = gl_Position.z / gl_Position.w;
}
