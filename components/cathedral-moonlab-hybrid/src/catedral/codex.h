#ifndef CODEX_H
#define CODEX_H

#include <stdint.h>
#include <stddef.h>

#define MAX_ENTRIES 10000

typedef struct {
    uint64_t timestamp;
    uint8_t operation_hash[32];      // SHA3 do payload da operação
    uint8_t quartz_seal[32];          // Selo de quartzo
    float integrity_score;            // Score de auditoria híbrida [0, 1]
    uint8_t merkle_proof[32];         // Prova Merkle para validação
} CodexEntry;

int codex_append(const CodexEntry* entry);
int codex_verify_integrity(void);

#endif // CODEX_H
