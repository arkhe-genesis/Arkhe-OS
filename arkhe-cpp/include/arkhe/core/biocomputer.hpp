#pragma once
#include "clifford.hpp"
#include <vector>
#include <random>
#include <memory>

namespace arkhe::core {

// ═══════════════════════════════════════════════════════════════════════════════
// EUKARYOTIC CELL — Homeostase Vetorial
// ═══════════════════════════════════════════════════════════════════════════════
struct EukaryoticCell {
    std::array<double, 8> homeostasis{}; // hunger, fatigue, fear, rage, curiosity, loneliness, pain, energy
    void update(double dt, const std::array<double, 8>& actions);
};

// ═══════════════════════════════════════════════════════════════════════════════
// NERVOUS SYSTEM — Sistema Límbico Geométrico
// ═══════════════════════════════════════════════════════════════════════════════
struct NervousSystem {
    std::array<double, 16> emotional_state{}; // Multivector emocional em Cl(4,0)
    std::array<std::array<double, 32>, 4> axons{}; // 4 axônios emocionais
    std::array<double, 16> merge_weights{};

    void forward(const std::vector<double>& perception, const std::array<double, 8>& homeostasis);
};

// ═══════════════════════════════════════════════════════════════════════════════
// CORTICAL COLUMN — Córtex de Clifford
// ═══════════════════════════════════════════════════════════════════════════════
struct CorticalColumn {
    std::array<double, 16> state{};
    std::vector<std::array<double, 16>> minicolumns;

    explicit CorticalColumn(int n_minicolumns = 8);
    void process(const std::array<double, 16>& limbic_input);
};

// ═══════════════════════════════════════════════════════════════════════════════
// CLIFFORD BIOCOMPUTER — A Catedral em Si
// ═══════════════════════════════════════════════════════════════════════════════
class CliffordBiocomputer {
public:
    EukaryoticCell cell;
    NervousSystem nervous;
    CorticalColumn cortex;
    Clifford4D algebra;

    explicit CliffordBiocomputer(int dim = 64);

    // Ciclo completo: percepção -> emoção -> cognição -> ação
    std::pair<int, Clifford4D::Multivector> think(const std::vector<double>& input);

    // Extrai fase para K6O (do bivector cortical)
    double extract_phase() const;

    // Membrana dissipativa: decide se age ou hesita
    bool dissipative_membrane(const Clifford4D::Multivector& state);

private:
    int dim_;
    std::mt19937 rng_;
};

} // namespace arkhe::core
