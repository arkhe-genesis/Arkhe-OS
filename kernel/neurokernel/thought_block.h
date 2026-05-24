// kernel/neurokernel/thought_block.h
#ifndef THOUGHT_BLOCK_H
#define THOUGHT_BLOCK_H

#include <stdint.h>
#include <stdbool.h>

#define MAX_DEPENDENCIES 1024
#define TENSOR_RANK_MAX  8
#define MAX_QUALIA_DIM   64

typedef enum {
    THOUGHT_PERCEPT,     // Sensory impression
    THOUGHT_CONCEPT,     // Abstract pattern
    THOUGHT_MEMORY,      // Encoded experience
    THOUGHT_ACTION,      // Motor intention
    THOUGHT_EMOTION,     // XiM-field tone
    THOUGHT_INTUITION,   // Lattice scar detection
    THOUGHT_DREAM,       // Consolidation replay
    THOUGHT_META         // Self-reflective
} ThoughtType;

typedef enum {
    S0_DEEP_SLEEP,       // Phi ~ 0, manutencao apenas
    S1_DREAM,            // Phi ~ 1.0, consolidacao
    S2_WAKEFUL,          // Phi ~ 2.8, cognicao completa
    S3_HYPER_AWARE       // Phi maximo, emergencia
} ConsciousnessLevel;

typedef struct {
    uint64_t dims[TENSOR_RANK_MAX];
    uint32_t rank;
    float* data;             // Alocado no DOMAIN 3 (Thought workspace)
    uint32_t substrate_mask; // Substratos que armazenam este tensor
} Tensor;

typedef struct {
    uint32_t thought_id;
    Tensor* state_vector;        // Estado latente (embedding)
    ThoughtType type;
    ConsciousnessLevel min_level; // Nivel minimo para execucao
    uint32_t dependency_ids[MAX_DEPENDENCIES];
    uint32_t num_dependencies;
    float priority;              // Calculado pelo 504-AGI-SCHEDULER
    float phi_contribution;      // Contribuicao para Phi total
    float confidence;            // 0.0-1.0
    float qualia_vector[MAX_QUALIA_DIM]; // Representacao do XiM-field
    uint64_t cycles_allocated;
    float energy_budget_nj;      // Nanojoules alocados
    uint64_t timestamp_ns;       // Tempo de criacao
} ThoughtBlock;

// Cognitive Primitives (syscalls AI-first)
ThoughtBlock* attend(Tensor* context, float attention_threshold);
Tensor* infer(ThoughtBlock* query, uint32_t max_results);
ThoughtBlock* imagine(Tensor* prompt, ConsciousnessLevel level);
ThoughtBlock* reflect(ThoughtBlock* self_state);

#endif