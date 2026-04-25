#include "arkhe/zk/allocator.hpp"
#include <cstdlib>
#include <cstring>
#include <iostream>

namespace arkhe::zk {

ZKAllocator::ZKAllocator() {
    small_pool_ = create_pool(4096, 1024);   // 4KB blocks
    medium_pool_ = create_pool(65536, 128);  // 64KB blocks
    large_pool_ = create_pool(1048576, 16);  // 1MB blocks
}

ZKAllocator::~ZKAllocator() {
    destroy_pool(small_pool_);
    destroy_pool(medium_pool_);
    destroy_pool(large_pool_);
}

zk_pool_t* ZKAllocator::create_pool(size_t block_size, size_t blocks_total) {
    zk_pool_t* pool = (zk_pool_t*)malloc(sizeof(zk_pool_t));
    pool->block_size = block_size;
    pool->blocks_total = blocks_total;
    pool->blocks_free = blocks_total;
    pool->memory = malloc(block_size * blocks_total);
    pool->free_list = (uint32_t*)malloc(sizeof(uint32_t) * ((blocks_total + 31) / 32));
    memset(pool->free_list, 0xFF, sizeof(uint32_t) * ((blocks_total + 31) / 32));
    pthread_mutex_init(&pool->lock, nullptr);
    return pool;
}

void ZKAllocator::destroy_pool(zk_pool_t* pool) {
    if (!pool) return;
    pthread_mutex_destroy(&pool->lock);
    free(pool->memory);
    free(pool->free_list);
    free(pool);
}

void* ZKAllocator::alloc_secure(size_t size, const char* purpose) {
    zk_pool_t* pool = nullptr;
    if (size <= 4096) pool = small_pool_;
    else if (size <= 65536) pool = medium_pool_;
    else if (size <= 1048576) pool = large_pool_;

    if (!pool) return nullptr;

    pthread_mutex_lock(&pool->lock);
    for (size_t i = 0; i < pool->blocks_total; ++i) {
        if (pool->free_list[i / 32] & (1 << (i % 32))) {
            pool->free_list[i / 32] &= ~(1 << (i % 32));
            pool->blocks_free--;
            void* ptr = (uint8_t*)pool->memory + (i * pool->block_size);
            pthread_mutex_unlock(&pool->lock);

            // Zero memory para segurança criptográfica
            memset(ptr, 0, pool->block_size);
            return ptr;
        }
    }
    pthread_mutex_unlock(&pool->lock);
    return nullptr;
}

void ZKAllocator::free_secure(void* ptr) {
    auto try_free = [&](zk_pool_t* pool) {
        if (!pool) return false;
        uint8_t* start = (uint8_t*)pool->memory;
        uint8_t* end = start + (pool->block_size * pool->blocks_total);
        if ((uint8_t*)ptr >= start && (uint8_t*)ptr < end) {
            size_t i = ((uint8_t*)ptr - start) / pool->block_size;
            pthread_mutex_lock(&pool->lock);
            pool->free_list[i / 32] |= (1 << (i % 32));
            pool->blocks_free++;
            pthread_mutex_unlock(&pool->lock);
            return true;
        }
        return false;
    };

    if (try_free(small_pool_)) return;
    if (try_free(medium_pool_)) return;
    if (try_free(large_pool_)) return;
}

} // namespace arkhe::zk
