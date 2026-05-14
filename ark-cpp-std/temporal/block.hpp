#ifndef ARK_CPP_STD_TEMPORAL_BLOCK_HPP
#define ARK_CPP_STD_TEMPORAL_BLOCK_HPP

#include <string>
#include <optional>
#include <cstdint>

namespace ark {

// Represents a block on the TemporalChain
struct TemporalBlock {
    std::string hash;
    uint64_t timestamp;
    std::string resource_info;
    std::string permissions;

    TemporalBlock(std::string h, uint64_t t, std::string res, std::string perms)
        : hash(std::move(h)), timestamp(t), resource_info(std::move(res)), permissions(std::move(perms)) {}
};

// Metadata attached to anchored objects
struct TemporalMetadata {
    std::string hash;
    TemporalBlock block;

    TemporalMetadata(std::string h, TemporalBlock b)
        : hash(std::move(h)), block(std::move(b)) {}
};

namespace temporal {

// A mock implementation of sha3_256 for the purpose of the backend wrapper.
inline std::string sha3_256(const std::string& input) {
    // In a real implementation this would call a crypto library.
    // For now we just return a dummy hash based on length to simulate hashing.
    return "hash_of_len_" + std::to_string(input.length());
}

// Anchors content to the TemporalChain, returning a TemporalBlock
template <typename Resource, typename Perm>
TemporalBlock anchor_content(const std::string& content, Resource res, Perm perms) {
    std::string hash = sha3_256(content);
    // In a real scenario, this would make an HTTP/gRPC call to the TemporalChain endpoint.
    // Here we just return a mock block.
    return TemporalBlock(hash, 0 /* mock timestamp */, "mock_resource", "mock_perms");
}

} // namespace temporal

} // namespace ark

#endif // ARK_CPP_STD_TEMPORAL_BLOCK_HPP
