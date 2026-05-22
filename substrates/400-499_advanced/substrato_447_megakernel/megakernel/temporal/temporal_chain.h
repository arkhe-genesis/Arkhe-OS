#ifndef TEMPORAL_CHAIN_H
#define TEMPORAL_CHAIN_H

#include "../megakernel.h"

int temporal_anchor_state(megakernel_t* mk);
double temporal_last_anchor_time(void);
int temporal_checkpoint(void);

#endif
