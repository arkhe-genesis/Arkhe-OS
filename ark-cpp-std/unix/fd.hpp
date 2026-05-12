#pragma once

#include <string>
#include <memory>
#include <optional>
#include <utility>
#include <stdexcept>
#include <unistd.h>
#include <fcntl.h>
#include <vector>

namespace ark {

template <typename E>
struct ErrType { E err; };

template <typename E>
ErrType<E> Err(E err) { return ErrType<E>{std::move(err)}; }

template <typename T>
using Option = std::optional<T>;

template <typename T, typename E = std::string>
class Result {
    std::optional<T> val_;
    std::optional<E> err_;
public:
    Result(T val) : val_(std::move(val)) {}
    Result(ErrType<E> err) : err_(std::move(err.err)) {}

    bool is_ok() const { return val_.has_value(); }
    T unwrap() {
        if (is_ok()) return std::move(*val_);
        throw std::runtime_error("Called unwrap on Err");
    }
    T or_throw() { return unwrap(); }
};


// Mock structs for the example
struct TemporalBlock {
    std::string hash;
    int64_t number;
};

struct TemporalMetadata {
    std::string anchor_hash;
    TemporalBlock block_id;
};

enum class UnixResource {
    File,
    Pipe,
    Socket
};

struct Perm {
    static constexpr int Read = 1 << 0;
    static constexpr int Write = 1 << 1;
    static constexpr int Execute = 1 << 2;

    int flags;
    constexpr Perm(int f) : flags(f) {}
    constexpr bool has_read() const { return flags & Read; }
    constexpr bool has_write() const { return flags & Write; }
};

// Mock Temporal/ZK functions
namespace temporal {
    inline TemporalBlock anchor_content(const std::string& content, UnixResource resource, Perm perms) {
        return TemporalBlock{"mock_hash_" + std::to_string(content.size()), 1};
    }
}

inline std::string sha3_256(const std::string& data) {
    return "sha3_hash";
}

struct ZKProof { std::string data; };

inline ZKProof prove(const std::string& claim, const std::vector<std::string>& public_inputs) {
    return ZKProof{"mock_proof"};
}

inline void anchor(const TemporalBlock& block, const ZKProof& proof) {
    // Anchor to the temporal chain
}

template <typename Resource_t, int P_flags>
class Fd {
    int fd_;
    Resource_t resource_;
    Perm perms_;
    std::optional<TemporalMetadata> temporal_;
    bool anchored_ = false;

public:
    Fd(int fd, Resource_t res, Perm perms) : fd_(fd), resource_(res), perms_(perms) {}

    // Move only
    Fd(Fd&& other) noexcept : fd_(std::exchange(other.fd_, -1)), resource_(other.resource_), perms_(other.perms_) {}
    Fd& operator=(Fd&& other) noexcept {
        if (this != &other) {
            if (fd_ >= 0) close();
            fd_ = std::exchange(other.fd_, -1);
            resource_ = other.resource_;
            perms_ = other.perms_;
            temporal_ = std::move(other.temporal_);
            anchored_ = other.anchored_;
        }
        return *this;
    }

    Fd(const Fd&) = delete;
    void operator=(const Fd&) = delete;

    ~Fd() { if (fd_ >= 0) { close(); } }

    void finalize_anchor() {
        // Mock finalization
    }

    void close() {
        if (anchored_ && temporal_) finalize_anchor();
        ::close(fd_);
        fd_ = -1;
    }

    std::string read_all() const {
        // Mock read
        return "file_content";
    }

    void write(const std::string& data) {
        if (!perms_.has_write()) throw std::runtime_error("No write permission");
        // ::write(fd_, data.data(), data.size());
    }

    // Anchor content to TemporalChain
    Result<TemporalBlock> anchor() {
        if (!perms_.has_read()) return Err(std::string("No read permission to anchor"));
        auto content = read_all();
        auto hash = sha3_256(content);
        auto block = temporal::anchor_content(content, resource_, perms_);
        temporal_ = TemporalMetadata{hash, block};
        anchored_ = true;
        return Result<TemporalBlock>(block);
    }
};

class FileFd : public Fd<UnixResource, Perm::Read | Perm::Write> {
public:
    FileFd(int fd, Perm perms) : Fd(fd, UnixResource::File, perms) {}

    static Result<FileFd> open(const std::string& path, Perm perms) {
        // Mock open
        int fd = 10; // dummy fd
        return Result<FileFd>(FileFd(fd, perms));
    }
};

} // namespace ark
