#include "PhaseGradientRedistributor.h"
#include <iostream>
#include <chrono>
#include <thread>

/**
 * @file gateway_main.cpp
 * @brief Principal entry point for the Tzinor Gateway embedding neural control.
 */

int main(int argc, char* argv[]) {
    std::cout << "==========================================" << std::endl;
    std::cout << "  🚂 tzinor_core Gateway v3.1" << std::endl;
    std::cout << "==========================================" << std::endl;

    const int64_t n_nodes = 1000;
    torch::Tensor dist_mask = (torch.rand({n_nodes, n_nodes}) > 0.95).to(torch::kFloat32);
    torch::Tensor battery = torch::full({n_nodes}, 0.7f);

    PhaseGradientRedistributor redistributor(n_nodes, dist_mask, battery);

    torch::Tensor phases = torch::rand({n_nodes}) * 2 * M_PI;
    torch::Tensor alive = torch::ones({n_nodes});

    // Main loop simulation
    for (int step = 0; step < 100; ++step) {
        auto [R, dtheta, loss] = redistributor.forward(phases, alive);
        float R_val = R.item<float>();

        if (R_val < 0.75) {
            std::cout << "[Step " << step << "] 🔄 Low Coherence (R=" << R_val << "), redistributing..." << std::endl;
            redistributor.redistribute(phases, alive, 10, 0.05f);
        }

        if (step % 20 == 0) {
            std::cout << "[Step " << step << "] R = " << R_val
                      << " | K_avg = " << redistributor.get_K().mean().item<float>() << std::endl;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    return 0;
}
