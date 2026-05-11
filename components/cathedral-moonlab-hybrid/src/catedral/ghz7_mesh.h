#ifndef GHZ7_MESH_H
#define GHZ7_MESH_H

#include <stdint.h>

typedef struct {
    int rank;
    int size;
    float local_coherence;
} mesh_node_t;

int mesh_init(int* argc, char*** argv, mesh_node_t* node);
int mesh_sync_ghz7(mesh_node_t* node);
void mesh_cleanup(void);

#endif // GHZ7_MESH_H
