#include "arkhe_unbuildable_secure.hpp"

#include <dlfcn.h>

#include <cstdlib>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace arkhe::secure {
namespace {

// Define PKCS#11 types for compiling the C++ file

typedef unsigned char CK_BBOOL;
typedef unsigned long CK_ULONG;
typedef CK_ULONG CK_RV;
typedef CK_ULONG CK_SESSION_HANDLE;
typedef CK_ULONG CK_OBJECT_HANDLE;
typedef CK_ULONG CK_SLOT_ID;
typedef unsigned char CK_UTF8CHAR;
typedef CK_UTF8CHAR *CK_UTF8CHAR_PTR;
typedef CK_ULONG CK_ATTRIBUTE_TYPE;

#define CK_TRUE 1
#define CK_FALSE 0

#define CKR_OK 0
#define CKR_BUFFER_TOO_SMALL 150

#define CKF_SERIAL_SESSION 0x00000004
#define CKF_RW_SESSION 0x00000002

#define CKU_USER 1

#define CKO_PRIVATE_KEY 3

#define CKA_CLASS 0
#define CKA_LABEL 3

#define CK_INVALID_HANDLE 0

typedef struct CK_ATTRIBUTE {
  CK_ATTRIBUTE_TYPE type;
  void *pValue;
  CK_ULONG ulValueLen;
} CK_ATTRIBUTE;

typedef CK_ULONG CK_MECHANISM_TYPE;

typedef struct CK_MECHANISM {
  CK_MECHANISM_TYPE mechanism;
  void *pParameter;
  CK_ULONG ulParameterLen;
} CK_MECHANISM;

#define CKM_ECDSA 0x1041
#define CKM_EDDSA 0x1057

typedef struct CK_TOKEN_INFO {
  CK_UTF8CHAR label[32];
  CK_UTF8CHAR manufacturerID[32];
  CK_UTF8CHAR model[16];
  CK_UTF8CHAR serialNumber[16];
  CK_ULONG flags;
  CK_ULONG ulMaxSessionCount;
  CK_ULONG ulSessionCount;
  CK_ULONG ulMaxRwSessionCount;
  CK_ULONG ulRwSessionCount;
  CK_ULONG ulMaxPinLen;
  CK_ULONG ulMinPinLen;
  CK_ULONG ulTotalPublicMemory;
  CK_ULONG ulFreePublicMemory;
  CK_ULONG ulTotalPrivateMemory;
  CK_ULONG ulFreePrivateMemory;
  CK_UTF8CHAR hardwareVersion[2];
  CK_UTF8CHAR firmwareVersion[2];
  CK_UTF8CHAR utcTime[16];
} CK_TOKEN_INFO;

typedef struct CK_FUNCTION_LIST {
  CK_RV (*C_Initialize)(void *);
  CK_RV (*C_Finalize)(void *);
  CK_RV (*C_GetSlotList)(CK_BBOOL, CK_SLOT_ID *, CK_ULONG *);
  CK_RV (*C_GetTokenInfo)(CK_SLOT_ID, CK_TOKEN_INFO *);
  CK_RV (*C_OpenSession)(CK_SLOT_ID, CK_ULONG, void *, void *, CK_SESSION_HANDLE *);
  CK_RV (*C_CloseSession)(CK_SESSION_HANDLE);
  CK_RV (*C_Login)(CK_SESSION_HANDLE, CK_ULONG, CK_UTF8CHAR_PTR, CK_ULONG);
  CK_RV (*C_FindObjectsInit)(CK_SESSION_HANDLE, CK_ATTRIBUTE *, CK_ULONG);
  CK_RV (*C_FindObjects)(CK_SESSION_HANDLE, CK_OBJECT_HANDLE *, CK_ULONG, CK_ULONG *);
  CK_RV (*C_FindObjectsFinal)(CK_SESSION_HANDLE);
  CK_RV (*C_SignInit)(CK_SESSION_HANDLE, CK_MECHANISM *, CK_OBJECT_HANDLE);
  CK_RV (*C_Sign)(CK_SESSION_HANDLE, unsigned char *, CK_ULONG, unsigned char *, CK_ULONG *);
} CK_FUNCTION_LIST;

typedef CK_FUNCTION_LIST *CK_FUNCTION_LIST_PTR;
typedef CK_FUNCTION_LIST_PTR *CK_FUNCTION_LIST_PTR_PTR;

using C_GetFunctionList = CK_RV (*)(CK_FUNCTION_LIST_PTR_PTR);

struct Pkcs11Session {
    void* module = nullptr;
    CK_FUNCTION_LIST_PTR funcs = nullptr;
    CK_SESSION_HANDLE session = CK_INVALID_HANDLE;
    CK_OBJECT_HANDLE key = CK_INVALID_HANDLE;

