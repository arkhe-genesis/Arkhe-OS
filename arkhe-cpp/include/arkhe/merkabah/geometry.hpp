#pragma once
#include "arkhe/core/clifford.hpp"
#include <vector>
#include <string>

namespace arkhe::merkabah {

// ═══════════════════════════════════════════════════════════════════════════════
// MERKABAH GEOMETRY — Projeção Estereográfica do Estado da Catedral
// ═══════════════════════════════════════════════════════════════════════════════
struct MerkabahFrame {
    double timestamp;
    std::vector<std::array<double,3>> solar;      // 4 vértices
    std::vector<std::array<double,3>> lunar;      // 4 vértices
    std::vector<std::array<double,3>> octahedron; // 6 vértices
    double rotation;
    double coherence;
    double global_phase;
    double energy;
    bool hesitating;

    std::string to_json() const;
};

class MerkabahGeometry {
public:
    explicit MerkabahGeometry(double scale = 2.0);

    MerkabahFrame from_state(double time, double r, double psi, double energy,
                               bool hesitating, const core::Clifford4D::Multivector& cortical);

private:
    double scale_;
    std::vector<std::array<double,3>> base_solar_;
    std::vector<std::array<double,3>> base_lunar_;

    std::vector<std::array<double,3>> rotate_y(const std::vector<std::array<double,3>>& pts, double angle);
};

} // namespace arkhe::merkabah
