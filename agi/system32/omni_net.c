#include "omni_net.h"
#include <stdlib.h>
#include <stdio.h>

struct OmniNetContext {
    int dummy;
};

OmniNetContext* omninet_create_context(const char *config_path) {
    printf("Creating OmniNetContext...\n");
    return malloc(sizeof(OmniNetContext));
}

void omninet_sync_channels(OmniNetContext *ctx, int steps) {
    // dummy sync
}

void omninet_destroy_context(OmniNetContext *ctx) {
    if (ctx) free(ctx);
}
