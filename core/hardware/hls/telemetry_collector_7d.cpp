// ============================================================================
// ARKHE OS v∞.Ω.∇+++.14.4 — FPGA-Based 7D Telemetry Collector
// Purpose: Ultra-low-latency ingestion of 7D coherence metrics in hardware
// Implemented for Vitis HLS
// ============================================================================

#include <ap_int.h>
#include <ap_fixed.h>

// Type definitions for fixed-point math to balance precision and resources
typedef ap_fixed<32, 16> coherence_val_t; // [16 integer bits, 16 fractional bits]
typedef ap_uint<64> timestamp_t;
typedef ap_uint<256> hash_t; // Representing a DID hash

// Hardware representation of the 7D Coherence Tensor
struct HlsCoherenceTensor7D {
    coherence_val_t phase;            // ε_φ
    coherence_val_t latency_us;       // ε_τ
    coherence_val_t power_mw;         // ε_ρ
    coherence_val_t mercy_gap;        // ε_ε
    coherence_val_t security;         // ε_σ
    coherence_val_t privacy;          // ε_π
    coherence_val_t interpretability; // ε_ι
};

struct TelemetryPacket {
    timestamp_t timestamp;
    hash_t vertex_did;
    HlsCoherenceTensor7D tensor;
};

// Internal hardware registers mapped to sensors
static coherence_val_t reg_phase = 0;
static coherence_val_t reg_latency = 0;
static coherence_val_t reg_power = 0;
static coherence_val_t reg_mercy = 0;
static coherence_val_t reg_security = 0;
static coherence_val_t reg_privacy = 0;
static coherence_val_t reg_interpretability = 0;

// Update specific dimension (called by hardware interrupt handlers or sensor ADCs)
void update_dimension(ap_uint<3> dim_id, coherence_val_t value) {
#pragma HLS INLINE
    switch (dim_id) {
        case 0: reg_phase = value; break;
        case 1: reg_latency = value; break;
        case 2: reg_power = value; break;
        case 3: reg_mercy = value; break;
        case 4: reg_security = value; break;
        case 5: reg_privacy = value; break;
        case 6: reg_interpretability = value; break;
    }
}

// Top-level HLS function to collect and output a 7D telemetry packet
// Streams interface used for ultra-low latency bridging to PCIe/AXI
void telemetry_collector_7d(
    timestamp_t current_timestamp,
    hash_t active_vertex_did,
    bool trigger_sample,
    TelemetryPacket* output_stream
) {
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL
#pragma HLS INTERFACE s_axilite port=current_timestamp bundle=CTRL
#pragma HLS INTERFACE s_axilite port=active_vertex_did bundle=CTRL
#pragma HLS INTERFACE s_axilite port=trigger_sample bundle=CTRL
#pragma HLS INTERFACE m_axi port=output_stream depth=1 offset=slave bundle=MEM

    if (trigger_sample) {
        TelemetryPacket packet;
        packet.timestamp = current_timestamp;
        packet.vertex_did = active_vertex_did;

        // Sample all registers atomically
        packet.tensor.phase = reg_phase;
        packet.tensor.latency_us = reg_latency;
        packet.tensor.power_mw = reg_power;
        packet.tensor.mercy_gap = reg_mercy;
        packet.tensor.security = reg_security;
        packet.tensor.privacy = reg_privacy;
        packet.tensor.interpretability = reg_interpretability;

        // Write to output stream/memory
        *output_stream = packet;
    }
}
