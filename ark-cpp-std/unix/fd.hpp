#ifndef ARK_CPP_STD_UNIX_FD_HPP
#define ARK_CPP_STD_UNIX_FD_HPP

#include <unistd.h>
#include <fcntl.h>
#include <sys/wait.h>
#include <string>
#include <optional>
#include <utility>
#include <iostream>

#include "../core/result.hpp"
#include "../temporal/block.hpp"

namespace ark {

// Mock enum for Resources
enum class UnixResource {
    File,
    Pipe,
    Socket
};

// Mock structure for Permissions
struct Perm {
    enum : unsigned int {
        Read = 1 << 0,
        Write = 1 << 1,
        Execute = 1 << 2
    };

    unsigned int flags_;

    constexpr Perm(unsigned int flags = 0) : flags_(flags) {}
    constexpr bool has_read() const { return (flags_ & Read) != 0; }
    constexpr bool has_write() const { return (flags_ & Write) != 0; }
    constexpr bool has_execute() const { return (flags_ & Execute) != 0; }
};

template <typename Resource, typename P>
class Fd {
protected:
    int fd_;
    Resource resource_;
    P perms_;
    std::optional<TemporalMetadata> temporal_;
    bool anchored_;

    void finalize_anchor() {
        // Mock finalization logic
        // E.g., send final diff to TemporalChain
        std::cout << "Finalizing anchor for fd " << fd_ << std::endl;
    }

public:
    Fd(int fd, Resource res, P perms)
        : fd_(fd), resource_(res), perms_(perms), anchored_(false) {}

    Fd(Fd&& other) noexcept
        : fd_(std::exchange(other.fd_, -1)),
          resource_(other.resource_),
          perms_(other.perms_),
          temporal_(std::move(other.temporal_)),
          anchored_(other.anchored_) {}

    Fd& operator=(Fd&& other) noexcept {
        if (this != &other) {
            if (fd_ >= 0) { close(); }
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

    ~Fd() {
        if (fd_ >= 0) {
            close();
        }
    }

    void close() {
        if (anchored_ && temporal_) {
            finalize_anchor();
        }
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

    std::string read_all() const {
        // For the sake of demonstration, we implement a simple read
        // In a real implementation this requires seeking to 0, reading everything, and seeking back
        // Or reading from current pos. We assume a simple read here.
        if (!perms_.has_read()) {
            throw std::runtime_error("No read permission");
        }
        std::string out;
        char buf[4096];
        // Note: this alters file pointer. This is a naive implementation.
        while (ssize_t n = ::read(fd_, buf, sizeof(buf))) {
            if (n < 0) break;
            out.append(buf, n);
        }
        return out;
    }

    void write(const std::string& data) {
        if (!perms_.has_write()) {
            throw std::runtime_error("No write permission");
        }
        ssize_t n = ::write(fd_, data.c_str(), data.length());
        if (n < 0 || static_cast<size_t>(n) != data.length()) {
            throw std::runtime_error("Failed to write to fd");
        }
    }

    // Anchor content to TemporalChain
    // requires (P::has_read()) in C++20. Since we target C++23, we can use concepts,
    // but a static_assert works too if Perm is known.
    ark::Result<TemporalBlock> anchor() {
        if (!perms_.has_read()) {
            return ark::Err<std::string>("Cannot anchor without read permission");
        }
        auto content = read_all();
        auto hash = temporal::sha3_256(content);
        auto block = temporal::anchor_content(content, resource_, perms_);
        temporal_.emplace(hash, block);
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

class FileFd : public Fd<UnixResource, Perm> {
public:
    FileFd(int fd, Perm perms) : Fd(fd, UnixResource::File, perms) {}

    static ark::Result<FileFd> open(const std::string& path, Perm perms) {
        int flags = 0;
        if (perms.has_read() && perms.has_write()) {
            flags = O_RDWR | O_CREAT;
        } else if (perms.has_read()) {
            flags = O_RDONLY;
        } else if (perms.has_write()) {
            flags = O_WRONLY | O_CREAT;
        }

        int fd = ::open(path.c_str(), flags, 0644);
        if (fd < 0) {
            return ark::Err<std::string>("Failed to open file: " + path);
        }
        return FileFd(fd, perms);
    }
};

} // namespace ark

// Macro for command capture
#define ARK_COMMAND_CAPTURE(cmd) \
    [](const std::string& command) -> ark::Result<std::string> { \
        int pipefd[2]; \
        if (pipe(pipefd)) return ark::Err<std::string>("pipe failed"); \
        pid_t pid = fork(); \
        if (pid < 0) return ark::Err<std::string>("fork failed"); \
        if (pid == 0) { \
            ::close(pipefd[0]); \
            dup2(pipefd[1], STDOUT_FILENO); \
            ::close(pipefd[1]); \
            execl("/bin/sh", "sh", "-c", command.c_str(), nullptr); \
            _exit(127); \
        } \
        ::close(pipefd[1]); \
        std::string out; \
        char buf[4096]; \
        while (ssize_t n = ::read(pipefd[0], buf, sizeof(buf))) { \
            if (n < 0) break; \
            out.append(buf, n); \
        } \
        ::close(pipefd[0]); \
        int status; \
        waitpid(pid, &status, 0); \
        if (WIFEXITED(status) && WEXITSTATUS(status) != 0) { \
            return ark::Err<std::string>("cmd failed"); \
        } \
        return out; \
    }(cmd)

#endif // ARK_CPP_STD_UNIX_FD_HPP
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
