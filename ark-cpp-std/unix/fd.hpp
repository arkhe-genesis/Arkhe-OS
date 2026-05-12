#include <utility>
#pragma once

#include <string>
#include <memory>
#include <optional>
#include <unistd.h>

namespace ark {

struct Perm {
    enum Value {
        Read = 1,
        Write = 2,
        ReadWrite = 3
    };
    Value val;
    bool has_read() const { return (val & Read) != 0; }
    bool has_write() const { return (val & Write) != 0; }
};

struct TemporalBlock {
    std::string hash;
};

template<typename T>
struct Result {
    T val;
    std::string err;
    bool is_ok() const { return err.empty(); }
    T or_throw() {
        if (!is_ok()) throw std::runtime_error(err);
        return std::move(val);
    }
};

namespace UnixResource {
    struct File {};
}

namespace temporal {
    TemporalBlock anchor_content(const std::string& content, auto resource, Perm perms) {
        return TemporalBlock{"mock_hash"}; // Simplified for compilation
    }
}

template <typename Resource, Perm P>
class Fd {
    int fd_;
    Resource resource_;
    Perm perms_;
    std::optional<TemporalBlock> temporal_;
    bool anchored_ = false;

    std::string read_all() { return ""; } // Simplified
    void finalize_anchor() {} // Simplified

public:
    Fd(int fd, Resource r, Perm p) : fd_(fd), resource_(r), perms_(p) {}
    Fd(Fd&& other) noexcept : fd_(std::exchange(other.fd_, -1)), resource_(other.resource_), perms_(other.perms_) {}
    Fd& operator=(Fd&&) = default;
    Fd(const Fd&) = delete;
    void operator=(const Fd&) = delete;

    ~Fd() { if (fd_ >= 0) { close(); } }

    void close() {
        if (anchored_ && temporal_) finalize_anchor();
        ::close(fd_);
        fd_ = -1;
    }

    // Anchor content to TemporalChain
    TemporalBlock anchor() {
        if (!perms_.has_read()) throw std::runtime_error("Requires read permissions");
        auto content = read_all();
        auto hash = "mock_sha3"; // sha3_256(content);
        auto block = temporal::anchor_content(content, resource_, perms_);
        temporal_.emplace(block);
        anchored_ = true;
        return block;
    }
};

struct FileFd : public Fd<UnixResource::File, Perm{Perm::ReadWrite}> {
    FileFd(int fd) : Fd(fd, UnixResource::File{}, Perm{Perm::ReadWrite}) {}
    static Result<FileFd> open(const std::string& path, Perm p) {
        return Result<FileFd>{FileFd(-1), ""};
    }
    void write(const std::string& content) {}
};

std::string prove(const std::string& proof_type, const std::string& data) {
    return "mock_proof";
}

void anchor(const TemporalBlock& block, const std::string& proof) {}

} // namespace ark
