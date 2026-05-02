// ARKHE OS v∞.371.1 — Fragment Shader Expandido
// Coerência F181 real + Carga topológica no buffer

precision highp float;

uniform float uTime;
uniform int uMode;        // 0=structural, 1=F181, 2=λ-locked, 3=full
uniform float uLambda;    // 3722/2705 = 1.3759704251
uniform float uOmega;     // 19.686678 (não 19.73!)
uniform float uCaptureThreshold;
uniform float uDilutionThreshold;

// Varyings passed from vertex shader (formerly attributes)
varying float vType;      // 0 or 1
varying float vLayer;     // 0-15
varying float vQ;         // 0-255
varying float vR;         // 0-255
varying float vTopCharge; // 0-15 (4 bits)
varying float vPhase;     // 0-180 (8 bits) - Sensor readings

// Removed varying output assignments to avoid l-value errors in standard WebGL 1.0/2.0 fragment shaders.
// Normally you output to gl_FragColor.

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

// P1: Substituir fase observada simulada por leitura de sensores físicos
// vPhase holds the observed phase

float coherence(float t, float q, float r, float layer, float tc, float phase_obs) {
    float psi_pred = phasePredicted(t, r, tc);

    // Circular distance in Z/181Z
    float diff = abs(psi_pred - phase_obs);
    diff = min(diff, MODULUS - diff);

    // Normalize: 0 = perfect, 90.5 = opposite
    return clamp(1.0 - diff / 90.5, 0.0, 1.0);
}

float regime(float coherence) {
    // P2: Calibrar thresholds com dados experimentais
    if (coherence >= uCaptureThreshold) return 1.0;  // CAPTURE
    if (coherence <= uDilutionThreshold) return 0.0;  // DILUTION
    return 0.5;                                       // TRANSITION
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
    // Simplified HSV to RGB for WebGL
    float c = 0.8 * 0.9;
    float x = c * (1.0 - abs(mod(hue * 6.0, 2.0) - 1.0));
    float m = 0.9 - c;
    vec3 rgb;
    if (hue < 1.0/6.0) rgb = vec3(c, x, 0.0);
    else if (hue < 2.0/6.0) rgb = vec3(x, c, 0.0);
    else if (hue < 3.0/6.0) rgb = vec3(0.0, c, x);
    else if (hue < 4.0/6.0) rgb = vec3(0.0, x, c);
    else if (hue < 5.0/6.0) rgb = vec3(x, 0.0, c);
    else rgb = vec3(c, 0.0, x);
    vec3 hsv_rgb = rgb + vec3(m);

    // Squeezing = bright, Dilution = dim
    float brightness = isSqueezing(topCharge) ? 1.0 : 0.4;
    return hsv_rgb * brightness;
}

vec3 colorLambdaLocked(float t, float r, float tc) {
    // Mode 2: λ-locked temporal
    float psi = uOmega * log(max(t + tc, 1e-10)) * r / R_MAX;
    float hue = mod(psi, 1.0);

    float c = 0.6 * 0.8;
    float x = c * (1.0 - abs(mod(hue * 6.0, 2.0) - 1.0));
    float m = 0.8 - c;
    vec3 rgb;
    if (hue < 1.0/6.0) rgb = vec3(c, x, 0.0);
    else if (hue < 2.0/6.0) rgb = vec3(x, c, 0.0);
    else if (hue < 3.0/6.0) rgb = vec3(0.0, c, x);
    else if (hue < 4.0/6.0) rgb = vec3(0.0, x, c);
    else if (hue < 5.0/6.0) rgb = vec3(x, 0.0, c);
    else rgb = vec3(c, 0.0, x);
    return rgb + vec3(m);
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

    // Calculate real coherence using observed phase from sensors
    float coh = coherence(uTime, vQ, vR, vLayer, tc, vPhase);
    float reg = regime(coh);

    // Select color based on mode
    vec3 color;
    if (uMode == 0) {
        color = colorStructural(vType, vLayer);
    } else if (uMode == 1) {
        color = colorF181(vPhase, vTopCharge);
    } else if (uMode == 2) {
        color = colorLambdaLocked(uTime, vR, tc);
    } else {
        color = colorFullCoherence(coh, reg);
    }

    gl_FragColor = vec4(color, 1.0);
}
