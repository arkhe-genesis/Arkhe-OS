#include "ghz7_mesh.h"
#include <stdio.h>
#include <stdlib.h>

#ifdef USE_MPI
#include <mpi.h>
#endif

int mesh_init(int* argc, char*** argv, mesh_node_t* node) {
#ifdef USE_MPI
    MPI_Init(argc, argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &node->rank);
    MPI_Comm_size(MPI_COMM_WORLD, &node->size);
    printf("[MESH] Node %d/%d initialized with MPI.\n", node->rank, node->size);
#else
    node->rank = 0;
    node->size = 1;
    printf("[MESH] Node initialized in standalone mode.\n");
#endif
    node->local_coherence = 1.0f;
    return 0;
}

int mesh_sync_ghz7(mesh_node_t* node) {
    printf("[MESH] Node %d participating in GHZ7 synchronization...\n", node->rank);
#ifdef USE_MPI
    float global_coherence;
    MPI_Allreduce(&node->local_coherence, &global_coherence, 1, MPI_FLOAT, MPI_MIN, MPI_COMM_WORLD);
    node->local_coherence = global_coherence;
    printf("[MESH] Global coherence synced: %.3f\n", global_coherence);
#endif
    return 0;
}

void mesh_cleanup(void) {
#ifdef USE_MPI
    MPI_Finalize();
#endif
}
