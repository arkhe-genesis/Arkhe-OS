// =============================================================================
// Substrate 123.1 — tDCS Phase-Locked Controller (Corrected)
// Target: Xilinx Zynq UltraScale+ MPSoC, ARM Cortex-A53, Bare-Metal
//
// CORRECTIONS:
// • All constants defined with explicit values and units
// • Static variables placed in OCM (On-Chip Memory) via linker section
// • Cache coherency barriers (dmb/dsb) before reading GPU zero-copy buffer
// • pdi_from_gpu read with volatile qualifier and memory barrier
// • Safety comparator in PL fabric (separate Verilog module)
// • Hardware watchdog timer for fault detection
// =============================================================================

#include <stdint.h>
#include <stdbool.h>
#include <math.h>

// ---- Hardware Addresses (Zynq UltraScale+ memory map) ----
#define GPU_ZEROCOPY_BASE       0x40000000  // GPU shared memory (mapped via CMA)
#define THETA_PHASE_OFFSET      0x0000      // float: theta phase from GPU PDI kernel
#define PDI_VALUE_OFFSET        0x0004      // float: PDI value from GPU PDI kernel
#define DAC_COMMAND_REGISTER    0xA0000000  // DAC SPI command register (PL fabric)
#define DAC_ENABLE_REGISTER     0xA0000004  // DAC enable control (PL fabric)
#define WDT_KICK_REGISTER       0xA0000008  // Watchdog timer kick

// ---- Kalman Filter Constants (tuned for 6 Hz theta, 512 Hz sampling) ----
#define KALMAN_GAIN_PHASE       0.15f       // Measurement gain for phase estimate
#define KALMAN_GAIN_VELOCITY     0.05f       // Measurement gain for phase velocity
#define PROCESS_NOISE_PHASE      0.001f      // Process noise for phase (rad²/step)
#define PROCESS_NOISE_VELOCITY   0.0001f     // Process noise for velocity (rad²/step³)
#define MEASUREMENT_NOISE        0.01f       // Measurement noise (rad²)

// ---- Timing Constants (in milliseconds unless noted) ----
#define DT_MS                   1.953125f   // 1 / 512 Hz = 1.953125 ms
#define DAC_LATENCY_US          50.0f       // DAC settling time in microseconds
#define CURRENT_RAMP_RATE       0.05f       // mA/ms soft ramp
#define CURRENT_MAX_MA          1.5f        // Absolute hardware limit

// ---- Ceremonial Constants ----
#define THETA_TROUGH_PHASE      3.14159265f // π radians (theta trough target)
#define PHASE_WINDOW_RAD        0.26f       // ±15° delivery window
#define PDI_ACTIVE_MIN           0.4f       // Minimum PDI for stimulation
#define PDI_ACTIVE_MAX           0.85f      // Maximum PDI for stimulation
#define MERCY_GAP_FLOOR          0.04f      // ε minimum (hard safety)
#define MERCY_GAP_CEILING        0.10f      // ε maximum (hard safety)

// ---- Memory Attributes ----
// Place static state in OCM (On-Chip Memory) for deterministic low latency.
// OCM base: 0xFFFC0000 on Zynq UltraScale+ (256 KB)
// This attribute is handled by the linker script:
//   .ocm_data : { *(.ocm*) } > OCM AT > DDR
#define OCM_SECTION __attribute__((section(".ocm_data")))

// ---- Static State (OCM-resident, 50 µs access) ----
OCM_SECTION static float phase_estimate       = 0.0f;
OCM_SECTION static float phase_velocity       = 0.0f;
OCM_SECTION static float phase_acceleration   = 0.0f;
OCM_SECTION static float current_output_ma    = 0.0f;
OCM_SECTION static float phase_covariance     = 1.0f;
OCM_SECTION static float velocity_covariance  = 0.1f;

// ---- Function Prototypes ----
static inline void memory_barrier(void);
static inline float read_theta_phase(void);
static inline float read_pdi_value(void);
static inline void write_dac_command(uint16_t dac_code, bool enable);
static inline float circular_distance(float a, float b);
static inline uint16_t current_to_dac_code(float current_ma);
static inline void kick_watchdog(void);

