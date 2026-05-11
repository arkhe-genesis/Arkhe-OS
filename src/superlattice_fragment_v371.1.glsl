// ARKHE OS v∞.371.1 — Fragment Shader Expandido
// Coerência F181 real + Carga topológica no buffer

precision highp float;

uniform float uTime;
uniform int uMode;        // 0=structural, 1=F181, 2=λ-locked, 3=full
uniform float uLambda;    // 3722/2705 = 1.3759704251
uniform float uOmega;     // 19.686678 (não 19.73!)

// Instanced attributes (from expanded buffer)
attribute float aType;      // 0 or 1
attribute float aLayer;     // 0-15
attribute float aQ;         // 0-255
attribute float aR;         // 0-255
attribute float aTopCharge; // 0-15 (4 bits)
attribute float aPhase;     // 0-180 (8 bits)

varying vec3 vColor;
varying float vCoherence;
varying float vRegime;      // 0=dilution, 1=capture, 0.5=transition

const float PI = 3.141592653589793;
const float MODULUS = 181.0;
const float R_MAX = 8.0;

// ============================================================
// F181 Phase Functions
// ============================================================

float phasePredicted(float t, float r, float tc) {
    // ψ(t, r) = ω_Δ · ln(t + t_c) · r / R_max  (mod 181)
    float safe_t = max(t + tc, 1e-10);
    float psi = uOmega * log(safe_t) * r / R_MAX;
    return mod(floor(psi), MODULUS);
}

float phaseObserved(float q, float r, float layer) {
    // ψ_obs = (q + 2r + 3*layer) mod 181
    return mod(q + 2.0*r + 3.0*layer, MODULUS);
}

float coherence(float t, float q, float r, float layer, float tc) {
    float psi_pred = phasePredicted(t, r, tc);
    float psi_obs = phaseObserved(q, r, layer);

    // Circular distance in Z/181Z
    float diff = abs(psi_pred - psi_obs);
    diff = min(diff, MODULUS - diff);

    // Normalize: 0 = perfect, 90.5 = opposite
    return clamp(1.0 - diff / 90.5, 0.0, 1.0);
}

float regime(float coherence) {
    if (coherence >= 0.85) return 1.0;  // CAPTURE
    if (coherence <= 0.15) return 0.0;  // DILUTION
    return 0.5;                          // TRANSITION
}

// ============================================================
// Topological Charge Classification
// ============================================================

bool isSqueezing(float topCharge) {
    return topCharge >= 8.0;
}

bool isDilution(float topCharge) {
    return topCharge < 8.0;
}

// ============================================================
// Color Mapping
// ============================================================

vec3 colorStructural(float type, float layer) {
    // Mode 0: Crystal structure
    vec3 aln = vec3(0.05, 0.05, 0.15);   // AlN: deep blue
    vec3 gan = vec3(0.0, 0.6, 0.3);      // GaN: green
    vec3 nbtin = vec3(0.8, 0.8, 0.9);    // NbTiN: silver

    vec3 base = mix(aln, gan, type);
    return mix(base, nbtin, layer / 15.0);
}

vec3 colorF181(float phase, float topCharge) {
    // Mode 1: F181 phase
    float hue = phase / 180.0;
    vec3 hsv = vec3(hue, 0.8, 0.9);

    // Squeezing = bright, Dilution = dim
    float brightness = isSqueezing(topCharge) ? 1.0 : 0.4;
    return hsv * brightness;
}

vec3 colorLambdaLocked(float t, float r, float tc) {
    // Mode 2: λ-locked temporal
    float psi = uOmega * log(max(t + tc, 1e-10)) * r / R_MAX;
    float hue = mod(psi, 1.0);
    return vec3(hue, 0.6, 0.8);
}

vec3 colorFullCoherence(float coherence, float regime) {
    // Mode 3: Full coherence
    if (regime > 0.8) return vec3(0.0, 1.0, 0.0);   // CAPTURE: green
    if (regime < 0.2) return vec3(1.0, 0.0, 0.0);   // DILUTION: red
    return vec3(1.0, 1.0, 0.0);                      // TRANSITION: yellow
}

// ============================================================
// Main
// ============================================================

void main() {
    float tc = 0.0;  // collapse time offset (configurable)

    // Calculate real coherence
    float coh = coherence(uTime, aQ, aR, aLayer, tc);
    float reg = regime(coh);

    // Select color based on mode
    vec3 color;
    if (uMode == 0) {
        color = colorStructural(aType, aLayer);
    } else if (uMode == 1) {
        color = colorF181(aPhase, aTopCharge);
    } else if (uMode == 2) {
        color = colorLambdaLocked(uTime, aR, tc);
    } else {
        color = colorFullCoherence(coh, reg);
    }

    vColor = color;
    vCoherence = coh;
    vRegime = reg;

    gl_FragColor = vec4(color, 1.0);
}
