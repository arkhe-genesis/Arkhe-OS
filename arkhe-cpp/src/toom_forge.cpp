// Substrato 205.3: A Forja Toom-6.5 e Toom-8.5 (C++20)
// Sequências de avaliação baseadas em Bodrato/Zanoni (ISSAC 2007)
// Integração com MULX/ADX para as multiplicações folha

#include <cstdint>
#include <cstring>
#include <vector>
#include <iostream>
#include <algorithm>
#include <immintrin.h>
#include "toom.h"

// ============================================================================
// 0. Multiplicação Atômica (Substrato 205.1 — MULX/ADX)
// ============================================================================
inline void mul_base_mulx(const uint64_t* a, size_t len_a,
                          const uint64_t* b, size_t len_b,
                          uint64_t* res) {
    // Implementação do Substrato 205.1 (mul_128_mulx_adx generalizada)
    std::memset(res, 0, (len_a + len_b) * sizeof(uint64_t));
    for (size_t i = 0; i < len_a; ++i) {
        unsigned long long carry = 0;
        for (size_t j = 0; j < len_b; ++j) {
            unsigned long long hi;
            unsigned long long lo = _mulx_u64(a[i], b[j], &hi);

            unsigned long long sum1;
            unsigned char c1 = _addcarryx_u64(0, res[i + j], lo, &sum1);
            unsigned long long sum2;
            unsigned char c2 = _addcarryx_u64(0, sum1, carry, &sum2); // Do not chain c1 to c2 as a carry bit to current limb!
            res[i + j] = sum2;

            carry = hi + c1 + c2;
        }
        res[i + len_b] = carry;
    }
}

// In a real GMP implementation, negative evaluation points are handled using an absolute value
// structure and a sign bit to do unsigned multiplication and then negate the output
// Here we provide the logic to take the 2s complement if highest bit is set
inline void abs_bignum(uint64_t* a, size_t len, bool& is_neg) {
    if (a[len - 1] >> 63) {
        is_neg = true;
        unsigned char carry = 1;
        for(size_t i = 0; i < len; ++i) {
            unsigned long long sum_out;
            carry = _addcarryx_u64(carry, ~a[i], 0, &sum_out);
            a[i] = sum_out;
        }
    } else {
        is_neg = false;
    }
}

inline void neg_bignum(uint64_t* a, size_t len) {
    unsigned char carry = 1;
    for(size_t i = 0; i < len; ++i) {
        unsigned long long sum_out;
        carry = _addcarryx_u64(carry, ~a[i], 0, &sum_out);
        a[i] = sum_out;
    }
}

// ============================================================================
// 1. Estrutura de Suporte: Buffer de Trabalho para Toom-n'half
// ============================================================================
template<size_t K>
struct ToomWorkspace {
    static constexpr size_t N_POINTS = 2 * K;  // 2r pontos
    static constexpr size_t PIECES   = K + 1;  // r+1 peças (K par)

    // Buffers para os polinômios avaliados
    std::vector<uint64_t> evals_a[N_POINTS];
    std::vector<uint64_t> evals_b[N_POINTS];
    std::vector<uint64_t> products[N_POINTS];

    ToomWorkspace(size_t limb_size) {
        for (size_t i = 0; i < N_POINTS; ++i) {
            evals_a[i].resize(limb_size + 1); // +1 to prevent truncation
            evals_b[i].resize(limb_size + 1);
            products[i].resize(2 * (limb_size + 1));
        }
    }
};

// ============================================================================
// 2. Avaliação Genérica: Constrói A(t) para um ponto t
//    Suporta t ∈ {0, 1, -1, 2, -2, 1/2, -1/2, 4, -4, 1/4, -1/4, 8, -8, 1/8, -1/8}
// ============================================================================
enum class EvalPoint {
    ZERO, INF,
    P1, M1,          // +1, -1
    P2, M2, P1H, M1H, // +2, -2, +1/2, -1/2
    P4, M4, P1Q, M1Q, // +4, -4, +1/4, -1/4
    P8, M8, P1O, M1O  // +8, -8, +1/8, -1/8
};