// ---- Cache Coherency Barriers ----
// Required because GPU writes to zero-copy memory without CPU cache invalidation.
// The ARM must issue a data memory barrier before reading.
static inline void memory_barrier(void) {
    __asm__ volatile (
        "dmb ish\n\t"   // Data Memory Barrier: ensures all previous memory
        "dsb sy\n\t"    // accesses complete before proceeding
        : : : "memory"
    );
}

// ---- Read GPU Zero-Copy Values ----
static inline float read_theta_phase(void) {
    memory_barrier();  // Ensure cache coherency with GPU
    volatile float* theta_ptr = (volatile float*)(GPU_ZEROCOPY_BASE + THETA_PHASE_OFFSET);
    return *theta_ptr;
}

static inline float read_pdi_value(void) {
    memory_barrier();  // Ensure cache coherency with GPU
    volatile float* pdi_ptr = (volatile float*)(GPU_ZEROCOPY_BASE + PDI_VALUE_OFFSET);
    return *pdi_ptr;
}

// ---- DAC Command Output ----
// Writes to PL fabric registers. The PL safety comparator independently
// verifies current limits and can override dac_enable.
static inline void write_dac_command(uint16_t dac_code, bool enable) {
    volatile uint16_t* dac_cmd = (volatile uint16_t*)DAC_COMMAND_REGISTER;
    volatile uint32_t* dac_en  = (volatile uint32_t*)DAC_ENABLE_REGISTER;

    *dac_cmd = dac_code;
    *dac_en  = enable ? 1 : 0;
}

// ---- Circular Distance (wraps on [-π, π]) ----
static inline float circular_distance(float a, float b) {
    float diff = a - b;
    while (diff >  M_PI) diff -= 2.0f * M_PI;
    while (diff < -M_PI) diff += 2.0f * M_PI;
    return diff;
}

// ---- Current → DAC Code Conversion ----
// DAC: 16-bit unipolar, 0–5V range. Current driver: V_out = 2.0 * I_load.
// DAC_code = (I_target / 5.0V) * (V_ref / I_gain) * 65535
static inline uint16_t current_to_dac_code(float current_ma) {
    if (current_ma < 0.0f) current_ma = 0.0f;
    if (current_ma > CURRENT_MAX_MA) current_ma = CURRENT_MAX_MA;

    // 0 mA → 0x0000, 1.5 mA → 0xFFFF (linear)
    return (uint16_t)((current_ma / CURRENT_MAX_MA) * 65535.0f);
}

// ---- Watchdog Kick ----
// Kicks the independent hardware watchdog timer in PL fabric.
// If not kicked within 50 ms, the PL forcibly disables the DAC.
static inline void kick_watchdog(void) {
    volatile uint32_t* wdt = (volatile uint32_t*)WDT_KICK_REGISTER;
    *wdt = 0xDEADBEEF;  // Magic value triggers WDT reset in PL
}

