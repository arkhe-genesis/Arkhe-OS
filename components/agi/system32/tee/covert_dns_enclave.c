#include "covert_dns_enclave.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

int init_covert_dns_session(dns_tunnel_session_t* session, uint32_t session_id) {
    if (!session) return -1;
    session->session_id = session_id;
    session->num_resolvers = 0;
    session->global_coherence = 1.0f;
    session->duplication_count = 2; // Default for reliability
    memset(session->resolvers, 0, sizeof(session->resolvers));
    return 0;
}

int add_resolver(dns_tunnel_session_t* session, const char* ip_address) {
    if (!session || !ip_address) return -1;
    if (session->num_resolvers >= MAX_RESOLVERS) return -2; // Max capacity

    // Check for duplicates
    for (int i = 0; i < session->num_resolvers; i++) {
        if (strcmp(session->resolvers[i].ip_address, ip_address) == 0) {
            return 0; // Already exists
        }
    }

    dns_resolver_t* r = &session->resolvers[session->num_resolvers++];
    strncpy(r->ip_address, ip_address, sizeof(r->ip_address) - 1);
    r->latency_ms = 100.0f; // Default baseline
    r->packet_loss = 0.0f;
    r->coherence_score = 0.5f; // Initial Phi_C score
    r->is_active = 1;

    return 0;
}

int update_resolver_metrics(dns_tunnel_session_t* session, const char* ip_address, float latency, float loss, float coherence) {
    if (!session || !ip_address) return -1;

    for (int i = 0; i < session->num_resolvers; i++) {
        if (strcmp(session->resolvers[i].ip_address, ip_address) == 0) {
            session->resolvers[i].latency_ms = latency;
            session->resolvers[i].packet_loss = loss;
            session->resolvers[i].coherence_score = coherence;

            // Auto-disable if Phi_C drops critically
            if (coherence < 0.1f) {
                session->resolvers[i].is_active = 0;
            } else {
                session->resolvers[i].is_active = 1;
            }
            return 0;
        }
    }
    return -1; // Not found
}

dns_resolver_t* select_best_resolver(dns_tunnel_session_t* session) {
    if (!session || session->num_resolvers == 0) return NULL;

    dns_resolver_t* best = NULL;
    float best_score = -1.0f;

    for (int i = 0; i < session->num_resolvers; i++) {
        dns_resolver_t* r = &session->resolvers[i];
        if (!r->is_active) continue;

        // Scoring formula combining Coherence (Phi_C), loss, and latency
        // Coherence is the primary routing metric.
        float score = (r->coherence_score * 0.9f) + ((1.0f - r->packet_loss) * 0.05f) + ((100.0f / (r->latency_ms + 1.0f)) * 0.05f);

        if (score > best_score) {
            best_score = score;
            best = r;
        }
    }

    return best;
}

int encode_dns_payload(const uint8_t* data, size_t data_len, uint8_t* out_buffer, size_t out_max, size_t* out_len) {
    if (!data || !out_buffer || !out_len) return -1;
    if (data_len + DNS_OVERHEAD > out_max) return -2; // Insufficient buffer

    // Simulate low-overhead packet structure: [HEADER: 7 bytes] [DATA]
    // Header format: [1B: Version/Flags] [2B: Seq Num] [2B: Session ID hash] [2B: Checksum]
    out_buffer[0] = 0x01; // Version 1

    // Mock simple XOR encryption for payload
    for (size_t i = 0; i < data_len; i++) {
        out_buffer[DNS_OVERHEAD + i] = data[i] ^ 0x42;
    }

    *out_len = data_len + DNS_OVERHEAD;
    return 0;
}

int decode_dns_payload(const uint8_t* dns_packet, size_t packet_len, uint8_t* out_data, size_t out_max, size_t* out_len) {
    if (!dns_packet || !out_data || !out_len) return -1;
    if (packet_len <= DNS_OVERHEAD) return -1; // Too small

    size_t data_len = packet_len - DNS_OVERHEAD;
    if (data_len > out_max) return -2; // Insufficient buffer

    // Version check
    if (dns_packet[0] != 0x01) return -3; // Unsupported version

    // Mock simple XOR decryption for payload
    for (size_t i = 0; i < data_len; i++) {
        out_data[i] = dns_packet[DNS_OVERHEAD + i] ^ 0x42;
    }

    *out_len = data_len;
    return 0;
}