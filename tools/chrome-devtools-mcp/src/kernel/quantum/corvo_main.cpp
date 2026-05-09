/**
 * @file corvo_main.cpp
 * @brief Integration example for CORVO OS
 */

#include "anyon_analyzer.hpp"
#include <iostream>
#include <chrono>
#include <thread>
#include <random>

using namespace corvo::quantum;

void vCORVOMainTask() {
    AnyonAnalyzer anyon;
    anyon.initialize();

    std::cout << "[CORVO] Initializing Anyon Analyzer..." << std::endl;
    std::cout << "[CORVO] Calibration: MU0 = 0.05, MU1 = 1.0" << std::endl;

    // Start measurement window
    anyon.start_measurement();
    std::cout << "[CORVO] Starting measurement window..." << std::endl;

    // Simulate APD data
    std::default_random_engine generator;
    std::bernoulli_distribution outcome_dist(P_VAC_FIBONACCI);
    std::poisson_distribution<uint32_t> vacuum_dist(MU0);
    std::poisson_distribution<uint32_t> tau_dist(MU1);

    for (int i = 0; i < 2000; ++i) {
        bool is_vacuum = outcome_dist(generator);
        uint32_t count = is_vacuum ? vacuum_dist(generator) : tau_dist(generator);

        anyon.on_photon_detection(count);
    }

    // Analyze and decide
    AnyonAnalyzer::Result result = anyon.analyze();

    std::cout << "[CORVO] Total trials: 2000" << std::endl;
    std::cout << "[CORVO] Log-likelihood ratio: " << anyon.get_log_lambda() << std::endl;

    switch (result) {
        case AnyonAnalyzer::Result::FIBONACCI_ANYON_DETECTED:
            std::cout << "[CORVO] Decision: FIBONACCI ANYON DETECTED ✓" << std::endl;
            break;
        case AnyonAnalyzer::Result::CLASSICAL_SYSTEM:
            std::cout << "[CORVO] Decision: SYSTEM CLASSICAL" << std::endl;
            break;
        default:
            std::cout << "[CORVO] Decision: INCONCLUSIVE" << std::endl;
            break;
    }
}

int main() {
    vCORVOMainTask();
    return 0;
}
