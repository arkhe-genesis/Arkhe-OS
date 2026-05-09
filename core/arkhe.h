#ifndef ARKHE_INTEROP_H
#define ARKHE_INTEROP_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Estrutura compacta de requisição C-RAG (192 bytes) */
#define CRAG_REQUEST_SIZE 192
typedef struct {
    uint8_t  version;
    uint8_t  method;          /* 0=GET, 1=POST, 2=CEREMONY */
    uint8_t  zone_id[4];
    uint8_t  query_hash[16];
    uint8_t  max_retrieved;
    uint8_t  flags;
    uint8_t  payload[168];
} CragRequest;

/* Finalidade da coerência (níveis Arxia) */
typedef enum {
    FINALITY_PENDING = 0,
    FINALITY_L0      = 1,
    FINALITY_L1      = 2,
    FINALITY_L2      = 3
} FinalityLevel;

/**
 * Empacota uma query C-RAG em um buffer de 192 bytes pronto para transmissão.
 */
void crag_pack_request(const CragRequest *req, uint8_t out[CRAG_REQUEST_SIZE]);

/**
 * Desempacota um buffer de 192 bytes em uma CragRequest.
 */
void crag_unpack_request(const uint8_t data[CRAG_REQUEST_SIZE], CragRequest *req);

/**
 * Estima a complexidade de Kolmogorov (K^t) de um texto via razão de compressão DEFLATE.
 * Retorna valor em bits (aproximado).  Quanto menor, mais simples/coerente.
 */
double kolmogorov_estimate(const char *text, size_t len);

/**
 * Calcula o gap de alucinação: ΔK = K(y) - K(source) - K(query).
 */
double kolmogorov_gap(const char *query, const char *source, const char *response);

/**
 * Converte um gap ΔK em nível de finalidade.
 */
FinalityLevel gap_to_finality(double gap);

#ifdef __cplusplus
}
#endif

#endif
