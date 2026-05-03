#include <cmath>

#define NUM_VARIANTS 16
#define WARM_START_LAUNCHES 2
#define WARM_START_REWARD 0.5f

struct KernelVariant {
    int variant_id;
    int total_launches;
    float cumulative_reward;
    float sum_squared_reward;
    float last_epsilon;
};

void ucb1_bandit_fpga(
    KernelVariant variants[NUM_VARIANTS],
    float exploration_constant,
    float eps_min,
    float eps_max,
    int* selected_variant_id
) {
    #pragma HLS INTERFACE s_axilite port=return bundle=CTRL_BUS
    #pragma HLS INTERFACE m_axi port=variants offset=slave bundle=DATA_BUS
    #pragma HLS INTERFACE s_axilite port=exploration_constant bundle=CTRL_BUS
    #pragma HLS INTERFACE s_axilite port=eps_min bundle=CTRL_BUS
    #pragma HLS INTERFACE s_axilite port=eps_max bundle=CTRL_BUS
    #pragma HLS INTERFACE s_axilite port=selected_variant_id bundle=CTRL_BUS

    int total_launches_all = 0;

    // Compute total launches
    for (int i = 0; i < NUM_VARIANTS; i++) {
        #pragma HLS PIPELINE II=1
        total_launches_all += variants[i].total_launches;
    }

    int best_id = -1;
    float best_ucb = -1000000.0f;

    for (int i = 0; i < NUM_VARIANTS; i++) {
        #pragma HLS PIPELINE II=1

        KernelVariant var = variants[i];

        // Safety mask
        bool is_safe = (var.total_launches == 0) || (var.last_epsilon >= eps_min && var.last_epsilon <= eps_max);

        if (is_safe) {
            float ucb;
            if (var.total_launches == 0) {
                ucb = 1000000.0f; // Force exploration
            } else {
                float mean_reward = var.cumulative_reward / var.total_launches;
                float exploration_bonus = exploration_constant * sqrt((2.0f * log((float)(total_launches_all > 0 ? total_launches_all : 1))) / var.total_launches);
                ucb = mean_reward + exploration_bonus;
            }

            if (ucb > best_ucb) {
                best_ucb = ucb;
                best_id = var.variant_id;
            }
        }
    }

    // Fallback if none found
    if (best_id == -1) {
        float best_mean = -1000000.0f;
        for (int i = 0; i < NUM_VARIANTS; i++) {
            #pragma HLS PIPELINE II=1
            KernelVariant var = variants[i];
            if (var.total_launches > 0) {
                float mean_reward = var.cumulative_reward / var.total_launches;
                if (mean_reward > best_mean) {
                    best_mean = mean_reward;
                    best_id = var.variant_id;
                }
            }
        }
    }

    // Last resort
    if (best_id == -1) {
        best_id = variants[0].variant_id;
    }

    *selected_variant_id = best_id;
}
