#include <iostream>
#include <openssl/evp.h>
#include <chrono>
#include <iomanip>
#include <sstream>

std::string generate_sha3_256(const std::string& data) {
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha3_256(), nullptr);
    EVP_DigestUpdate(ctx, data.c_str(), data.size());

    unsigned char hash[32];
    unsigned int hash_len;
    EVP_DigestFinal_ex(ctx, hash, &hash_len);
    EVP_MD_CTX_free(ctx);

    std::stringstream ss;
    for (unsigned int i = 0; i < hash_len; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    return ss.str();
}

int main() {
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(
        now.time_since_epoch()
    ).count();

    std::string event = "polyglot_cpp_anchor";
    std::string data = event + std::to_string(timestamp);
    std::string seal = generate_sha3_256(data);

    std::cout << "🔩 C++ TemporalChain: Evento '" << event
              << "' ancorado | Selo=" << seal.substr(0, 16) << "..."
              << std::endl;
    return 0;
}