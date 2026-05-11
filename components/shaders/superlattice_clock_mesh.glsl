#version 450

// Superlattice Clock Mesh Shader Fragment - ARKHE OS v∞.371
// (Recreation to include Entry 991: uMode == 4.0 for Torsion Phonon Topological Coherence Transport)

uniform float uMode;
uniform float uTime;
uniform float uOmega;
uniform float uOmegaVacuum;

in float vLayer;
in float vType;
in float emission_time; // Provided by Vertex Shader for pulsing

out vec4 fragColor;

void main() {
    vec3 baseColor = vec3(1.0);

    // Modes 1 to 3 logic omitted for brevity in this excerpt.
    // ...

    if (uMode == 4.0) {
        // Torsion Phonon Visualization
        // Highlight struts where resonance condition is satisfied

        float omega_inst = uOmega / (uTime + 5.0);  // ω_Δ/(t+t_c)
        float resonance = smoothstep(0.0, 0.01, 1.0 - abs(omega_inst - uOmegaVacuum));

        // Color by phonon charge (if emitted)
        if (resonance > 0.5) {
            // Emission event: color by charge sign
            float charge_sign = sin(vLayer * 0.5 + uTime);  // Pseudo-random ±1
            baseColor = charge_sign > 0.0
                ? vec3(0.0, 1.0, 0.5)   // Q_τ = +1: green-cyan
                : vec3(1.0, 0.0, 0.5);  // Q_τ = -1: magenta
        } else {
            // No emission: structural color
            baseColor = vType < 0.5 ? vec3(0.3, 0.1, 0.6) : vec3(0.1, 0.2, 0.8);
        }

        // Add pulse animation at emission sites
        if (resonance > 0.5) {
            float pulse = 0.5 * (1.0 + sin(20.0 * (uTime - emission_time)));
            baseColor *= (1.0 + 0.5 * pulse);
        }
    }

    fragColor = vec4(baseColor, 1.0);
}
