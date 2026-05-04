#include "arkhe/core/biocomputer.hpp"
#include <cmath>
#include <algorithm>

namespace arkhe::core {

void EukaryoticCell::update(double dt, const std::array<double, 8>& actions) {
    // Decaimento natural
    homeostasis[0] = std::min(1.0, homeostasis[0] + 0.01 * dt); // hunger
    homeostasis[1] = std::min(1.0, homeostasis[1] + 0.005 * dt); // fatigue
    homeostasis[7] = std::max(0.0, homeostasis[7] - 0.008 * dt); // energy
    homeostasis[2] = std::max(0.0, homeostasis[2] - 0.02 * dt);  // fear
    homeostasis[3] = std::max(0.0, homeostasis[3] - 0.015 * dt); // rage

    // Efeitos de ação
    homeostasis[0] = std::max(0.0, homeostasis[0] - actions[0]); // eat
    homeostasis[1] = std::max(0.0, homeostasis[1] - actions[1]); // sleep
    homeostasis[7] = std::min(1.0, homeostasis[7] + actions[7]); // energy+
    homeostasis[3] = std::min(1.0, homeostasis[3] + actions[3]); // rage+
}

void NervousSystem::forward(const std::vector<double>& perception,
                            const std::array<double, 8>& homeostasis) {
    // Concatena percepção + homeostase (simplificado para 32 dims)
    std::vector<double> x(32, 0.0);
    for(size_t i=0; i<std::min(perception.size(), size_t(24)); i++) x[i] = perception[i];
    for(int i=0; i<8; i++) x[24+i] = homeostasis[i];

    // 4 axônios paralelos
    std::array<double, 16> outputs[4];
    for(int a=0; a<4; a++) {
        double sum = 0.0;
        for(size_t i=0; i<x.size(); i++) sum += axons[a][i] * x[i];
        double act = std::tanh(sum);
        for(int j=0; j<16; j++) outputs[a][j] = act * merge_weights[j];
    }

    // Fusão geométrica (média simplificada)
    for(int j=0; j<16; j++) {
        emotional_state[j] = 0.25 * (outputs[0][j] + outputs[1][j] + outputs[2][j] + outputs[3][j]);
    }
}

CorticalColumn::CorticalColumn(int n_minicolumns) {
    minicolumns.resize(n_minicolumns);
    for(auto& mc : minicolumns) mc = Clifford4D::zero();
}

void CorticalColumn::process(const std::array<double, 16>& limbic_input) {
    // Recorrência: estado = 0.7*estado + 0.3*input
    for(int i=0; i<16; i++) {
        state[i] = 0.7 * state[i] + 0.3 * limbic_input[i];
    }
    // Ativação minicolumns (competição)
    double max_act = -1e18;
    for(auto& mc : minicolumns) {
        double act = Clifford4D::scalar_product(mc, state);
        if(act > max_act) max_act = act;
    }
}

CliffordBiocomputer::CliffordBiocomputer(int dim) : dim_(dim), cortex(8) {
    rng_.seed(42);
    // Inicializa pesos nervosos com pequenos valores aleatórios
    std::uniform_real_distribution<double> dist(-0.1, 0.1);
    for(auto& axon : nervous.axons)
        for(auto& w : axon) w = dist(rng_);
    for(auto& w : nervous.merge_weights) w = dist(rng_);
}

std::pair<int, Clifford4D::Multivector> CliffordBiocomputer::think(
    const std::vector<double>& input) {

    // 1. Sistema Límbico
    nervous.forward(input, cell.homeostasis);

    // 2. Córtex
    cortex.process(nervous.emotional_state);

    // 3. Produto geométrico global
    auto global_state = Clifford4D::geometric_product(
        Clifford4D::Multivector(nervous.emotional_state),
        cortex.state
    );

    // 4. Decisão (ação baseada na direção do vetor resultante)
    int action_id = 0;
    double max_val = global_state[1];
    for(int i=2; i<5; i++) {
        if(global_state[i] > max_val) { max_val = global_state[i]; action_id = i-1; }
    }

    // 5. Membrana dissipativa: hesitação se norma < threshold
    if(dissipative_membrane(global_state)) {
        action_id = -1; // HESITAÇÃO
    }

    return {action_id, global_state};
}

double CliffordBiocomputer::extract_phase() const {
    auto bivec = Clifford4D::extract_bivector(cortex.state);
    double phase = 0.0;
    for(auto v : bivec) phase += v;
    return std::atan2(phase, Clifford4D::norm(cortex.state));
}

bool CliffordBiocomputer::dissipative_membrane(const Clifford4D::Multivector& state) {
    double n = Clifford4D::norm(state);
    // Hesita se energia baixa ou estado incoerente
    return (cell.homeostasis[7] < 0.2) || (n < 0.5);
}

} // namespace arkhe::core