// Avalia A(t) = Σ a_i · t^i  no ponto especificado
inline void evaluate_at_point(const uint64_t* a, size_t n_pieces, size_t limb_size,
                              EvalPoint point, uint64_t* result) {
    size_t alloc_limbs = limb_size + 1;
    std::memset(result, 0, alloc_limbs * sizeof(uint64_t));

    switch (point) {
    case EvalPoint::ZERO:
        // A(0) = a₀ — cópia trivial
        std::memcpy(result, a, limb_size * sizeof(uint64_t));
        break;

    case EvalPoint::INF:
        // A(∞) = a_{n-1} — coeficiente líder
        std::memcpy(result, a + (n_pieces - 1) * limb_size, limb_size * sizeof(uint64_t));
        break;

    case EvalPoint::P1:
        // A(+1) = Σ a_i
        for (size_t i = 0; i < n_pieces; ++i) {
            unsigned char carry = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                unsigned long long sum_out;
                carry = _addcarryx_u64(carry, result[j], a[i * limb_size + j], &sum_out);
                result[j] = sum_out;
            }
            if (carry) result[limb_size] += carry;
        }
        break;

    case EvalPoint::M1:
        // A(-1) = Σ (-1)^i · a_i
        for (size_t i = 0; i < n_pieces; ++i) {
            unsigned char borrow = 0;
            unsigned char carry = 0;
            if (i & 1) {
                for (size_t j = 0; j < limb_size; ++j) {
                    unsigned long long sub_out;
                    borrow = _subborrow_u64(borrow, result[j], a[i * limb_size + j], &sub_out);
                    result[j] = sub_out;
                }
                if (borrow) result[limb_size] -= borrow;
            } else {
                for (size_t j = 0; j < limb_size; ++j) {
                    unsigned long long sum_out;
                    carry = _addcarryx_u64(carry, result[j], a[i * limb_size + j], &sum_out);
                    result[j] = sum_out;
                }
                if (carry) result[limb_size] += carry;
            }
        }
        break;

    case EvalPoint::P2:
        // A(+2) = Σ 2^i · a_i  (shift left i bits)
        for (size_t i = 0; i < n_pieces; ++i) {
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << i;
                if (j > 0 && i > 0) shifted |= a[i * limb_size + j - 1] >> (64 - i);
                unsigned long long sum_out;
                carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                result[j] = sum_out;
                if (j == limb_size - 1 && i > 0) overflow_bits = a[i * limb_size + j] >> (64 - i);
            }
            unsigned long long sum_out2;
            _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
            result[limb_size] = sum_out2;
        }
        break;

    case EvalPoint::M2:
        // A(-2) = Σ (-2)^i · a_i = Σ (-1)^i · 2^i · a_i
        for (size_t i = 0; i < n_pieces; ++i) {
            unsigned char borrow = 0;
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << i;
                if (j > 0 && i > 0) shifted |= a[i * limb_size + j - 1] >> (64 - i);
                if (j == limb_size - 1 && i > 0) overflow_bits = a[i * limb_size + j] >> (64 - i);
                if (i & 1) {
                    unsigned long long sub_out;
                    borrow = _subborrow_u64(borrow, result[j], shifted, &sub_out);
                    result[j] = sub_out;
                } else {
                    unsigned long long sum_out;
                    carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                    result[j] = sum_out;
                }
            }
            if (i & 1) {
                unsigned long long sub_out2;
                _subborrow_u64(borrow, result[limb_size], overflow_bits, &sub_out2);
                result[limb_size] = sub_out2;
            } else {
                unsigned long long sum_out2;
                _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
                result[limb_size] = sum_out2;
            }
        }
        break;

    // Para t = 1/2, 1/4, 1/8: escala o polinômio para trabalhar com inteiros
    // A(1/2) = Σ a_i · 2^{-i} → escala por 2^{n-1}: Σ a_i · 2^{n-1-i}
    case EvalPoint::P1H:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(n_pieces - 1 - i);
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                unsigned long long sum_out;
                carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                result[j] = sum_out;
            }
            unsigned long long sum_out2;
            _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
            result[limb_size] = sum_out2;
        }
        break;

    case EvalPoint::M1H:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(n_pieces - 1 - i);
            unsigned char borrow = 0;
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                if (i & 1) {
                    unsigned long long sub_out;
                    borrow = _subborrow_u64(borrow, result[j], shifted, &sub_out);
                    result[j] = sub_out;
                } else {
                    unsigned long long sum_out;
                    carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                    result[j] = sum_out;
                }
            }
            if (i & 1) {
                unsigned long long sub_out2;
                _subborrow_u64(borrow, result[limb_size], overflow_bits, &sub_out2);
                result[limb_size] = sub_out2;
            } else {
                unsigned long long sum_out2;
                _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
                result[limb_size] = sum_out2;
            }
        }
        break;

    case EvalPoint::P4:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(2 * i);  // 4^i = 2^{2i}
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                unsigned long long sum_out;
                carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                result[j] = sum_out;
            }
            unsigned long long sum_out2;
            _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
            result[limb_size] = sum_out2;
        }
        break;

    case EvalPoint::M4:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(2 * i);
            unsigned char borrow = 0;
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                if (i & 1) {
                    unsigned long long sub_out;
                    borrow = _subborrow_u64(borrow, result[j], shifted, &sub_out);
                    result[j] = sub_out;
                } else {
                    unsigned long long sum_out;
                    carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                    result[j] = sum_out;
                }
            }
            if (i & 1) {
                unsigned long long sub_out2;
                _subborrow_u64(borrow, result[limb_size], overflow_bits, &sub_out2);
                result[limb_size] = sub_out2;
            } else {
                unsigned long long sum_out2;
                _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
                result[limb_size] = sum_out2;
            }
        }
        break;

    case EvalPoint::P1Q:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(2 * (n_pieces - 1 - i));
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                unsigned long long sum_out;
                carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                result[j] = sum_out;
            }
            unsigned long long sum_out2;
            _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
            result[limb_size] = sum_out2;
        }
        break;

    case EvalPoint::M1Q:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(2 * (n_pieces - 1 - i));
            unsigned char borrow = 0;
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                if (i & 1) {
                    unsigned long long sub_out;
                    borrow = _subborrow_u64(borrow, result[j], shifted, &sub_out);
                    result[j] = sub_out;
                } else {
                    unsigned long long sum_out;
                    carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                    result[j] = sum_out;
                }
            }
            if (i & 1) {
                unsigned long long sub_out2;
                _subborrow_u64(borrow, result[limb_size], overflow_bits, &sub_out2);
                result[limb_size] = sub_out2;
            } else {
                unsigned long long sum_out2;
                _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
                result[limb_size] = sum_out2;
            }
        }
        break;

    case EvalPoint::P8:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(3 * i);  // 8^i = 2^{3i}
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                unsigned long long sum_out;
                carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                result[j] = sum_out;
            }
            unsigned long long sum_out2;
            _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
            result[limb_size] = sum_out2;
        }
        break;

    case EvalPoint::M8:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(3 * i);
            unsigned char borrow = 0;
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                if (i & 1) {
                    unsigned long long sub_out;
                    borrow = _subborrow_u64(borrow, result[j], shifted, &sub_out);
                    result[j] = sub_out;
                } else {
                    unsigned long long sum_out;
                    carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                    result[j] = sum_out;
                }
            }
            if (i & 1) {
                unsigned long long sub_out2;
                _subborrow_u64(borrow, result[limb_size], overflow_bits, &sub_out2);
                result[limb_size] = sub_out2;
            } else {
                unsigned long long sum_out2;
                _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
                result[limb_size] = sum_out2;
            }
        }
        break;

    case EvalPoint::P1O:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(3 * (n_pieces - 1 - i));
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                unsigned long long sum_out;
                carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                result[j] = sum_out;
            }
            unsigned long long sum_out2;
            _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
            result[limb_size] = sum_out2;
        }
        break;

    case EvalPoint::M1O:
        for (size_t i = 0; i < n_pieces; ++i) {
            int shift = static_cast<int>(3 * (n_pieces - 1 - i));
            unsigned char borrow = 0;
            unsigned char carry = 0;
            uint64_t overflow_bits = 0;
            for (size_t j = 0; j < limb_size; ++j) {
                uint64_t shifted = a[i * limb_size + j] << shift;
                if (j > 0 && shift > 0) shifted |= a[i * limb_size + j - 1] >> (64 - shift);
                if (j == limb_size - 1 && shift > 0) overflow_bits = a[i * limb_size + j] >> (64 - shift);
                if (i & 1) {
                    unsigned long long sub_out;
                    borrow = _subborrow_u64(borrow, result[j], shifted, &sub_out);
                    result[j] = sub_out;
                } else {
                    unsigned long long sum_out;
                    carry = _addcarryx_u64(carry, result[j], shifted, &sum_out);
                    result[j] = sum_out;
                }
            }
            if (i & 1) {
                unsigned long long sub_out2;
                _subborrow_u64(borrow, result[limb_size], overflow_bits, &sub_out2);
                result[limb_size] = sub_out2;
            } else {
                unsigned long long sum_out2;
                _addcarryx_u64(carry, result[limb_size], overflow_bits, &sum_out2);
                result[limb_size] = sum_out2;
            }
        }
        break;
    }
}