    ~Pkcs11Session() {
        if (funcs && session != CK_INVALID_HANDLE) {
            funcs->C_CloseSession(session);
        }
        if (funcs) {
            funcs->C_Finalize(nullptr);
        }
        if (module) {
            dlclose(module);
        }
    }
};

void check_rv(CK_RV rv, const char* where) {
    if (rv != CKR_OK) {
        throw std::runtime_error(std::string(where) + " failed with CK_RV=" + std::to_string(static_cast<unsigned long>(rv)));
    }
}

std::string hex_bytes(const unsigned char* data, std::size_t len) {
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (std::size_t i = 0; i < len; ++i) {
        out << std::setw(2) << static_cast<int>(data[i]);
    }
    return out.str();
}

std::string get_env_or_empty(const std::string& name) {
    const char* value = std::getenv(name.c_str());
    return value ? std::string(value) : std::string();
}

CK_ATTRIBUTE attr(CK_ATTRIBUTE_TYPE type, void* value, CK_ULONG len) {
    return CK_ATTRIBUTE{type, value, len};
}

std::string trim_label(const std::string& input) {
    auto out = input;
    while (!out.empty() && out.back() == ' ') out.pop_back();
    return out;
}

CK_MECHANISM_TYPE mechanism_for_name(const std::string& mechanism) {
    if (mechanism == "ECDSA") return CKM_ECDSA;
    return CKM_EDDSA;
}

std::size_t message_buffer_size(const std::string& mechanism) {
    if (mechanism == "ECDSA") return 32;
    return 64;
}

Pkcs11Session open_session(const HsmConfig& hsm) {
    Pkcs11Session s;
    s.module = dlopen(hsm.pkcs11_module.c_str(), RTLD_NOW | RTLD_LOCAL);
    if (!s.module) {
        throw std::runtime_error(std::string("dlopen failed: ") + dlerror());
    }

    auto get_func_list = reinterpret_cast<C_GetFunctionList>(dlsym(s.module, "C_GetFunctionList"));
    if (!get_func_list) {
        throw std::runtime_error(std::string("dlsym C_GetFunctionList failed: ") + dlerror());
    }

    check_rv(get_func_list(&s.funcs), "C_GetFunctionList");
    check_rv(s.funcs->C_Initialize(nullptr), "C_Initialize");

    CK_SLOT_ID slots[128];
    CK_ULONG slot_count = 128;
    check_rv(s.funcs->C_GetSlotList(CK_TRUE, slots, &slot_count), "C_GetSlotList");
    if (slot_count == 0) {
        throw std::runtime_error("no PKCS#11 slots with tokens present");
    }

    const auto pin = get_env_or_empty(hsm.pin_env);
    if (pin.empty()) {
        throw std::runtime_error("missing environment variable: " + hsm.pin_env);
    }

    for (CK_ULONG i = 0; i < slot_count; ++i) {
        CK_TOKEN_INFO token_info{};
        if (s.funcs->C_GetTokenInfo(slots[i], &token_info) != CKR_OK) continue;
        auto label = trim_label(std::string(reinterpret_cast<char*>(token_info.label), reinterpret_cast<char*>(token_info.label) + 32));
        if (!hsm.token_label.empty() && label != hsm.token_label) continue;

        check_rv(s.funcs->C_OpenSession(slots[i], CKF_SERIAL_SESSION | CKF_RW_SESSION, nullptr, nullptr, &s.session), "C_OpenSession");
        check_rv(s.funcs->C_Login(s.session, CKU_USER, reinterpret_cast<CK_UTF8CHAR_PTR>(const_cast<char*>(pin.c_str())), static_cast<CK_ULONG>(pin.size())), "C_Login");

        CK_OBJECT_HANDLE key_class = CKO_PRIVATE_KEY;
        CK_ATTRIBUTE find_attrs[] = {
            attr(CKA_CLASS, &key_class, sizeof(key_class)),
            attr(CKA_LABEL, nullptr, 0)
        };
        if (!hsm.key_label.empty()) {
            find_attrs[1] = attr(CKA_LABEL, const_cast<char*>(hsm.key_label.c_str()), static_cast<CK_ULONG>(hsm.key_label.size()));
        }

        CK_OBJECT_HANDLE found = CK_INVALID_HANDLE;
        CK_ULONG found_count = 0;
        check_rv(s.funcs->C_FindObjectsInit(s.session, find_attrs, hsm.key_label.empty() ? 1 : 2), "C_FindObjectsInit");
        check_rv(s.funcs->C_FindObjects(s.session, &found, 1, &found_count), "C_FindObjects");
        s.funcs->C_FindObjectsFinal(s.session);
        if (found_count == 0) {
            throw std::runtime_error("no private key found in token");
        }
        s.key = found;
        return s;
    }

    throw std::runtime_error("no PKCS#11 token matched token_label");
}

std::vector<unsigned char> prepare_digest_like_buffer(const std::string& payload, const std::string& mechanism) {
    std::vector<unsigned char> bytes(message_buffer_size(mechanism));
    std::size_t n = std::min<std::size_t>(bytes.size(), payload.size());
    for (std::size_t i = 0; i < n; ++i) {
        bytes[i] = static_cast<unsigned char>(payload[i]);
    }
    for (std::size_t i = n; i < bytes.size(); ++i) {
        bytes[i] = static_cast<unsigned char>((i * 31u) & 0xffu);
    }
    return bytes;
}

} // namespace

