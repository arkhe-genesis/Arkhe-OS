#ifndef COVERT_DNS_ENCLAVE_H
#define COVERT_DNS_ENCLAVE_H

#include <stdint.h>
#include <stddef.h>

#define MAX_RESOLVERS 16
#define DNS_TUNNEL_MTU 150
#define DNS_OVERHEAD 7

// Resolver definition with health and coherence metrics
typedef struct {
    char ip_address[64];
    float latency_ms;
    float packet_loss;
    float coherence_score; // Phi_C contribution
    int is_active;
} dns_resolver_t;

// Session context inside the TEE
typedef struct {
    uint32_t session_id;
    dns_resolver_t resolvers[MAX_RESOLVERS];
    int num_resolvers;
    float global_coherence;
    int duplication_count;
} dns_tunnel_session_t;

// Initialize the DNS tunnel session inside the enclave
int init_covert_dns_session(dns_tunnel_session_t* session, uint32_t session_id);

// Add a resolver to the session
int add_resolver(dns_tunnel_session_t* session, const char* ip_address);

// Update metrics for a resolver
int update_resolver_metrics(dns_tunnel_session_t* session, const char* ip_address, float latency, float loss, float coherence);

// Select the best resolver based on coherence Phi_C
dns_resolver_t* select_best_resolver(dns_tunnel_session_t* session);

// Encode payload for covert transport
int encode_dns_payload(const uint8_t* data, size_t data_len, uint8_t* out_buffer, size_t out_max, size_t* out_len);

// Decode payload from covert transport
int decode_dns_payload(const uint8_t* dns_packet, size_t packet_len, uint8_t* out_data, size_t out_max, size_t* out_len);

#endif // COVERT_DNS_ENCLAVE_H