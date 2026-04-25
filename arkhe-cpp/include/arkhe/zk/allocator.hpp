#pragma once
#include <cstdint>
#include <cstddef>
#include <pthread.h>
#include <vector>

namespace arkhe::zk {

typedef struct {
    void* memory;
    size_t block_size;           // Tamanho fixo por pool (ex: 4KB, 64KB)
    size_t blocks_total;
    size_t blocks_free;
    uint32_t* free_list;         // Bitmap de blocos livres
    pthread_mutex_t lock;
} zk_pool_t;

// Pool hierárquico por tipo de witness
class ZKAllocator {
public:
    ZKAllocator();
    ~ZKAllocator();

    void* alloc_secure(size_t size, const char* purpose);
    void free_secure(void* ptr);

private:
    zk_pool_t* create_pool(size_t block_size, size_t blocks_total);
    void destroy_pool(zk_pool_t* pool);

    zk_pool_t* small_pool_;   // 256B - 4KB: scalars, hashes
    zk_pool_t* medium_pool_;  // 4KB - 64KB: activation vectors
    zk_pool_t* large_pool_;   // 64KB+: weight samples, Merkle paths
};

} // namespace arkhe::zk