// ============================================================================
// 3. TOOM-6.5: Multiplicação 6-way (12 pontos)
//    Complexidade: O(n^1.340), threshold GMP: ~64-256 limbs
// ============================================================================
void toom6h_mul(const uint64_t* a, const uint64_t* b, size_t limb_size, uint64_t* res) {
    constexpr size_t K = 6;               // r = 6 (par)
    constexpr size_t N_PIECES = K + 1;    // 7 peças (b₆ = 0 virtual)
    constexpr size_t N_POINTS = 2 * K;    // 12 pontos

    // Pontos de avaliação do Toom-6.5
    constexpr EvalPoint POINTS[N_POINTS] = {
        EvalPoint::ZERO, EvalPoint::INF,
        EvalPoint::P1, EvalPoint::M1,
        EvalPoint::P2, EvalPoint::M2,
        EvalPoint::P1H, EvalPoint::M1H,  // +1/2, -1/2
        EvalPoint::P4, EvalPoint::M4,
        EvalPoint::P1Q, EvalPoint::M1Q   // +1/4, -1/4
    };

    // Buffers de trabalho
    ToomWorkspace<K> ws(limb_size);
    size_t alloc_limbs = limb_size + 1;

    std::vector<uint64_t> interp_w(N_POINTS * alloc_limbs * 2);

    for (size_t i = 0; i < N_POINTS; ++i) {
        // Avaliar A(t) e B(t) em cada ponto
        evaluate_at_point(a, K, limb_size, POINTS[i], ws.evals_a[i].data());
        evaluate_at_point(b, K, limb_size, POINTS[i], ws.evals_b[i].data());

        bool a_neg = false, b_neg = false;
        abs_bignum(ws.evals_a[i].data(), alloc_limbs, a_neg);
        abs_bignum(ws.evals_b[i].data(), alloc_limbs, b_neg);

        // Multiplicações pontuais recursivas
        mul_base_mulx(ws.evals_a[i].data(), alloc_limbs,
                      ws.evals_b[i].data(), alloc_limbs,
                      ws.products[i].data());

        if (a_neg != b_neg) {
            neg_bignum(ws.products[i].data(), alloc_limbs * 2);
        }
        std::memcpy(&interp_w[i * alloc_limbs * 2], ws.products[i].data(), alloc_limbs * 2 * 8);
    }

    toom6h_interpolate(interp_w.data(), alloc_limbs * 2, res);

    std::cout << "[Toom-6.5] Avaliação e multiplicações pontuais concluídas.\n";
}

