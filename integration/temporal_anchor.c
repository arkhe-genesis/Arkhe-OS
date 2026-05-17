/*
 * ARKHE OS Substrato ∞: TemporalChain Anchor Client
 * Canon: ∞.Ω.∇+++.∞.integration.temporal_anchor
 * Função: Ancorar eventos do sistema híbrido na TemporalChain
 * Linguagem: C (userspace, HTTP client with PQC signatures)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <curl/curl.h>
#include <json-c/json.h>
#include <sha3/sha3.h>
#include <crypto/dilithium/dilithium.h>

#define TEMPORAL_CHAIN_API "https://temporal.arkhe.os/v1/anchor"
#define HSM_DEVICE "/dev/arkhe_hsm"

struct temporal_anchor_ctx {
    char *api_endpoint;
    char *institution_id;
    char *hsm_key_label;
    CURL *curl;
};

struct anchor_response {
    char seal[65];  /* SHA3-256 hex + null */
    char *error;
    int http_code;
};

static size_t
write_callback(void *ptr, size_t size, size_t nmemb, void *userdata)
{
    /* Simplified: just return size for now */
    return size * nmemb;
}

static char *
sign_with_hsm(const char *institution_id, const char *data, size_t data_len)
{
    /* In production: communicate with HSM via ioctl or character device */
    /* Mock: compute SHA3-256 of data + institution_id */

    SHA3_256_CTX ctx;
    sha3_256_init(&ctx);
    sha3_256_update(&ctx, (const uint8_t *)institution_id, strlen(institution_id));
    sha3_256_update(&ctx, (const uint8_t *)data, data_len);

    uint8_t hash[32];
    sha3_256_final(&ctx, hash);

    /* Convert to hex */
    static char hex[65];
    for (int i = 0; i < 32; i++) {
        sprintf(hex + i * 2, "%02x", hash[i]);
    }
    hex[64] = '\0';

    return hex;
}

int
temporal_anchor_event(
    struct temporal_anchor_ctx *ctx,
    const char *event_type,
    const char *event_payload_json
)
{
    if (!ctx || !ctx->curl || !event_type || !event_payload_json) {
        return EINVAL;
    }

    /* Compute content hash */
    SHA3_256_CTX hash_ctx;
    sha3_256_init(&hash_ctx);
    sha3_256_update(&hash_ctx, (const uint8_t *)event_payload_json,
                    strlen(event_payload_json));
    uint8_t content_hash[32];
    sha3_256_final(&hash_ctx, content_hash);

    /* Sign with HSM */
    char *signature = sign_with_hsm(ctx->institution_id, event_payload_json,
                                     strlen(event_payload_json));

    /* Build JSON payload for API */
    json_object *payload = json_object_new_object();
    json_object_object_add(payload, "institution_id",
                          json_object_new_string(ctx->institution_id));
    json_object_object_add(payload, "event_type",
                          json_object_new_string(event_type));
    json_object_object_add(payload, "event_payload",
                          json_object_new_string(event_payload_json));
    json_object_object_add(payload, "content_hash",
                          json_object_new_string_len((char *)content_hash, 32));
    json_object_object_add(payload, "pqc_signature",
                          json_object_new_string(signature));
    json_object_object_add(payload, "timestamp",
                          json_object_new_int64(time(NULL)));

    const char *json_str = json_object_to_json_string(payload);

    /* Prepare curl request */
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "X-ARKHE-Protocol: 1.0");

    curl_easy_setopt(ctx->curl, CURLOPT_URL, ctx->api_endpoint);
    curl_easy_setopt(ctx->curl, CURLOPT_POSTFIELDS, json_str);
    curl_easy_setopt(ctx->curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(ctx->curl, CURLOPT_WRITEFUNCTION, write_callback);

    /* Execute request */
    CURLcode res = curl_easy_perform(ctx->curl);

    /* Cleanup */
    curl_slist_free_all(headers);
    json_object_put(payload);

    if (res != CURLE_OK) {
        fprintf(stderr, "curl error: %s\n", curl_easy_strerror(res));
        return -1;
    }

    /* Get response code */
    long http_code;
    curl_easy_getinfo(ctx->curl, CURLINFO_RESPONSE_CODE, &http_code);

    if (http_code != 200) {
        fprintf(stderr, "HTTP error: %ld\n", http_code);
        return -1;
    }

    printf("[TemporalChain] Event anchored: %s\n", event_type);
    return 0;
}

struct temporal_anchor_ctx *
temporal_anchor_init(const char *institution_id, const char *hsm_key_label)
{
    struct temporal_anchor_ctx *ctx = calloc(1, sizeof(*ctx));
    if (!ctx) return NULL;

    ctx->api_endpoint = strdup(TEMPORAL_CHAIN_API);
    ctx->institution_id = strdup(institution_id);
    ctx->hsm_key_label = strdup(hsm_key_label ? hsm_key_label : "default");

    ctx->curl = curl_easy_init();
    if (!ctx->curl) {
        free(ctx->api_endpoint);
        free(ctx->institution_id);
        free(ctx->hsm_key_label);
        free(ctx);
        return NULL;
    }

    /* Configure curl */
    curl_easy_setopt(ctx->curl, CURLOPT_TIMEOUT, 30L);
    curl_easy_setopt(ctx->curl, CURLOPT_FOLLOWLOCATION, 1L);

    return ctx;
}

void
temporal_anchor_cleanup(struct temporal_anchor_ctx *ctx)
{
    if (!ctx) return;

    if (ctx->curl) curl_easy_cleanup(ctx->curl);
    free(ctx->api_endpoint);
    free(ctx->institution_id);
    free(ctx->hsm_key_label);
    free(ctx);
}

/* Example usage */
#ifdef STANDALONE_TEST
int main(int argc, char *argv[])
{
    curl_global_init(CURL_GLOBAL_DEFAULT);

    struct temporal_anchor_ctx *ctx =
        temporal_anchor_init("orcid:0009-0005-2697-4668", "arkhe_anchor_key");

    if (!ctx) {
        fprintf(stderr, "Failed to initialize temporal anchor\n");
        return 1;
    }

    /* Anchor a test event */
    const char *payload = "{\"jail_id\":\"test123\",\"action\":\"created\"}";

    int result = temporal_anchor_event(ctx, "jail_created", payload);

    temporal_anchor_cleanup(ctx);
    curl_global_cleanup();

    return result == 0 ? 0 : 1;
}
#endif
