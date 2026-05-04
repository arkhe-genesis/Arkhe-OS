#pragma once
#include "arkhe/core/clifford.hpp"
#include <complex>
#include <vector>
#include <string>
#include <map>
#include <random>

namespace arkhe::quantum {

// ═══════════════════════════════════════════════════════════════════════════════
// QHTTP — Protocolo quantum:// Simulado
// ═══════════════════════════════════════════════════════════════════════════════
enum class QMethod { SUPERPOSE, ENTANGLE, ROTATE, MEASURE, TELEPORT, DECOHERE };

// Prioridade do Quantum Bus
enum class QBusPriority {
    EMERGENCY = 10,
    INFERENCE = 7,
    CONSENT = 6,
    AUDIT = 4,
    BACKGROUND = 1
};

// Frame do Quantum Bus com metadados de soberania
struct QBusFrame {
    uint32_t magic = 0xCADEA1;
    uint16_t version = 1;
    QBusPriority priority = QBusPriority::CONSENT;
    char consent_id[36]; // UUID do consentimento
    char substrate_mask[8];
    uint32_t payload_len;
    std::vector<uint8_t> payload;
};

struct QResponse {
    int status = 200;
    std::string status_text;
    std::vector<std::complex<double>> statevector;
    std::string classical_bits;
    double fidelity = 1.0;
    std::string consent_id; // Adicionado para rastreabilidade
};

class QNode {
public:
    std::string node_id;
    int n_qubits;

    explicit QNode(std::string id, int qubits = 8);

    // Gera par de Bell (simulado)
    QResponse entangle(const std::string& remote_node);

    // Teletransporte de estado (simulado via correlação de fase)
    QResponse teleport_state(const std::string& remote,
                             const std::vector<std::complex<double>>& amplitude,
                             const std::string& consent_id = "");

    // Codifica estado cortical em amplitudes quânticas
    std::vector<std::complex<double>> encode_cortical(const core::Clifford4D::Multivector& state);

    // Emaranhamentos ativos
    std::map<std::string, std::pair<int,int>> entangled_pairs;

    // Novo: Envio via Quantum Bus Frame
    QResponse send_frame(const QBusFrame& frame, const std::string& remote_node);

private:
    std::mt19937 rng_;
};

} // namespace arkhe::quantum
