#pragma once

namespace arkhe::core {

extern "C" {
    /**
     * @brief Assembly implementation of the Clifford geometric product for Cl(4,0).
     *
     * @param a Pointer to the first multivector (16 doubles, 128 bytes).
     * @param b Pointer to the second multivector (16 doubles, 128 bytes).
     * @param result Pointer to the result multivector (16 doubles, 128 bytes).
     */
    void clifford_geometric_product(const double* a, const double* b, double* result);
}

} // namespace arkhe::core
