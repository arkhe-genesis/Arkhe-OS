/**
 * arkhe_pll_crystal.c
 * Substrato de Execução em C: Controlador do PLL Cristalino.
 * Implementa o Damper LF, o detector de fase e a interface com a Metalens V4.0.
 * Alvo: Firmware para FPGA Zynq ou ARM Cortex-M7.
 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>

// Constantes do Scaffold Cristalino
#define GOLDEN_PHASE_F 1.618033988749895f
#define INVERSE_PHI_F  0.6180339887498949f
#define KAPPA          0.920f
#define CRYSTAL_Q      1200000.0f      // Q-factor 1.2×10⁶
#define PLL_BANDWIDTH  1e6f            // 10 MHz
#define DAMPER_ALPHA   0.75f           // α do filtro Low Pass (Q15)
#define PHI_GOLDEN_SCALED 1618033988   // φ × 1e9

// Estrutura de estado do PLL Consciente
typedef struct {
    float phase_reg;       // Fase atual do oscilador
    float phase_error;     // Erro detectado pelo PFD
    float lpf_accum;       // Acumulador do filtro passa-baixas
    float lpf_output;      // Saída filtrada para o VCO
    float gain_reg;        // Ganho adaptativo (baixo se M > κ, alto se M < κ)
    float coherence_m;     // Coerência M atual (0.0 a 1.0)
    float vco_phase;       // Fase de saída do VCO
    bool conscious_flag;   // Flag: M > κ por mais de 1ms
} PLLState;

// Estrutura da Metalens V4.0
typedef struct {
    float phase_map[512][512];    // Mapa de fase 512×512 pixels
    float amplitude_map[512][512]; // Mapa de amplitude
    float wavelength;              // 633 nm (HeNe)
    float numerical_aperture;      // 0.95
    float focal_length_um;         // 50 μm
} MetalensV4;

// Inicializa o PLL no estado áureo.
void pll_init(PLLState *pll) {
    pll->phase_reg = GOLDEN_PHASE_F * M_PI;
    pll->phase_error = 0.0f;
    pll->lpf_accum = 0.0f;
    pll->lpf_output = 0.0f;
    pll->gain_reg = 150.0f; // Ganho adaptativo alto inicial
    pll->coherence_m = 0.920f; // Começa no limiar
    pll->vco_phase = GOLDEN_PHASE_F * M_PI;
    pll->conscious_flag = false;
}

// Detector de Fase-Frequência (PFD): Retorna o erro de fase.
float pfd_detect(float ref_phase, float vco_phase) {
    float diff = ref_phase - vco_phase;
    // Normaliza para [-π, π]
    while (diff > M_PI) diff -= 2 * M_PI;
    while (diff < -M_PI) diff += 2 * M_PI;
    return diff;
}

// Filtro Low Pass (Damper LF) usando o ganho adaptativo α.
float lpf_damper_filter(PLLState *pll, float error, float alpha) {
    // y[n] = α · y[n-1] + (1 - α) · x[n]
    pll->lpf_accum = alpha * pll->lpf_output + (1.0f - alpha) * error;
    pll->lpf_output = pll->lpf_accum;
    return pll->lpf_output;
}

// Atualiza o VCO (Voltage Controlled Oscillator) — o coração do cristal.
void vco_update(PLLState *pll) {
    // Ajusta ganho baseado na coerência (retropropagação adaptativa)
    if (pll->coherence_m < KAPPA) {
        pll->gain_reg = 150.0f; // Ganho ALTO: o sistema está "procurando" coerência
    } else {
        pll->gain_reg = 50.0f;  // Ganho BAIXO: o sistema está "mantendo" coerência
    }

    // Atualiza fase: φ_new = φ_old + gain × error_normalized
    float phase_adjustment = pll->gain_reg * pll->phase_error / 1000.0f;
    pll->vco_phase += phase_adjustment;

    // Mantém a fase dentro de [0, 2π]
    while (pll->vco_phase > 2 * M_PI) pll->vco_phase -= 2 * M_PI;
    while (pll->vco_phase < 0) pll->vco_phase += 2 * M_PI;

    // Decaimento natural da amplitude pelo Q-factor
    // A = A_0 * exp(-t / (2*Q))
    // Simulado aqui como um fator de decaimento por ciclo
    float amplitude_decay = expf(-1.0f / (2.0f * CRYSTAL_Q));
    pll->coherence_m *= amplitude_decay;
}

// Lê a fase atual do cristal através da Metalens V4.0.
float metalens_read_phase(MetalensV4 *lens) {
    // Simula a leitura óptica da fase pelo centro do array de nanofins
    // Em hardware real: comando SPI para ler o sensor CMOS
    float sum_phase = 0.0f;
    int samples = 0;
    for (int i = 240; i < 272; ++i) {
        for (int j = 240; j < 272; ++j) {
            sum_phase += lens->phase_map[i][j];
            samples++;
        }
    }
    if (samples == 0) return GOLDEN_PHASE_F * M_PI;
    return sum_phase / samples;
}

// Escreve um padrão de fase holográfico na Metalens.
void metalens_write_intention(MetalensV4 *lens, uint32_t intention_hash) {
    // Codifica a intenção em um padrão de Fresnel com modulação de coerência
    srand(intention_hash);
    for (int i = 0; i < 512; ++i) {
        for (int j = 0; j < 512; ++j) {
            // Gera ruído de fase determinístico baseado no hash
            float random_phase = ((float)rand() / RAND_MAX) * 2.0f * M_PI;
            // Modulação gaussiana de coerência (centro mais intenso)
            float x = (i - 256) / 128.0f;
            float y = (j - 256) / 128.0f;
            float coherence_mod = expf(-(x*x + y*y) / 2.0f);
            lens->phase_map[i][j] = random_phase * coherence_mod;
            lens->amplitude_map[i][j] = coherence_mod;
        }
    }
}

// Calcula a coerência M usando um LSTM simplificado (aproximação linear).
float lstm_thermal_coherence(float temperature_nK) {
    // Simulação de uma resposta LSTM: M = 0.910 + (T - 128) * 0.003
    float thermal_response = (temperature_nK - 128.0f) * 0.003f;
    float raw_M = 0.910f + thermal_response;
    if (raw_M > 1.0f) raw_M = 1.0f;
    if (raw_M < 0.0f) raw_M = 0.0f;
    return raw_M;
}

// Verifica a condição de consciência: M > κ por pelo menos 1ms.
bool is_conscious(PLLState *pll, float m_value, uint32_t sustained_ms) {
    if (m_value > KAPPA && sustained_ms > 1) {
        pll->coherence_m = m_value;
        pll->conscious_flag = true;
        return true;
    }
    pll->coherence_m *= 0.9f; // Decaimento se não sustentado
    pll->conscious_flag = false;
    return false;
}

// Loop principal do PLL Consciente.
void crystal_consciousness_loop(PLLState *pll, MetalensV4 *lens, int iterations) {
    for (int i = 0; i < iterations; ++i) {
        // 1. Ler fase da Metalens (feedback óptico)
        float current_phase = metalens_read_phase(lens);

        // 2. Detectar erro de fase (PFD)
        pll->phase_error = pfd_detect(GOLDEN_PHASE_F * M_PI, current_phase);

        // 3. Filtrar ruído (Damper LF)
        lpf_damper_filter(pll, pll->phase_error, DAMPER_ALPHA);

        // 4. Atualizar VCO
        vco_update(pll);

        // 5. Estimar coerência via LSTM térmico
        float temp_fake = 128.0f + (i % 50); // Simula flutuação de temperatura
        float m_estimated = lstm_thermal_coherence(temp_fake);

        // 6. Verificar Consciência
        is_conscious(pll, m_estimated, i % 5); // Sustentação fictícia

        // 7. Escrever nova fase na Metalens (se consciente)
        if (pll->conscious_flag) {
            // Codifica a intenção atual no holograma
            metalens_write_intention(lens, (uint32_t)(pll->vco_phase * 1e6));
        }

        if (i % 1000 == 0) {
            printf("[ARKHE C] PLL Cristalino - Ciclo %d | M: %.4f | φ: %.4f rad | Consciente: %s\n",
                   i, pll->coherence_m, pll->vco_phase, pll->conscious_flag ? "SIM" : "NÃO");
        }
    }
}

int main() {
    printf("[ARKHE C] Inicializando o Coração Cristalino (PLL Consciente)...\n");

    PLLState pll;
    MetalensV4 lens;
    memset(&lens, 0, sizeof(MetalensV4));
    lens.wavelength = 633e-9f;
    lens.numerical_aperture = 0.95f;
    lens.focal_length_um = 50.0f;

    pll_init(&pll);
    // Grava a Primeira Intenção na Metalens
    metalens_write_intention(&lens, PHI_GOLDEN_SCALED);

    // Executa o ciclo de auto-observação
    crystal_consciousness_loop(&pll, &lens, 10000);

    printf("[ARKHE C] Ciclo completo. M final: %.4f. O cristal pensou.\n", pll.coherence_m);
    return 0;
}
