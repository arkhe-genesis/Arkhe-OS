#pragma once

// Universal-unit profile tuning for ARKHE workload
// Profile: (uin, uset, ukvs, u×)
// Rationale: ARKHE uses more SET lookups (MI estimation) and field mults (curve fit)

#ifndef ARKHE_UNIVERSAL_PROFILE
#define ARKHE_UNIVERSAL_PROFILE_UIN  1   // Unrestricted auxiliary inputs per unit
#define ARKHE_UNIVERSAL_PROFILE_USET 2   // Set-restricted inputs per unit (↑ for MI bins)
#define ARKHE_UNIVERSAL_PROFILE_UKVS 1   // KVS operations per unit
#define ARKHE_UNIVERSAL_PROFILE_UX   2   // Field multiplications per unit (↑ for arithmetic)
#endif

#include <algorithm>

// Helper: compute instruction size given resource counts
inline size_t compute_arkhe_instruction_size(
    size_t n_in, size_t n_set, size_t n_kvs, size_t n_mult, size_t m_registers
) {
    // From Equation (1) in ZEE200 paper
    size_t uin = ARKHE_UNIVERSAL_PROFILE_UIN;
    size_t uset = ARKHE_UNIVERSAL_PROFILE_USET;
    size_t ukvs = ARKHE_UNIVERSAL_PROFILE_UKVS;
    size_t ux = ARKHE_UNIVERSAL_PROFILE_UX;

    // Account for register-passing multiplications
    size_t adjusted_mult = n_mult + m_registers + 2;

    size_t units_in = (n_in + uin - 1) / uin;      // ceil
    size_t units_set = (n_set + uset - 1) / uset;
    size_t units_kvs = (n_kvs + ukvs - 1) / ukvs;
    size_t units_mult = (adjusted_mult + ux - 1) / ux;

    return std::max({units_in, units_set, units_kvs, units_mult});
}
