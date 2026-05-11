#include "arkhe.h"
#include <zlib.h>
#include <string.h>
#include <math.h>

static uint64_t deflate_compressed_size(const void *data, size_t len) {
    if (!data || len == 0) return 0;
    z_stream stream;
    memset(&stream, 0, sizeof(stream));
    if (deflateInit(&stream, Z_DEFAULT_COMPRESSION) != Z_OK) return len * 8;
    stream.next_in = (Bytef*)data;
    stream.avail_in = (uInt)len;
    uint64_t total_out = 0;
    uint8_t buf[1024];
    do {
        stream.next_out = buf;
        stream.avail_out = sizeof(buf);
        int ret = deflate(&stream, Z_FINISH);
        total_out += sizeof(buf) - stream.avail_out;
        if (ret == Z_STREAM_END) break;
    } while (stream.avail_out == 0);
    deflateEnd(&stream);
    return total_out;
}

void crag_pack_request(const CragRequest *req, uint8_t out[CRAG_REQUEST_SIZE]) {
    out[0] = req->version;
    out[1] = req->method;
    memcpy(out+2, req->zone_id, 4);
    memcpy(out+6, req->query_hash, 16);
    out[22] = req->max_retrieved;
    out[23] = req->flags;
    memcpy(out+24, req->payload, 168);
}

void crag_unpack_request(const uint8_t data[CRAG_REQUEST_SIZE], CragRequest *req) {
    req->version = data[0];
    req->method  = data[1];
    memcpy(req->zone_id, data+2, 4);
    memcpy(req->query_hash, data+6, 16);
    req->max_retrieved = data[22];
    req->flags = data[23];
    memcpy(req->payload, data+24, 168);
}

double kolmogorov_estimate(const char *text, size_t len) {
    if (len == 0) return 0.0;
    uint64_t compressed_bits = deflate_compressed_size(text, len) * 8;
    return (double)compressed_bits + 512.0;
}

double kolmogorov_gap(const char *query, const char *source, const char *response) {
    if (!query || !source || !response) return 0.0;
    double kt_q = kolmogorov_estimate(query, strlen(query));
    double kt_s = kolmogorov_estimate(source, strlen(source));
    double kt_r = kolmogorov_estimate(response, strlen(response));
    return kt_r - kt_s - kt_q;
}

FinalityLevel gap_to_finality(double gap) {
    if (gap > 25.0) return FINALITY_PENDING;
    if (gap > 15.0) return FINALITY_L0;
    if (gap > 5.0)  return FINALITY_L1;
    return FINALITY_L2;
}