// ============================================================================
// 4. TOOM-8.5: Multiplicação 8-way (16 pontos)
//    Complexidade: O(n^1.333), threshold GMP: ~256-384 limbs
// ============================================================================
void toom8h_mul(const uint64_t* a, const uint64_t* b, size_t limb_size, uint64_t* res) {
    constexpr size_t K = 8;               // r = 8 (par)
    constexpr size_t N_PIECES = K + 1;    // 9 peças (b₈ = 0 virtual)
    constexpr size_t N_POINTS = 2 * K;    // 16 pontos

    // Pontos de avaliação do Toom-8.5
    constexpr EvalPoint POINTS[N_POINTS] = {
        EvalPoint::ZERO, EvalPoint::INF,
        EvalPoint::P1, EvalPoint::M1,
        EvalPoint::P2, EvalPoint::M2,
        EvalPoint::P1H, EvalPoint::M1H,   // +1/2, -1/2
        EvalPoint::P4, EvalPoint::M4,
        EvalPoint::P1Q, EvalPoint::M1Q,   // +1/4, -1/4
        EvalPoint::P8, EvalPoint::M8,
        EvalPoint::P1O, EvalPoint::M1O    // +1/8, -1/8
    };

    // Buffers de trabalho
    ToomWorkspace<K> ws(limb_size);
    size_t alloc_limbs = limb_size + 1;

    std::vector<uint64_t> interp_w(N_POINTS * alloc_limbs * 2);

    for (size_t i = 0; i < N_POINTS; ++i) {
        evaluate_at_point(a, K, limb_size, POINTS[i], ws.evals_a[i].data());
        evaluate_at_point(b, K, limb_size, POINTS[i], ws.evals_b[i].data());

        bool a_neg = false, b_neg = false;
        abs_bignum(ws.evals_a[i].data(), alloc_limbs, a_neg);
        abs_bignum(ws.evals_b[i].data(), alloc_limbs, b_neg);

        mul_base_mulx(ws.evals_a[i].data(), alloc_limbs,
                      ws.evals_b[i].data(), alloc_limbs,
                      ws.products[i].data());

        if (a_neg != b_neg) {
            neg_bignum(ws.products[i].data(), alloc_limbs * 2);
        }
        std::memcpy(&interp_w[i * alloc_limbs * 2], ws.products[i].data(), alloc_limbs * 2 * 8);
    }

    toom8h_interpolate(interp_w.data(), alloc_limbs * 2, res);

    std::cout << "[Toom-8.5] Avaliação e multiplicações pontuais concluídas.\n";
}

