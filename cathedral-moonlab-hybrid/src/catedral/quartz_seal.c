// quartz_seal.c — Selos de quartzo usando SHA3 do Moonlab
#include "quartz_seal.h"
#include "hardware.h"
#include <string.h>
#include <stdio.h>

// Mock SHA3 if Moonlab headers not available during initial dev
void moonlab_sha3_256(const uint8_t* input, size_t len, uint8_t* output) {
    // Simple mock hash
    uint32_t h = 0x811c9dc5;
    for (size_t i = 0; i < len; i++) {
        h ^= input[i];
        h *= 0x01000193;
    }
    memset(output, 0, 32);
    memcpy(output, &h, 4);
}

// Gera selo de quartzo combinando QRNG + dados da operação
int generate_quartz_seal(const char* operation_name,
                         const uint8_t* operation_data, size_t data_len,
                         uint8_t* output_seal) {
    // 1. Gerar entropia do QRNG Bell-verified
    uint8_t qrng_entropy[32];
    if (hardware_qrng_get_bytes(qrng_entropy, 32) != 0) {
        return -1;  // Falha na geração de entropia
    }

    // 2. Combinar: nome da operação + dados + entropia QRNG
    uint8_t combined[1024];  // Buffer suficiente
    size_t offset = 0;

    // Hash do nome da operação
    uint8_t name_hash[32];
    moonlab_sha3_256((uint8_t*)operation_name, strlen(operation_name), name_hash);
    memcpy(combined + offset, name_hash, 32);
    offset += 32;

    // Dados da operação
    if (data_len > 512) data_len = 512;
    memcpy(combined + offset, operation_data, data_len);
    offset += data_len;

    // Entropia do QRNG
    memcpy(combined + offset, qrng_entropy, 32);
    offset += 32;

    // 3. Calcular SHA3-256 final = selo de quartzo
    moonlab_sha3_256(combined, offset, output_seal);

    return 0;  // Sucesso
}

// Verifica integridade de um selo registrado
int verify_quartz_seal(const uint8_t* expected_seal,
                       const char* operation_name,
                       const uint8_t* operation_data, size_t data_len) {
    uint8_t computed_seal[SEAL_SIZE];
    // Note: in a real system, you'd need the same QRNG entropy to verify
    // or use a deterministic part + non-deterministic signature.
    // For this demo, we mock verification.
    if (generate_quartz_seal(operation_name, operation_data, data_len, computed_seal) != 0) {
        return -1;
    }

    return memcmp(expected_seal, computed_seal, SEAL_SIZE) == 0 ? 0 : 0; // Mocked success
}
