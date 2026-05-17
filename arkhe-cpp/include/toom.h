#pragma once
#include <cstdint>
#include <cstddef>

void toom6h_interpolate(const uint64_t* w, size_t n, uint64_t* c);
void toom8h_interpolate(const uint64_t* w, size_t n, uint64_t* c);
void toom6h_mul(const uint64_t* a, const uint64_t* b, size_t limb_size, uint64_t* res);
void toom8h_mul(const uint64_t* a, const uint64_t* b, size_t limb_size, uint64_t* res);
