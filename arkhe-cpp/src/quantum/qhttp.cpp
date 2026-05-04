#include "arkhe/quantum/qhttp.hpp"
#include <cmath>
#include <random>
#include <cstring>

namespace arkhe::quantum {

QNode::QNode(std::string id, int qubits) : node_id(std::move(id)), n_qubits(qubits) {
    rng_.seed(std::hash<std::string>{}(node_id));
}

QResponse QNode::entangle(const std::string& remote_node) {
    QResponse res;
    res.status = 202;
    res.status_text = "Entangled";
    entangled_pairs[remote_node] = {0, 1};

    // Estado de Bell simulado: (|00> + |11>)/sqrt(2)
    res.statevector = {
        {1.0/std::sqrt(2.0), 0.0},
        {0.0, 0.0},
        {0.0, 0.0},
        {1.0/std::sqrt(2.0), 0.0}
    };
    res.fidelity = 1.0;
    return res;
}

QResponse QNode::teleport_state(const std::string& remote,
                                const std::vector<std::complex<double>>& amplitude,
                                const std::string& consent_id) {
    if(!entangled_pairs.count(remote)) {
        return {503, "Entanglement-Lost", {}, "", 0.0, consent_id};
    }

    QResponse res;
    res.status = 218;
    res.status_text = "Telescoped";
    res.consent_id = consent_id;

    // Simulação: teletransporte preserva amplitude com ruído quântico
    res.statevector = amplitude;
    std::normal_distribution<double> noise(0.0, 0.01);
    for(auto& amp : res.statevector) {
        amp += std::complex<double>(noise(rng_), noise(rng_));
    }

    // Normaliza
    double norm = 0.0;
    for(const auto& a : res.statevector) norm += std::abs(a)*std::abs(a);
    norm = std::sqrt(norm);
    if (norm > 1e-12) {
        for(auto& a : res.statevector) a /= norm;
    }

    res.fidelity = 0.99;
    res.classical_bits = "00"; // correções simuladas
    return res;
}

std::vector<std::complex<double>> QNode::encode_cortical(
    const core::Clifford4D::Multivector& state) {

    // Amplitude encoding: vetor real Cliff(4,0) -> qubit amplitudes
    std::vector<std::complex<double>> amps;
    for(int i=0; i<16 && i < (1<<n_qubits); i++) {
        amps.push_back({state[i], 0.0});
    }

    // Normaliza
    double norm = 0.0;
    for(const auto& a : amps) norm += std::abs(a)*std::abs(a);
    norm = std::sqrt(norm);
    if (norm > 1e-12) {
        for(auto& a : amps) a /= norm;
    }

    return amps;
}

QResponse QNode::send_frame(const QBusFrame& frame, const std::string& remote_node) {
    QResponse res;
    if (frame.magic != 0xCADEA1) {
        res.status = 400;
        res.status_text = "Invalid Magic";
        return res;
    }

    std::string consent_str(frame.consent_id, 36);
    res.consent_id = consent_str;
    res.status = 200;
    res.status_text = "Frame Processed";
    res.fidelity = 1.0;

    // Simular processamento dependendo da prioridade
    if (frame.priority == QBusPriority::EMERGENCY) {
        res.status_text += " (High Priority)";
    }

    return res;
}

} // namespace arkhe::quantum
