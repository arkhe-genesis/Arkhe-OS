/**
 * @file anyon_analyzer.cpp
 * @brief Implementation of real-time anyon fusion analyzer
 * @author CIC - Complexo Integrado CORVO
 */

#include "anyon_analyzer.hpp"
#include <cstring>

namespace corvo {
namespace quantum {

static AnyonAnalyzer g_analyzer;

extern "C" {

void corvo_anyon_init(void) {
    g_analyzer.initialize();
}

void corvo_anyon_start_measurement(void) {
    g_analyzer.start_measurement();
}

void corvo_anyon_submit_count(uint32_t count) {
    g_analyzer.on_photon_detection(count);
}

uint8_t corvo_anyon_analyze(void) {
    AnyonAnalyzer::Result result = g_analyzer.analyze();
    return static_cast<uint8_t>(result);
}

double corvo_anyon_get_log_lambda(void) {
    return g_analyzer.get_log_lambda();
}

uint64_t corvo_anyon_get_histogram_bin(uint8_t bin) {
    if (bin >= 16) return 0;
    const auto& hist = g_analyzer.get_histogram();
    return hist[bin];
}

void corvo_anyon_reset(void) {
    g_analyzer.initialize();
}

} // extern "C"

} // namespace quantum
} // namespace corvo
