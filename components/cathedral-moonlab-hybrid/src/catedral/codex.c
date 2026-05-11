// codex.c — Códice de auditoria com validação Merkle
#include "codex.h"
#include <string.h>

// Mock SHA3 if Moonlab headers not available
extern void moonlab_sha3_256(const uint8_t* input, size_t len, uint8_t* output);

static CodexEntry codex[MAX_ENTRIES];
static uint32_t codex_size = 0;
static uint8_t merkle_root[32];

// Adiciona entrada ao códice e atualiza raiz Merkle
int codex_append(const CodexEntry* entry) {
    if (codex_size >= MAX_ENTRIES) return -1;

    // Copiar entrada
    memcpy(&codex[codex_size], entry, sizeof(CodexEntry));

    // Atualizar raiz Merkle (simplificado: hash da última entrada + raiz anterior)
    uint8_t combined[64];
    memcpy(combined, merkle_root, 32);
    memcpy(combined + 32, entry->quartz_seal, 32);
    moonlab_sha3_256(combined, 64, merkle_root);

    codex_size++;
    return 0;
}

// Valida integridade do códice via raiz Merkle
int codex_verify_integrity(void) {
    // Recalcular raiz Merkle a partir das entradas
    uint8_t computed_root[32] = {0};

    for (uint32_t i = 0; i < codex_size; i++) {
        uint8_t combined[64];
        memcpy(combined, computed_root, 32);
        memcpy(combined + 32, codex[i].quartz_seal, 32);
        moonlab_sha3_256(combined, 64, computed_root);
    }

    return memcmp(computed_root, merkle_root, 32) == 0 ? 0 : -1;
}
