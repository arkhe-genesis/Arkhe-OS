#include "arkhepp.hpp"
#include <iostream>
int main() {
    auto gap = arkhe::kolmogorov_gap("query", "source", "response");
    std::cout << gap << std::endl;
}