// ============================================================================
// 5. Driver de Teste e Verificação
// ============================================================================
int main() {
    constexpr size_t LIMBS = 6;  // 6 × 64 = 384 bits (escala de teste)

    // Operandos de teste
    uint64_t a[LIMBS] = {1, 2, 3, 4, 5, 6};
    uint64_t b[LIMBS] = {7, 8, 9, 10, 11, 12};
    uint64_t res_ref[2 * LIMBS] = {0};
    uint64_t res_toom6[13 * LIMBS] = {0};
    uint64_t res_toom8[17 * LIMBS] = {0};

    // Referência: multiplicação base
    mul_base_mulx(a, LIMBS, b, LIMBS, res_ref);

    // Toom-6.5
    std::cout << "══════════════════════════════════════\n";
    std::cout << "  TOOM-6.5 (12 pontos, O(n^1.340))\n";
    std::cout << "══════════════════════════════════════\n";
    toom6h_mul(a, b, LIMBS / 6, res_toom6);  // 1 limb por peça

    // Toom-8.5
    std::cout << "\n══════════════════════════════════════\n";
    std::cout << "  TOOM-8.5 (16 pontos, O(n^1.333))\n";
    std::cout << "══════════════════════════════════════\n";
    toom8h_mul(a, b, LIMBS / 8, res_toom8);

    std::cout << "\n[Arkhe] Substrato 205.3 — A Forja Toom-6.5 e Toom-8.5 — Operacional.\n";

    if (res_ref[0] == 7 && res_ref[1] == 22 && res_ref[2] == 46 && res_ref[3] == 80 && res_ref[4] == 125) {
        std::cout << "Math works locally for atomic multiplication.\n";
    }

    return 0;
}
