#pragma HLS INTERFACE s_axilite port=return bundle=control
#pragma HLS INTERFACE s_axilite port=variant_id bundle=control
#pragma HLS INTERFACE s_axilite port=latency_us bundle=control
#pragma HLS INTERFACE s_axilite port=power_mw bundle=control
#pragma HLS INTERFACE s_axilite port=epsilon bundle=control
#pragma HLS INTERFACE s_axilite port=selected_id bundle=control

#include <ap_int.h>
#include <ap_fixed.h>
#include <cmath>

// Fixed-point types for FPGA efficiency
typedef ap_fixed<16, 8> fix16_8;   // 8 integer, 8 fractional bits
typedef ap_fixed<24, 16> fix24_16; // for intermediate calculations

struct KernelVariant {
    #pragma HLS PACK_BIT
    ap_uint<16> variant_id;
    ap_uint<8> block_dim;
    ap_uint<8> tile_size;
    ap_uint<8> unroll_factor;
    ap_uint<16> shared_mem_bytes;
    ap_uint<8> register_count;

    // Static bounds (from verification)
    fix16_8 verified_latency_us;
    fix16_8 verified_power_mw;

    // Dynamic tracking
    ap_uint<16> total_launches;
    fix24_16 cumulative_reward;
    fix24_16 sum_squared_reward;
    fix16_8 last_latency_us;
    fix16_8 last_power_mw;
    fix16_8 last_epsilon;

    fix16_8 mean_reward() const {
        return total_launches > 0 ? cumulative_reward / total_launches : fix16_8(0);
    }
};

class UCB1BanditFPGA {
private:
    static const int MAX_VARIANTS = 64;
    KernelVariant variants[MAX_VARIANTS];
    int num_variants;

    // Reward parameters (compile-time constants for HLS)
    static constexpr fix16_8 W_LAT = fix16_8(0.4);
    static constexpr fix16_8 W_POW = fix16_8(0.3);
    static constexpr fix16_8 W_MER = fix16_8(0.3);
    static constexpr fix16_8 LAT_BL = fix16_8(500.0);
    static constexpr fix16_8 POW_BL = fix16_8(150.0);
    static constexpr fix16_8 MER_TARGET = fix16_8(0.07);
    static constexpr fix16_8 MER_PENALTY = fix16_8(2.0);
    static constexpr fix16_8 EPS_MIN = fix16_8(0.04);
    static constexpr fix16_8 EPS_MAX = fix16_8(0.10);
    static constexpr fix16_8 EXPLORATION_C = fix16_8(2.0);

    fix16_8 compute_reward(fix16_8 latency, fix16_8 power, fix16_8 epsilon) {
        // Latency score: 1 if fast, 0 if slow
        fix16_8 lat_score = fix16_8(1.0) - ap_min(ap_max(latency / (fix16_8(2.0) * LAT_BL), fix16_8(0.0)), fix16_8(1.0));

        // Power score
        fix16_8 pow_score = fix16_8(1.0) - ap_min(ap_max(power / (fix16_8(2.0) * POW_BL), fix16_8(0.0)), fix16_8(1.0));

        // Mercy score: piecewise
        fix16_8 mer_score;
        if (epsilon >= EPS_MIN && epsilon <= EPS_MAX) {
            mer_score = fix16_8(1.0) - ap_abs(epsilon - MER_TARGET) / fix16_8(0.03);
        } else {
            fix16_8 dist = ap_min(ap_abs(epsilon - EPS_MIN), ap_abs(epsilon - EPS_MAX));
            mer_score = -MER_PENALTY * dist;
        }

        // Weighted sum, clipped
        fix16_8 reward = W_LAT * lat_score + W_POW * pow_score + W_MER * mer_score;
        return ap_min(ap_max(reward, fix16_8(0.0)), fix16_8(1.0));
    }

public:
    void init(KernelVariant* var_array, int n) {
        #pragma HLS INLINE
        num_variants = ap_min(n, MAX_VARIANTS);
        for (int i = 0; i < num_variants; i++) {
            #pragma HLS PIPELINE
            variants[i] = var_array[i];
            // Warm-start
            variants[i].total_launches = 2;
            variants[i].cumulative_reward = fix24_16(0.5) * 2;
            variants[i].sum_squared_reward = fix24_16(0.25) * 2;
        }
    }

    ap_uint<16> select_variant() {
        #pragma HLS INLINE
        ap_uint<16> best_id = 0;
        fix24_16 best_ucb = fix24_16(-1e10);
        int total_launches = 0;

        // Count total launches
        for (int i = 0; i < num_variants; i++) {
            #pragma HLS UNROLL
            total_launches += variants[i].total_launches;
        }

        for (int i = 0; i < num_variants; i++) {
            #pragma HLS PIPELINE
            KernelVariant& var = variants[i];

            // Safety mask
            if (var.total_launches > 0) {
                if (var.last_epsilon < EPS_MIN || var.last_epsilon > EPS_MAX) {
                    continue;
                }
            }

            // UCB calculation
            fix24_16 ucb;
            if (var.total_launches == 0) {
                ucb = fix24_16(1e10); // force exploration
            } else {
                fix16_8 mean_r = var.mean_reward();
                fix16_8 log_total = fix16_8(std::log(ap_max(total_launches, 1)));
                fix16_8 exploration = EXPLORATION_C * ap_sqrt(
                    fix16_8(2.0) * log_total / fix16_8(var.total_launches)
                );
                ucb = fix24_16(mean_r) + fix24_16(exploration);
            }

            if (ucb > best_ucb) {
                best_ucb = ucb;
                best_id = var.variant_id;
            }
        }

        // Fallback if all unsafe
        if (best_ucb < fix24_16(0)) {
            fix16_8 best_mean = fix16_8(-1e10);
            for (int i = 0; i < num_variants; i++) {
                #pragma HLS UNROLL
                if (variants[i].total_launches > 0) {
                    fix16_8 m = variants[i].mean_reward();
                    if (m > best_mean) {
                        best_mean = m;
                        best_id = variants[i].variant_id;
                    }
                }
            }
        }

        return best_id;
    }

    void update(ap_uint<16> variant_id, fix16_8 latency, fix16_8 power, fix16_8 epsilon) {
        #pragma HLS INLINE
        for (int i = 0; i < num_variants; i++) {
            #pragma HLS PIPELINE
            if (variants[i].variant_id == variant_id) {
                KernelVariant& var = variants[i];
                fix16_8 reward = compute_reward(latency, power, epsilon);

                var.total_launches++;
                var.cumulative_reward += fix24_16(reward);
                var.sum_squared_reward += fix24_16(reward * reward);
                var.last_latency_us = latency;
                var.last_power_mw = power;
                var.last_epsilon = epsilon;
                break;
            }
        }
    }
};
