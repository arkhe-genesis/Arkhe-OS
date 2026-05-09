#include <torch/torch.h>
#include <vector>
#include <iostream>

class PhaseGradientRedistributor : public torch::nn::Module {
public:
    PhaseGradientRedistributor(int64_t n_nodes,
                               const torch::Tensor& distance_mask,
                               const torch::Tensor& battery_levels,
                               float initial_k = 1.5f)
        : n_nodes_(n_nodes),
          dist_mask_(distance_mask),
          battery_levels_(battery_levels),
          sparse_weight_(0.01f),
          energy_budget_(0.5f) {

        K_ = register_parameter("K", torch::full({n_nodes, n_nodes}, initial_k, torch::requires_grad()));
        dist_mask_ = dist_mask_.to(K_.device());
        battery_levels_ = battery_levels_.to(K_.device());
    }

    std::tuple<torch::Tensor, torch::Tensor, torch::Tensor> forward(
        const torch::Tensor& phases,
        const torch::Tensor& alive_mask) {

        auto phi_i = phases.unsqueeze(1);
        auto phi_j = phases.unsqueeze(0);
        auto phase_diff = phi_j - phi_i;

        // Effective mask: nodes alive * distance * battery_penalty
        auto battery_penalty = battery_levels_.clamp(0.1, 1.0);
        auto effective_mask = alive_mask.unsqueeze(1) * alive_mask.unsqueeze(0) * dist_mask_ * battery_penalty;

        auto sin_diff = torch::sin(phase_diff);
        auto coupling = torch::sum(K_ * effective_mask * sin_diff, 1);

        auto cos_sum = torch::mean(torch::cos(phases));
        auto sin_sum = torch::mean(torch::sin(phases));
        auto R = torch::sqrt(cos_sum.pow(2) + sin_sum.pow(2));

        // Energy cost: penalize high K on low battery
        auto energy_cost = torch::mean(K_.abs() * (1.0 - battery_levels_));

        auto loss = (1.0 - R) + 0.01 * torch::norm(K_) + sparse_weight_ * torch::norm(K_, 1) + 0.1 * energy_cost;

        return {R, coupling, loss};
    }

    void redistribute(torch::Tensor& phases, const torch::Tensor& alive_mask, int64_t steps = 50, float lr = 0.05f) {
        torch::optim::Adam optimizer({K_}, torch::optim::AdamOptions(lr));

        for (int64_t i = 0; i < steps; ++i) {
            optimizer.zero_grad();
            auto [R, dtheta, loss] = forward(phases, alive_mask);
            loss.backward();
            optimizer.step();

            {
                torch::NoGradGuard no_grad;
                K_.data().clamp_(0.1, 5.0);
                // Euler integration
                phases = (phases + dtheta * 0.1).remainder(2 * M_PI);
            }
        }
    }

    void update_battery(const torch::Tensor& battery_levels) {
        battery_levels_ = battery_levels.to(K_.device());
    }

    torch::Tensor get_K() const { return K_; }

private:
    torch::nn::Parameter K_;
    torch::Tensor dist_mask_;
    torch::Tensor battery_levels_;
    int64_t n_nodes_;
    float sparse_weight_;
    float energy_budget_;
};
