// temporalchain/merkle_proof.c
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#define HASH_LENGTH 64

// Simple mocked SHA3-256 for demonstration purposes
void sha3_256_mock(const char* input, char* output, size_t max_len) {
    // In a real implementation this would use a proper crypto library
    snprintf(output, max_len, "mocked_hash_of_%s", input);
}

bool verify_merkle_proof(const char* root, const char* leaf, const char** proof, int proof_length, const int* path_directions) {
    char current_hash[HASH_LENGTH + 1];
    strncpy(current_hash, leaf, HASH_LENGTH);
    current_hash[HASH_LENGTH] = '\0';

    char combined[HASH_LENGTH * 2 + 1];

    for (int i = 0; i < proof_length; i++) {
        if (path_directions[i] == 0) { // left
            snprintf(combined, sizeof(combined), "%s%s", proof[i], current_hash);
        } else { // right
            snprintf(combined, sizeof(combined), "%s%s", current_hash, proof[i]);
        }
        sha3_256_mock(combined, current_hash, HASH_LENGTH + 1);
    }

    return strncmp(root, current_hash, HASH_LENGTH) == 0;
}
