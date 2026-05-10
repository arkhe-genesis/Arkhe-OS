#include <iostream>
#include <torch/torch.h>
#include <yaml-cpp/yaml.h>
#include "PhaseGradientRedistributor.h"

int main(int argc, char** argv) {
    std::string config_path = "config/gateway_config.yaml";
    if (argc > 2 && std::string(argv[1]) == "--config") {
        config_path = argv[2];
    }

    std::cout << "🜏 Tzinor Gateway Initializing..." << std::endl;

    try {
        YAML::Node config = YAML::LoadFile(config_path);
        int n_nodes = config["n_nodes"].as<int>();
        float initial_k = config["initial_k"].as<float>();

        std::cout << "Loading configuration for " << n_nodes << " nodes (K=" << initial_k << ")" << std::endl;

        PhaseGradientRedistributor redistributor(n_nodes, initial_k);

        // Simulação de loop de controle
        auto phases = torch::randn({n_nodes});
        auto alive_mask = torch::ones({n_nodes});

        auto [R, coupling] = redistributor.forward(phases, alive_mask);

        std::cout << "Initial Coherence (R): " << R.item<float>() << std::endl;
        std::cout << "Gateway operational." << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Fatal Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
