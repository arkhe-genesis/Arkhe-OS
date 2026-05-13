#ifndef ARK_CPP_STD_CORE_TYPES_HPP
#define ARK_CPP_STD_CORE_TYPES_HPP

#include <cstdint>
#include <string>
#include <vector>

namespace ark {

using Int = int64_t;
using Float = double;
using Bool = bool;
using String = std::string;
using Byte = uint8_t;

// A Qubit collapses on destruction or measurement.
class Qubit {
    double probability_amplitude_;
public:
    explicit Qubit(double amp = 0.5) : probability_amplitude_(amp) {}
    Qubit(Qubit&&) noexcept = default;
    Qubit& operator=(Qubit&&) noexcept = default;

    // Non-copyable
    Qubit(const Qubit&) = delete;
    Qubit& operator=(const Qubit&) = delete;

    ~Qubit() = default;

    // A mock measurement
    int measure() {
        // Simplified measurement representation
        return probability_amplitude_ >= 0.5 ? 1 : 0;
    }
};

} // namespace ark

#endif // ARK_CPP_STD_CORE_TYPES_HPP
