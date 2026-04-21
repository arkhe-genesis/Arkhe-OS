#ifndef ARKHE_UTILS_HPP
#define ARKHE_UTILS_HPP

#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <thread>
#include <random>
#include <algorithm>
#include <cctype>

namespace arkhe {

// ═══════════════════════════════════════════════════════════════════════════════
// CORES ANSI (Para que o terminal tenha a beleza da forja)
// ═══════════════════════════════════════════════════════════════════════════════
namespace color {
    const std::string RED     = "\033[1;31m";
    const std::string GREEN   = "\033[1;32m";
    const std::string YELLOW  = "\033[1;33m";
    const std::string BLUE    = "\033[1;34m";
    const std::string MAGENTA = "\033[1;35m";
    const std::string CYAN    = "\033[1;36m";
    const std::string WHITE   = "\033[1;37m";
    const std::string RESET   = "\033[0m";
}

// ═══════════════════════════════════════════════════════════════════════════════
// HESITAÇÃO (O coração do Casulo)
// ═══════════════════════════════════════════════════════════════════════════════
inline void hesitate(int milliseconds = 500) {
    std::this_thread::sleep_for(std::chrono::milliseconds(milliseconds));
}

// ═══════════════════════════════════════════════════════════════════════════════
// GERAÇÃO DE UUID SIMPLES
// ═══════════════════════════════════════════════════════════════════════════════
inline std::string generate_uuid() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<> dis(0, 15);
    static const char* digits = "0123456789abcdef";

    std::string uuid;
    for (int i = 0; i < 32; ++i) {
        uuid += digits[dis(gen)];
        if (i == 7 || i == 11 || i == 15 || i == 19) uuid += '-';
    }
    return uuid;
}

// ═══════════════════════════════════════════════════════════════════════════════
// DETECÇÃO DE RUNAS PROIBIDAS (Bytes nulos em string)
// ═══════════════════════════════════════════════════════════════════════════════
inline bool contains_null_byte(const std::string& payload) {
    return payload.find('\0') != std::string::npos;
}

// ═══════════════════════════════════════════════════════════════════════════════
// SPLIT DE STRING
// ═══════════════════════════════════════════════════════════════════════════════
inline std::vector<std::string> split(const std::string& s, char delimiter) {
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream tokenStream(s);
    while (std::getline(tokenStream, token, delimiter)) {
        tokens.push_back(token);
    }
    return tokens;
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRIM
// ═══════════════════════════════════════════════════════════════════════════════
inline std::string trim(const std::string& str) {
    size_t first = str.find_first_not_of(" \t\n\r");
    if (first == std::string::npos) return "";
    size_t last = str.find_last_not_of(" \t\n\r");
    return str.substr(first, last - first + 1);
}

} // namespace arkhe

#endif // ARKHE_UTILS_HPP
