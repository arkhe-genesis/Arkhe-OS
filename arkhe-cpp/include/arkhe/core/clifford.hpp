#pragma once
#include <array>
#include <cmath>
#include <numeric>
#include <algorithm>
#include <string>
#include "arkhe/core/clifford_asm.h"

namespace arkhe::core {

// ═══════════════════════════════════════════════════════════════════════════════
// CLIFFORD 4D — Cl(4,0) — O Substrato Geométrico da Catedral
// ═══════════════════════════════════════════════════════════════════════════════
// Grades: 0(escalar) + 4(vetor) + 6(bivector) + 4(trivector) + 1(pseudoscalar) = 16
// ═══════════════════════════════════════════════════════════════════════════════

class Clifford4D {
public:
    static constexpr int DIM = 4;
    static constexpr int SIZE = 16;
    static constexpr std::array<int, 5> GRADE_SIZES = {1, 4, 6, 4, 1};

    using Multivector = std::array<double, SIZE>;

    Clifford4D() = default;

    // Produto geométrico completo (simplificado para grades 0,1,2)
    static Multivector geometric_product(const Multivector& a, const Multivector& b) {
        Multivector result{};
        // Invocando a Muralha de Quartzo diretamente no coração do processador.
        clifford_geometric_product(a.data(), b.data(), result.data());
        return result;
    }

    // Produto interno (parte escalar + vetorial)
    static double scalar_product(const Multivector& a, const Multivector& b) {
        double s = a[0]*b[0];
        for(int i=1;i<5;i++) s += a[i]*b[i];
        return s;
    }

    // Extrai bivector (grades 2) — usado pelo K6O para fase
    static std::array<double, 6> extract_bivector(const Multivector& mv) {
        std::array<double, 6> b;
        for(int i=0;i<6;i++) b[i] = mv[5+i];
        return b;
    }

    // Norma
    static double norm(const Multivector& mv) {
        double n = 0.0;
        for(auto v : mv) n += v*v;
        return std::sqrt(n);
    }

    // Rotação via rotor (simplificada: rotação em plano ij por ângulo)
    static Multivector rotate(const Multivector& mv, int i, int j, double angle) {
        // Aplicação simplificada: apenas perturba componentes relevantes
        Multivector result = mv;
        double c = std::cos(angle);
        double s = std::sin(angle);
        int idx1 = 1 + i;
        int idx2 = 1 + j;
        double v1 = mv[idx1];
        double v2 = mv[idx2];
        result[idx1] = c*v1 - s*v2;
        result[idx2] = s*v1 + c*v2;
        return result;
    }

    static Multivector zero() {
        Multivector z{};
        return z;
    }

    static Multivector scalar(double s) {
        Multivector z{};
        z[0] = s;
        return z;
    }

    static Multivector vector(double x, double y, double z, double w) {
        Multivector m{};
        m[0] = 0; m[1]=x; m[2]=y; m[3]=z; m[4]=w;
        return m;
    }
};

} // namespace arkhe::core
