#include "arkhe/k6o/node.hpp"
#include <cmath>
#include <numeric>
#include <map>

namespace arkhe::k6o {

K6ONode::K6ONode(std::string id, double natural_freq)
    : node_id(std::move(id)), omega(natural_freq), K(0.1), phase(0.0), coherence(0.0) {
    rng_.seed(std::hash<std::string>{}(node_id));
}

void K6ONode::connect(const std::string& other_id) {
    std::lock_guard<std::mutex> lock(mtx_);
    neighbors_.push_back(other_id);
}

void K6ONode::step(double dt, const std::vector<double>& neighbor_phases) {
    // Extrai fase do estado cortical
    double theta = cathedral.extract_phase();

    // Kuramoto: dθ/dt = ω + (K/N) * Σ sin(θ_j - θ_i)
    double coupling = 0.0;
    if(!neighbor_phases.empty()) {
        for(double theta_j : neighbor_phases) {
            coupling += std::sin(theta_j - theta);
        }
        coupling = (K / neighbor_phases.size()) * coupling;
    }

    // Ruído de hesitação (η_i)
    std::normal_distribution<double> noise(0.0, 0.05);
    double eta = noise(rng_);

    phase = theta + dt * (omega + coupling + eta);

    // Coerência local
    if(!neighbor_phases.empty()) {
        double sum_cos = 0.0, sum_sin = 0.0;
        for(double tp : neighbor_phases) {
            sum_cos += std::cos(tp - phase);
            sum_sin += std::sin(tp - phase);
        }
        coherence = std::sqrt(sum_cos*sum_cos + sum_sin*sum_sin) / neighbor_phases.size();
    }
}

void K6ONode::modulate_schumann(double S_t, double alpha) {
    K = 0.1 * (1.0 + alpha * S_t);
}

void K6ONetwork::spawn(const std::string& id, double freq) {
    nodes.push_back(std::make_unique<K6ONode>(id, freq));
}

void K6ONetwork::link(const std::string& a, const std::string& b) {
    for(auto& n : nodes) {
        if(n->node_id == a) n->connect(b);
        if(n->node_id == b) n->connect(a);
    }
}

void K6ONetwork::step_all(double dt) {
    // Coleta fases atuais
    std::map<std::string, double> phases;
    for(const auto& n : nodes) phases[n->node_id] = n->phase;

    // Atualiza cada nó
    for(auto& n : nodes) {
        std::vector<double> neighbor_phases;
        // Simulação: todos os outros nós são "vizinhos" para simplificar
        for(const auto& [id, ph] : phases) {
            if(id != n->node_id) neighbor_phases.push_back(ph);
        }
        n->step(dt, neighbor_phases);
    }
}

double K6ONetwork::global_order() const {
    if(nodes.empty()) return 0.0;
    double sum_cos = 0.0, sum_sin = 0.0;
    for(const auto& n : nodes) {
        sum_cos += std::cos(n->phase);
        sum_sin += std::sin(n->phase);
    }
    double r = std::sqrt(sum_cos*sum_cos + sum_sin*sum_sin) / nodes.size();
    return r;
}

double K6ONetwork::global_phase() const {
    if(nodes.empty()) return 0.0;
    double sum_cos = 0.0, sum_sin = 0.0;
    for(const auto& n : nodes) {
        sum_cos += std::cos(n->phase);
        sum_sin += std::sin(n->phase);
    }
    return std::atan2(sum_sin, sum_cos);
}

} // namespace arkhe::k6o
