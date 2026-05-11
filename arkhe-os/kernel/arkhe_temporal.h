#ifndef ARKHE_TEMPORAL_H
#define ARKHE_TEMPORAL_H

#include <linux/types.h>

#define ARKHE_HASH_SIZE 32
#define ARKHE_MAX_BLOCK_SIZE 1048576
#define ARKHE_HASH_TABLE_BITS 10
#define ARKHE_HASH_TABLE_SIZE (1 << ARKHE_HASH_TABLE_BITS)
#define ARKHE_MAX_BLOCKS 1000000

#define IPPROTO_ARKHE 253
#define ARKHE_MAGIC 0xCA71
#define ARKHE_VERSION 4

struct arkhe_header {
    __be16 magic;
    __u8 version;
    __u8 checksum;
};

#endif
