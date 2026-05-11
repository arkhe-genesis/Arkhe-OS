#ifndef ARKHE_CONSENSUS_H
#define ARKHE_CONSENSUS_H

#include <linux/types.h>

#define ARKHE_ADDR_SIZE 32
#define ARKHE_MAX_COST 1000000
#define ARKHE_MIN_SCORE 0
#define ARKHE_BLOCK_INTERVAL 1000
#define ARKHE_MAX_EPOCH_DIFF 10
#define ARKHE_MAX_PAYLOAD_SIZE 65536
#define ARKHE_QUANTUM_TOLERANCE_NS 1000000

#define ARKHE_VIOL_LOOP (1 << 0)
#define ARKHE_VIOL_PARADOX_TEMP (1 << 1)
#define ARKHE_VIOL_PARADOX_CAUSAL (1 << 2)
#define ARKHE_VIOL_ENTROPY (1 << 3)
#define ARKHE_VIOL_STALE (1 << 4)
#define ARKHE_VIOL_TEMPORAL (1 << 5)
#define ARKHE_VIOL_SOLAR_SWITCHBACK (1 << 6)

struct arkhe_message {
    __u8 sender[ARKHE_ADDR_SIZE];
    __u8 receiver[ARKHE_ADDR_SIZE];
    __u64 source_ts;
    __u64 target_ts;
    __u32 content_len;
    __u32 payload_len;
    __u32 zk_proof_len;
};

struct arkhe_eval_context {
    __u64 accumulated_cost;
    __u64 current_epoch;
};

struct arkhe_solar_state {
    __u8 switchback_active;
    __u8 severity;
};

#endif
