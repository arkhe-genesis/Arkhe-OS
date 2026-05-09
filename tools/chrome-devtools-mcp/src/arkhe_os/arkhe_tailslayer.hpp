#ifndef ARKHE_TAILSLAYER_HPP
#define ARKHE_TAILSLAYER_HPP

#include <tailslayer/hedged_reader.hpp>
#include "arkhe_hal.h"
#include <iostream>
#include <iomanip>
#include <cmath>

namespace arkhe {

// Signal function: waits for a simulated coherence trigger
[[gnu::always_inline]] inline std::size_t arkhe_phase_signal() {
    // Simulated wait for coherence trigger
    uint64_t start = tailslayer::detail::rdtsc_lfence();
    // Wait for approx 0.05s on a 2GHz machine
    while (tailslayer::detail::rdtsc_lfence() - start < 100000000);

    return 0; // Read the first phase for demo
}

// Work function: processes the read phase
[[gnu::always_inline]] inline void arkhe_phase_work(arkhe_phase_t phase) {
    std::cout << "[🜏 ARKHE_TAILSLAYER] PHASE_READ_COMPLETE\n";
    std::cout << "  REAL: " << std::fixed << std::setprecision(6) << phase.real << "\n";
    std::cout << "  IMAG: " << std::fixed << std::setprecision(6) << phase.imag << "\n";

    double coherence = std::sqrt(phase.real * phase.real + phase.imag * phase.imag);
    std::cout << "  LOCAL_COHERENCE: " << coherence << "\n";

    if (coherence > 0.847) {
        std::cout << "  STATUS: PHASE_LOCKED\n";
    } else {
        std::cout << "  STATUS: DECOHERENT_RECOVERY_REQUIRED\n";
    }
}

using CoherentPhaseBuffer = tailslayer::HedgedReader<arkhe_phase_t, arkhe_phase_signal, arkhe_phase_work>;

} // namespace arkhe

#endif // ARKHE_TAILSLAYER_HPP
