#pragma once
#include <cstdint>
#include <ctime>
#include <string>

namespace arkhe::core {

typedef struct {
    uint64_t start_ns;
    uint64_t end_ns;
    const char* operation;      // ex: "zk_proof_gen", "llm_infer"
    const char* substrate;      // ex: "FS-100"
    int consent_granted;        // Se o usuário consentiu profiling detalhado
    uint64_t memory_peak_bytes; // Pico de memória (apenas se consentido)
} sovereign_profile_t;

static uint64_t prof_get_time_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

// Macro de profiling condicional ao consentimento
#define SOVEREIGN_PROFILE(consent, op, sub, code) \
    do { \
        arkhe::core::sovereign_profile_t _prof = { \
            .start_ns = arkhe::core::prof_get_time_ns(), \
            .operation = op, \
            .substrate = sub, \
            .consent_granted = consent, \
            .memory_peak_bytes = 0 \
        }; \
        code \
        _prof.end_ns = arkhe::core::prof_get_time_ns(); \
        if (consent) { \
            /* Registrar log de perfilamento aqui se consentido */ \
        } \
    } while(0)

} // namespace arkhe::core
