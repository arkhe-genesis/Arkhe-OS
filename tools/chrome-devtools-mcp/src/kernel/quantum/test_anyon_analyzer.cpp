#include <iostream>
#include <cassert>
#include <cmath>
#include "anyon_analyzer.hpp"

using namespace corvo::quantum;

void test_log_gamma() {
    std::cout << "Testing log_gamma..." << std::endl;
    // log_gamma(1) = log(0!) = 0
    assert(std::abs(log_gamma(1.0)) < 1e-10);
    // log_gamma(2) = log(1!) = 0
    assert(std::abs(log_gamma(2.0)) < 1e-10);
    // log_gamma(6) = log(5!) = log(120) ≈ 4.7874917
    assert(std::abs(log_gamma(6.0) - 4.7874917) < 1e-6);
}

void test_poisson_pmf() {
    std::cout << "Testing poisson_pmf..." << std::endl;
    // P(k=0; mu=0.05) = e^-0.05 ≈ 0.951229
    double p0 = poisson_pmf(0, 0.05);
    assert(std::abs(p0 - 0.951229) < 1e-6);

    // P(k=1; mu=1.0) = e^-1 * 1^1 / 1! = e^-1 ≈ 0.367879
    double p1 = poisson_pmf(1, 1.0);
    assert(std::abs(p1 - 0.367879) < 1e-6);
}

void test_mixture_model() {
    std::cout << "Testing MixtureModel..." << std::endl;
    // Classical/Ising mixture: p_vac = 0.5, mu0 = 0.05, mu1 = 1.0
    MixtureModel model(0.5, 0.05, 1.0);
    // P(k=0) = 0.5 * e^-0.05 + 0.5 * e^-1 ≈ 0.5*0.9512 + 0.5*0.3679 ≈ 0.4756 + 0.1840 = 0.6596
    double p0 = model.pmf(0);
    assert(std::abs(p0 - 0.6596) < 0.001);
}

int main() {
    test_log_gamma();
    test_poisson_pmf();
    test_mixture_model();

    std::cout << "All Anyon Analyzer tests passed ✓" << std::endl;
    return 0;
}
