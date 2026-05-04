#include "PhaseGradientRedistributor.h"
#include <torch/script.h> // para otimizadores
#include <iostream>
#include <fstream>

PhaseGradientRedistributor::PhaseGradientRedistributor(int64_t n_nodes,
                                                       const torch::Tensor& distance_mask,
                                                       float initial_k)
    : n_nodes_(n_nodes),
      dist_mask_(distance_mask),
      sparse_weight_(0.01f) {
    // Inicializa K como parâmetro treinável
    K_ = register_parameter("K", torch::full({n_nodes, n_nodes}, initial_k, torch::requires_grad()));
    // Garante que a máscara de distância esteja no mesmo dispositivo que o modelo
    dist_mask_ = dist_mask_.to(K_.device());
}

std::tuple<torch::Tensor, torch::Tensor, torch::Tensor>
PhaseGradientRedistributor::forward(const torch::Tensor& phases,
                                    const torch::Tensor& alive_mask,
                                    float dt) {
    // 1. Expandir fases para calcular diferenças
    auto phi_i = phases.unsqueeze(1);        // [n, 1]
    auto phi_j = phases.unsqueeze(0);        // [1, n]
    auto phase_diff = phi_j - phi_i;         // [n, n]

    // 2. Máscara efetiva: nós vivos + distância
    auto effective_mask = alive_mask.unsqueeze(1) * alive_mask.unsqueeze(0) * dist_mask_;

    // 3. Termo de acoplamento: sum_j K_ij * sin(θ_j - θ_i) * mask
    auto sin_diff = torch::sin(phase_diff);
    auto coupling = torch::sum(K_ * effective_mask * sin_diff, /*dim=*/1); // [n]

    // 4. Coerência global R
    auto complex_phases = torch::exp(torch::complex(phases, torch::zeros_like(phases)));
    auto R = torch::abs(torch::mean(complex_phases));

    // 5. Perda: (1 - R) + L2 + L1
    auto loss = (1.0 - R) + 0.01 * torch::norm(K_) + sparse_weight_ * torch::norm(K_, 1);

    // 6. Derivada (dθ/dt) – aqui assumimos frequência natural zero
    auto dtheta = coupling;   // pode adicionar omega depois

    return {R, dtheta, loss};
}

void PhaseGradientRedistributor::redistribute(torch::Tensor& phases,
                                              const torch::Tensor& alive_mask,
                                              int64_t steps,
                                              float lr) {
    // Criar otimizador Adam sobre o parâmetro K_
    torch::optim::Adam optimizer({K_}, torch::optim::AdamOptions(lr));

    for (int64_t step = 0; step < steps; ++step) {
        optimizer.zero_grad();
        auto [R, dtheta, loss] = forward(phases, alive_mask);
        loss.backward();
        optimizer.step();

        // Clamping para manter K_ dentro de limites físicos
        {
            torch::NoGradGuard no_grad;
            K_.data().clamp_(0.1, 5.0);
        }

        // Atualiza as fases com Euler (dt = 0.1)
        phases = phases + dtheta * 0.1;
        phases = phases % (2 * M_PI);  // wrap to [0, 2π)

        if (step % 10 == 0) {
            std::cout << "Step " << step << " | R = " << R.item<float>()
                      << " | K_mean = " << K_.mean().item<float>() << std::endl;
        }
    }
}

void PhaseGradientRedistributor::apply_node_override(int64_t node_idx, float multiplier,
                                                     int duration_sec,
                                                     const std::string& technician_id,
                                                     const std::string& reason) {
    std::lock_guard<std::mutex> lock(override_mutex_);
    auto now = std::chrono::steady_clock::now();
    OverrideEntry entry{multiplier, now + std::chrono::seconds(duration_sec), technician_id, reason};

    // Salvar K original (se ainda não estiver salvo)
    if (original_K_.numel() == 0) {
        original_K_ = K_.detach().clone();
    }

    // Aplicar override: multiplicar todos os K_ij que envolvem node_idx
    torch::NoGradGuard no_grad;
    auto K_data = K_.data_ptr<float>();
    for (int64_t j = 0; j < n_nodes_; ++j) {
        K_data[node_idx * n_nodes_ + j] *= multiplier;
        if (node_idx != j) {
            K_data[j * n_nodes_ + node_idx] *= multiplier;
        }
    }
    node_overrides_[node_idx] = entry;

    std::cout << "[OVERRIDE] Node " << node_idx << " K multiplied by " << multiplier
              << " for " << duration_sec << "s. Technician: " << technician_id
              << " Reason: " << reason << std::endl;

    log_override(node_idx, multiplier, duration_sec, technician_id, reason);
}

void PhaseGradientRedistributor::clear_override(int64_t node_idx) {
    std::lock_guard<std::mutex> lock(override_mutex_);
    if (node_overrides_.count(node_idx)) {
        torch::NoGradGuard no_grad;
        auto K_data = K_.data_ptr<float>();
        auto orig_data = original_K_.data_ptr<float>();
        for (int64_t j = 0; j < n_nodes_; ++j) {
            K_data[node_idx * n_nodes_ + j] = orig_data[node_idx * n_nodes_ + j];
            K_data[j * n_nodes_ + node_idx] = orig_data[j * n_nodes_ + node_idx];
        }
        node_overrides_.erase(node_idx);
    }
}

void PhaseGradientRedistributor::update_overrides() {
    std::lock_guard<std::mutex> lock(override_mutex_);
    auto now = std::chrono::steady_clock::now();
    bool changed = false;

    for (auto it = node_overrides_.begin(); it != node_overrides_.end(); ) {
        if (now >= it->second.expiry) {
            torch::NoGradGuard no_grad;
            auto K_data = K_.data_ptr<float>();
            auto orig_data = original_K_.data_ptr<float>();
            int64_t idx = it->first;
            for (int64_t j = 0; j < n_nodes_; ++j) {
                K_data[idx * n_nodes_ + j] = orig_data[idx * n_nodes_ + j];
                K_data[j * n_nodes_ + idx] = orig_data[j * n_nodes_ + idx];
            }
            it = node_overrides_.erase(it);
            changed = true;
        } else {
            ++it;
        }
    }

    if (changed) {
        std::cout << "[OVERRIDE] Expired overrides cleared." << std::endl;
    }
}

void PhaseGradientRedistributor::log_override(int64_t node_idx, float multiplier, int duration_sec,
                                               const std::string& technician_id, const std::string& reason) {
    std::ofstream log_file("manual_overrides.csv", std::ios::app);
    if (log_file.is_open()) {
        auto now = std::chrono::system_clock::now();
        std::time_t now_time = std::chrono::system_clock::to_time_t(now);
        char buf[100];
        std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&now_time));
        log_file << buf << "," << node_idx << "," << multiplier << "," << duration_sec << "," << technician_id << "," << reason << "\n";
        log_file.close();
    }
}
