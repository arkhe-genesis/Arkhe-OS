#pragma once
#include "arkhe/core/arena.hpp"
#include <string>
#include <vector>

namespace arkhe::mind {

class CathedralLLM {
public:
    explicit CathedralLLM(core::cathedral_arena_t* arena);
    ~CathedralLLM() = default;

    std::string generate(const std::string& prompt);

    struct Token {
        int id;
        float logit;
    };

private:
    core::cathedral_arena_t* arena_;
    Token* kv_cache_;
    size_t cache_size_;
};

} // namespace arkhe::mind
