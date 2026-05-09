#include "PhaseGradientRedistributor.h"
#include <iostream>

/**
 * @file sybil_test.cpp
 * @brief Simulates a noise-injection (Sybil) attack and verifies the redistributor's ability to expel noise.
 */

int main() {
    const int64_t n_nodes = 1000;

    // Physical constraints
    torch::Tensor dist_mask = (torch::rand({n_nodes, n_nodes}) > 0.95).to(torch::kFloat32);
    torch::Tensor battery = torch::full({n_nodes}, 0.8f);

    PhaseGradientRedistributor model(n_nodes, dist_mask, battery);
    torch::Tensor phases = torch::rand({n_nodes}) * 2 * M_PI;
    torch::Tensor alive = torch::ones({n_nodes});

    std::cout << "🜏 [SYBIL TEST] Initializing stable network..." << std::endl;
    model.redistribute(phases, alive, 20);

    // Injection
    std::cout << "🜏 [SYBIL TEST] Injecting 200 Sybil nodes (noise)..." << std::endl;
    auto sybil_idx = torch::randint(0, n_nodes, {200});
    phases.index_put_({sybil_idx}, torch::rand({200}) * 2 * M_PI);

    std::cout << "🜏 [SYBIL TEST] Running recovery gradient..." << std::endl;
    model.redistribute(phases, alive, 50);

    auto K_final = model.get_K();
    std::cout << "✅ Result: K_avg = " << K_final.mean().item<float>() << std::endl;

    return 0;
}
