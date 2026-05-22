#include "temporal_chain.h"

int temporal_anchor_state(megakernel_t* mk) {
    (void)mk;
    return 0;
}

double temporal_last_anchor_time(void) {
    return (double)time(NULL);
}

int temporal_checkpoint(void) {
    return 0;
}