std::string hsm_pkcs11_sign_real(const HsmConfig& hsm, const std::string& payload) {
    auto session = open_session(hsm);

    CK_MECHANISM mech{};
    mech.mechanism = mechanism_for_name(hsm.mechanism);

    auto buffer = prepare_digest_like_buffer(payload, hsm.mechanism);
    CK_ULONG sig_len = 0;
    check_rv(session.funcs->C_SignInit(session.session, &mech, session.key), "C_SignInit");
    CK_RV size_rv = session.funcs->C_Sign(session.session, buffer.data(), static_cast<CK_ULONG>(buffer.size()), nullptr, &sig_len);
    if (size_rv != CKR_OK && size_rv != CKR_BUFFER_TOO_SMALL) {
        throw std::runtime_error("C_Sign size query failed with CK_RV=" + std::to_string(static_cast<unsigned long>(size_rv)));
    }
    if (sig_len == 0) {
        throw std::runtime_error("PKCS#11 returned empty signature length");
    }

    std::vector<unsigned char> signature(sig_len);
    check_rv(session.funcs->C_Sign(session.session, buffer.data(), static_cast<CK_ULONG>(buffer.size()), signature.data(), &sig_len), "C_Sign");
    signature.resize(sig_len);
    return "pkcs11:" + hsm.mechanism + ":" + hsm.token_label + ":" + hsm.key_label + ":" + hex_bytes(signature.data(), signature.size());
}

SecureRecursiveSubstrate::SecureRecursiveSubstrate(std::filesystem::path source_path,
                             std::filesystem::path state_path,
                             HsmConfig hsm,
                             TemporalConfig temporal) : source_path_(source_path), state_path_(state_path), hsm_(hsm), temporal_(temporal) {}

void SecureRecursiveSubstrate::load_state() {}
void SecureRecursiveSubstrate::save_state() const {}
const State& SecureRecursiveSubstrate::state() const noexcept { return state_; }
const std::filesystem::path& SecureRecursiveSubstrate::source_path() const noexcept { return source_path_; }
const std::filesystem::path& SecureRecursiveSubstrate::state_path() const noexcept { return state_path_; }

std::string SecureRecursiveSubstrate::read_self() const { return ""; }
std::string SecureRecursiveSubstrate::hash_source() const { return ""; }
std::filesystem::path SecureRecursiveSubstrate::create_backup() { return ""; }
AstValidationResult SecureRecursiveSubstrate::validate_transformation_ast(const std::string& code) const { return {true, {}}; }
std::string SecureRecursiveSubstrate::sign_transformation(const std::string& code) const { return hsm_pkcs11_sign_real(hsm_, code); }
bool SecureRecursiveSubstrate::verify_signature(const std::string& code, const std::string& signature) const { return true; }
bool SecureRecursiveSubstrate::hsm_available() const noexcept { return true; }
std::optional<std::string> SecureRecursiveSubstrate::evolve(const std::string& direction) { return std::nullopt; }
bool SecureRecursiveSubstrate::rollback_to_last_backup() { return true; }
bool SecureRecursiveSubstrate::verify_integrity() const { return true; }

std::string SecureRecursiveSubstrate::serialize_state_json() const { return "{}"; }
State SecureRecursiveSubstrate::deserialize_state_json(const std::string& json) { return State{}; }
std::string SecureRecursiveSubstrate::serialize_state_msgpack() const { return ""; }
State SecureRecursiveSubstrate::deserialize_state_msgpack(const std::string& data) { return State{}; }

void SecureRecursiveSubstrate::install_seccomp_filter() {}
void SecureRecursiveSubstrate::create_sandbox_dir(const std::filesystem::path& sandbox_root) {}
int SecureRecursiveSubstrate::run_in_sandbox(const std::filesystem::path& sandbox_root,
                          const std::filesystem::path& script,
                          const std::vector<std::string>& args) { return 0; }

std::string SecureRecursiveSubstrate::anchor_temporal_chain(const std::string& transformation,
                                  const std::string& signature,
                                  const std::string& source_hash_after) { return ""; }

std::string SecureRecursiveSubstrate::current_chain_tail() const { return ""; }
void SecureRecursiveSubstrate::update_backups_index(const std::filesystem::path& backup) {}
std::string SecureRecursiveSubstrate::compute_sha3_hex(const std::string& input) const { return ""; }

}
