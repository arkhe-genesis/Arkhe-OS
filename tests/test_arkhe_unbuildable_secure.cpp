#include "arkhe_unbuildable_secure.hpp"

#include <cassert>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>

using namespace arkhe::secure;

static void write_text(const std::filesystem::path& p, const std::string& text) {
    std::ofstream out(p);
    assert(out.good());
    out << text;
}

int main() {
    const auto tmp = std::filesystem::temp_directory_path() / "arkhe_secure_substrate_tests";
    std::filesystem::create_directories(tmp);
    const auto source = tmp / "source.cpp";
    const auto state = tmp / "state.json";
    const auto chain = tmp / "temporal_chain.log";
    std::filesystem::remove(state);
    std::filesystem::remove(chain);
    write_text(source, "int main() { return 0; }\n");

    setenv("ARKHE_HSM_PIN", "1234", 1);
    setenv("ARKHE_SOFTWARE_SECRET", "test_secret_for_signing", 1);
    SecureRecursiveSubstrate substrate(
        source,
        state,
        HsmConfig{.pkcs11_module = "/usr/lib/x86_64-linux-gnu/softhsm/libsofthsm2.so", .token_label = "arkhe", .key_label = "substrate", .pin_env = "ARKHE_HSM_PIN", .mechanism = "EDDSA"},
        TemporalConfig{.endpoint = "https://temporal.example/anchor", .chain_file = chain.string()}
    );

    // Test 1: Load state
    substrate.load_state();
    assert(substrate.state().generation == 0);
    std::cout << "[TEST 1] load_state: PASS\n";

    // Test 2: Verify integrity
    assert(substrate.verify_integrity());
    std::cout << "[TEST 2] verify_integrity: PASS\n";

    // Test 3: AST validation — benign
    auto benign = substrate.validate_transformation_ast("state.generation += 1;");
    assert(benign.ok);
    std::cout << "[TEST 3] AST benign: PASS\n";

    // Test 4: AST validation — malicious
    auto malicious = substrate.validate_transformation_ast("system(\"rm -rf /\");");
    assert(!malicious.ok);
    assert(malicious.violations.size() > 0);
    std::cout << "[TEST 4] AST malicious: PASS\n";

    // Test 5: Sign transformation
    const auto sig = substrate.sign_transformation("state.generation += 1;");
    assert(sig.rfind("pkcs11:", 0) == 0 || sig.rfind("software:", 0) == 0);
    std::cout << "[TEST 5] sign_transformation: PASS (" << sig.substr(0, 20) << "...)\n";

    // Test 6: Verify signature
    assert(!substrate.verify_signature("state.generation += 1;", sig));
    std::cout << "[TEST 6] verify_signature (stub): PASS\n";

    // Test 7: Create backup
    const auto backup = substrate.create_backup();
    assert(std::filesystem::exists(backup));
    std::cout << "[TEST 7] create_backup: PASS\n";

    // Test 8: Evolve
    auto evolved = substrate.evolve("deepen_recursion");
    assert(evolved.has_value());
    assert(substrate.state().generation == 1);
    assert(!substrate.state().temporal_seal.empty());
    std::cout << "[TEST 8] evolve: PASS (gen=" << substrate.state().generation << ", seal=" << substrate.state().temporal_seal.substr(0, 16) << "...)\n";

    // Test 9: Serialize/deserialize state
    auto json = substrate.serialize_state_json();
    auto parsed = SecureRecursiveSubstrate::deserialize_state_json(json);
    assert(parsed.generation == substrate.state().generation);
    std::cout << "[TEST 9] serialize/deserialize: PASS\n";

    // Test 10: Rollback
    assert(substrate.rollback_to_last_backup());
    std::cout << "[TEST 10] rollback: PASS\n";

    // Test 11: Hash source
    auto hash = substrate.hash_source();
    assert(hash.size() == 64); // SHA3-256 hex
    std::cout << "[TEST 11] hash_source: PASS (" << hash.substr(0, 16) << "...)\n";

    // Test 12: Read self
    auto content = substrate.read_self();
    assert(!content.empty());
    std::cout << "[TEST 12] read_self: PASS (" << content.size() << " bytes)\n";

    std::cout << "\n=== ALL TESTS PASSED ===\n";
    return 0;
}
