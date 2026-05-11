#ifndef ARKHEPP_HPP
#define ARKHEPP_HPP
#include "../arkhe.h"
#include <array>
#include <string>
#include <span>

namespace arkhe {
    struct CragRequest {
        uint8_t version = 1;
        uint8_t method = 0;
        std::array<uint8_t,4> zone_id{};
        std::array<uint8_t,16> query_hash{};
        uint8_t max_retrieved = 5;
        uint8_t flags = 0;
        std::array<uint8_t,168> payload{};

        void pack(std::span<uint8_t,192> out) const {
            ::CragRequest c;
            c.version = version; c.method = method;
            std::copy(zone_id.begin(), zone_id.end(), c.zone_id);
            std::copy(query_hash.begin(), query_hash.end(), c.query_hash);
            c.max_retrieved = max_retrieved; c.flags = flags;
            std::copy(payload.begin(), payload.end(), c.payload);
            crag_pack_request(&c, out.data());
        }
    };

    inline double kolmogorov_gap(const std::string& query, const std::string& source, const std::string& response) {
        return ::kolmogorov_gap(query.c_str(), source.c_str(), response.c_str());
    }
}
#endif
