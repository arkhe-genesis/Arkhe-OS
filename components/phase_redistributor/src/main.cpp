#include "PhaseGradientRedistributor.h"
#include <iostream>
#include <random>

int main() {
    // Simular 1000 nós (sensores fixos + móveis)
    const int64_t n_nodes = 1000;

    // Criar uma máscara de distância realista: enlace possível se distância < 100m
    // Aqui geramos uma matriz aleatória para exemplo; na prática, carregue de um arquivo.
    torch::Tensor dist_mask = torch::rand({n_nodes, n_nodes}) > 0.95; // 5% de densidade
    dist_mask = dist_mask.to(torch::kFloat32);

    // Instanciar o redistribuidor
    PhaseGradientRedistributor redistributor(n_nodes, dist_mask, 1.5f);

    // Inicializar fases aleatórias
    torch::Tensor phases = 2 * M_PI * torch::rand({n_nodes});

    // Simular ataque EMP: 20% dos nós falham
    torch::Tensor alive_mask = torch::ones({n_nodes});
    int64_t n_fail = static_cast<int64_t>(0.2 * n_nodes);
    auto fail_indices = torch::randperm(n_nodes).slice(0, 0, n_fail);
    alive_mask.index_fill_(0, fail_indices, 0.0);

    std::cout << "Iniciando redistribuição após EMP..." << std::endl;
    redistributor.redistribute(phases, alive_mask, 50, 0.05f);

    // Exibir matriz K final (média e desvio)
    auto K_final = redistributor.get_K();
    std::cout << "\nMatriz K final:" << std::endl;
    std::cout << "Média: " << K_final.mean().item<float>()
              << ", Desvio: " << K_final.std().item<float>() << std::endl;

    return 0;
}
