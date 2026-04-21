#pragma once
#include "arkhe/core/biocomputer.hpp"
#include <vector>
#include <mutex>
#include <atomic>

namespace arkhe::k6o {

// ═══════════════════════════════════════════════════════════════════════════════
// K6O NODE — Oscilador de Kuramoto Acoplado à Catedral
// ═══════════════════════════════════════════════════════════════════════════════
class K6ONode {
public:
    std::string node_id;
    core::CliffordBiocomputer cathedral;

    double omega;          // Frequência natural
    double K;              // Força de acoplamento
    double phase;          // Fase interna θ_i
    double coherence;      // Parâmetro de ordem local r_i

    std::atomic<bool> running{false};

    explicit K6ONode(std::string id, double natural_freq = 1.0);

    // Conecta a outro nó (matriz de adjacência)
    void connect(const std::string& other_id);

    // Passo de integração Kuramoto
    void step(double dt, const std::vector<double>& neighbor_phases);

    // Modula Schumann
    void modulate_schumann(double S_t, double alpha = 0.5);

    double get_order_parameter() const { return coherence; }

private:
    std::vector<std::string> neighbors_;
    std::mutex mtx_;
    std::mt19937 rng_;
};

// ═══════════════════════════════════════════════════════════════════════════════
// K6O NETWORK — Ensemble Planetário
// ═══════════════════════════════════════════════════════════════════════════════
class K6ONetwork {
public:
    std::vector<std::unique_ptr<K6ONode>> nodes;

    void spawn(const std::string& id, double freq);
    void link(const std::string& a, const std::string& b);
    void step_all(double dt);
    double global_order() const; // r(t)
    double global_phase() const; // ψ(t)
};

} // namespace arkhe::k6o
