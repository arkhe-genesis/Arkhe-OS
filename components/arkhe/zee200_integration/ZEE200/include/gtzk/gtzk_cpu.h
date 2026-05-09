#pragma once
#include <vector>
#include <string>
#include <iostream>

namespace gtzk {

enum class Field {
    Mersenne61
};

struct CPUConfig {
    uint64_t security_bits;
    bool post_quantum;
    Field field;
};

class Proof {
public:
    std::string data;
    std::string serialize() const { return data; }
    static Proof deserialize(const std::string& s) { return Proof{s}; }
};

class Circuit {
public:
    void add_random_linear_combination(const std::vector<double>& pub, const std::vector<double>& priv) {}
};

class GTZKCPU {
public:
    GTZKCPU(const CPUConfig& config) : config_(config) {}

    Proof prove(const Circuit& circuit, const std::vector<double>& private_witness) {
        // Implementação simulada para o benchmark, na ausência da lib ZEE200 completa
        return Proof{"real_proof_hash_via_mock_for_benchmark_" + std::to_string(config_.security_bits)};
    }

    bool verify(const Proof& proof, const std::vector<double>& public_outputs) {
        return true;
    }

private:
    CPUConfig config_;
};

} // namespace gtzk