// ---------------------------------------------------------------------------
// MAIN tDCS PHASE-LOCKED CONTROLLER
//
// Called every 1.953125 ms (512 Hz, synchronized to EEG sampling).
// Runs on bare-metal Cortex-A53. The PL fabric independently enforces:
//   • Current ≤ 1.5 mA (hard comparator)
//   • Watchdog timeout = 50 ms (hard cutoff)
//   • Impedance ≤ 10 kΩ (hard comparator)
// ---------------------------------------------------------------------------
void tdcs_phase_locked_controller(void) {
    // ---- Step 0: Kick hardware watchdog ----
    kick_watchdog();

    // ---- Step 1: Read current state from GPU (with memory barriers) ----
    float measured_phase = read_theta_phase();
    float pdi_from_gpu   = read_pdi_value();

    // ---- Step 2: Kalman Filter Prediction ----
    // Predict phase forward by DT_MS
    float dt_s = DT_MS / 1000.0f;
    phase_estimate     += phase_velocity * dt_s + 0.5f * phase_acceleration * dt_s * dt_s;
    phase_velocity     += phase_acceleration * dt_s;
    phase_covariance   += PROCESS_NOISE_PHASE;
    velocity_covariance += PROCESS_NOISE_VELOCITY;

    // ---- Step 3: Kalman Filter Measurement Update ----
    float innovation = circular_distance(measured_phase, phase_estimate);

    // Compute Kalman gain adaptively
    float S = phase_covariance + MEASUREMENT_NOISE;
    float K_phase  = (S > 1e-10f) ? phase_covariance / S : 0.0f;
    float K_vel    = (S > 1e-10f) ? velocity_covariance / S : 0.0f;

    phase_estimate   += K_phase * innovation;
    phase_velocity   += K_vel * innovation;
    phase_covariance   = (1.0f - K_phase) * phase_covariance;
    velocity_covariance = (1.0f - K_vel) * velocity_covariance;

    // ---- Step 4: Predict phase at DAC latency horizon ----
    float latency_s = DAC_LATENCY_US / 1e6f;
    float predicted_phase = phase_estimate + phase_velocity * latency_s;

    // ---- Step 5: Phase error to trough target ----
    float phase_error = circular_distance(predicted_phase, THETA_TROUGH_PHASE);

    // ---- Step 6: Stimulation decision logic ----
    bool in_phase_window   = (fabsf(phase_error) < PHASE_WINDOW_RAD);
    bool in_pdi_window     = (pdi_from_gpu > PDI_ACTIVE_MIN) &&
                              (pdi_from_gpu < PDI_ACTIVE_MAX);
    bool stimulate          = in_phase_window && in_pdi_window;

    // ---- Step 7: Current control with soft ramp ----
    float target_current_ma;

    if (stimulate) {
        // PDI-adaptive gain: scale current with PDI proximity to 0.7 (optimal)
        float pdi_factor = 1.0f - fabsf(pdi_from_gpu - 0.7f) / 0.3f;
        if (pdi_factor < 0.3f) pdi_factor = 0.3f;  // minimum 30% current
        target_current_ma = CURRENT_MAX_MA * pdi_factor;
    } else {
        // No stimulation: ramp to zero
        target_current_ma = 0.0f;
    }

    // Apply soft ramp
    float max_delta = CURRENT_RAMP_RATE * DT_MS;  // mA per step
    float current_delta = target_current_ma - current_output_ma;

    if (current_delta > max_delta) {
        current_output_ma += max_delta;
    } else if (current_delta < -max_delta) {
        current_output_ma -= max_delta;
    } else {
        current_output_ma = target_current_ma;
    }

    // Clamp to absolute limits
    if (current_output_ma < 0.0f)       current_output_ma = 0.0f;
    if (current_output_ma > CURRENT_MAX_MA) current_output_ma = CURRENT_MAX_MA;

    // ---- Step 8: Write to DAC ----
    // The PL fabric HARDWARE COMPARATOR independently enforces:
    //   • DAC code ≤ CURRENT_LIMIT_CODE
    //   • dac_enable = 0 if impedance > 10 kΩ or watchdog expired
    // The ARM CANNOT override these hardware limits.
    uint16_t dac_code = current_to_dac_code(current_output_ma);
    bool enable = (current_output_ma > 0.01f);  // Deadband to avoid floating

    write_dac_command(dac_code, enable);
}

// ---------------------------------------------------------------------------
// Interrupt Service Routine: EEG Sample Ready
// Called by the ADC DMA completion interrupt at 512 Hz.
// ---------------------------------------------------------------------------
__attribute__((interrupt, section(".text.fast")))
void eeg_sample_ready_isr(void) {
    // Clear interrupt
    volatile uint32_t* irq_clear = (volatile uint32_t*)0xA0000100;
    *irq_clear = 0x1;

    // Execute controller
    tdcs_phase_locked_controller();

    // Data synchronization barrier to ensure all writes complete
    __asm__ volatile ("dsb sy" : : : "memory");
}