#pragma once

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace arkhe::secure {

struct State {
    int generation = 0;
    std::string parent_hash;
    std::string current_hash;
    std::string last_transformation;
    std::string last_signature;
    std::string temporal_seal;
    std::vector<std::string> backups;
};

struct HsmConfig {
    std::string pkcs11_module;
    std::string token_label;
    std::string key_label;
    std::string pin_env = "ARKHE_HSM_PIN";
    std::string mechanism = "EDDSA";
};

struct TemporalConfig {
    std::string endpoint;
    std::string chain_file;
};

struct AstValidationResult {
    bool ok = false;
    std::vector<std::string> violations;
};

std::string hsm_pkcs11_sign_real(const HsmConfig& hsm, const std::string& payload);

class SecureRecursiveSubstrate {
public:
    SecureRecursiveSubstrate(std::filesystem::path source_path,
                             std::filesystem::path state_path,
                             HsmConfig hsm,
                             TemporalConfig temporal);

    void load_state();
    void save_state() const;
    const State& state() const noexcept;
    const std::filesystem::path& source_path() const noexcept;
    const std::filesystem::path& state_path() const noexcept;

    std::string read_self() const;
    std::string hash_source() const;
    std::filesystem::path create_backup();
    AstValidationResult validate_transformation_ast(const std::string& code) const;
    std::string sign_transformation(const std::string& code) const;
    bool verify_signature(const std::string& code, const std::string& signature) const;
    bool hsm_available() const noexcept;
    std::optional<std::string> evolve(const std::string& direction);
    bool rollback_to_last_backup();
    bool verify_integrity() const;

    std::string serialize_state_json() const;
    static State deserialize_state_json(const std::string& json);

    static void install_seccomp_filter();
    static void create_sandbox_dir(const std::filesystem::path& sandbox_root);
    static int run_in_sandbox(const std::filesystem::path& sandbox_root,
                              const std::filesystem::path& script,
                              const std::vector<std::string>& args);

    std::string anchor_temporal_chain(const std::string& transformation,
                                      const std::string& signature,
                                      const std::string& source_hash_after);

private:
    std::filesystem::path source_path_;
    std::filesystem::path state_path_;
    HsmConfig hsm_;
    TemporalConfig temporal_;
    State state_;
    bool hsm_available_ = false;
    std::string source_before_last_evolution_;

    std::string current_chain_tail() const;
    void update_backups_index(const std::filesystem::path& backup);
    std::string compute_sha3_hex(const std::string& input) const;
};

} // namespace arkhe::secure
