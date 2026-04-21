#include "arkhe/transliterator.hpp"
#include <cmath>
#include <numbers>

namespace arkhe {

core::Clifford4D::Multivector Transliterator::synthesize(
    const core::Clifford4D::Multivector& a,
    const core::Clifford4D::Multivector& b) {
    auto prod = core::Clifford4D::geometric_product(a, b);
    // Trunca em grade 2 (Lei da Síntese)
    for(int i=11; i<16; i++) prod[i] = 0.0;
    return prod;
}

bool Transliterator::check_coherence(double source_phase, double target_phase, double r_global) {
    double diff = std::abs(target_phase - source_phase);
    while(diff > std::numbers::pi) diff -= 2*std::numbers::pi;
    // double max_noise = std::sqrt((1.0 - r_global) / 2.0);
    double K = 0.1; double Kc = 0.1;
    double r_crit = (2.0 / std::numbers::pi) * std::atan(K / Kc);
    double coherence = std::abs(std::cos(diff));
    return coherence >= r_crit;
}

bool Transliterator::check_cohesion(const core::Clifford4D::Multivector& before,
                                    const core::Clifford4D::Multivector& after) {
    double dist = 0.0;
    for(int i=0; i<16; i++) dist += std::abs(after[i] - before[i]);
    double epsilon = 0.5; // tolerância base
    return dist <= epsilon;
}

double Transliterator::arkhe_number(const core::Clifford4D::Multivector& state,
                                     double phase, double cohesion_w) {
    // Entropia sintética simplificada
    double norm = core::Clifford4D::norm(state);
    double H = 0.0;
    for(int i=0; i<16; i++) {
        double p = (state[i]*state[i]) / (norm*norm + 1e-12);
        if(p > 1e-12) H -= p * std::log(p);
    }
    double C = std::abs(std::cos(phase));
    return 0.4 * H + 0.3 * (1.0 - C) + 0.3 * cohesion_w;
}

} // namespace arkhe
