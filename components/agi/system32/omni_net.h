#ifndef OMNI_NET_H
#define OMNI_NET_H

typedef struct OmniNetContext OmniNetContext;

OmniNetContext* omninet_create_context(const char *config_path);
void omninet_sync_channels(OmniNetContext *ctx, int steps);
void omninet_destroy_context(OmniNetContext *ctx);

#endif
