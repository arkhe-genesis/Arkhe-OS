/*
 * ARKHE Ω-TEMP — SHA3-256 para Windows Kernel
 *
 * Usa Windows CNG (Cryptography API: Next Generation)
 * para SHA3-256 acelerado por hardware.
 *
 * Alternativa: implementação pura em C (mais lenta, mas funciona sem CNG).
 */

#include <ntddk.h>
#include <bcrypt.h>
#include "arkhe_wdm.h"

#pragma comment(lib, "bcrypt.lib")

/* Cache do handle do algoritmo SHA3-256 */
static BCRYPT_ALG_HANDLE g_sha3Alg = NULL;
static KSPIN_LOCK g_sha3Lock;
static BOOLEAN g_sha3Initialized = FALSE;

/*
 * Inicializar SHA3-256 via CNG
 */
NTSTATUS InitializeSha3_256(VOID)
{
    NTSTATUS status;

    /* Usar BCRYPT_SHA3_256_ALGORITHM se disponível (Windows 10+ 19H1+) */
    status = BCryptOpenAlgorithmProvider(
        &g_sha3Alg,
        BCRYPT_SHA3_256_ALGORITHM,   /* SHA3-256 */
        MS_PRIMITIVE_PROVIDER,
        0);

    if (!NT_SUCCESS(status)) {
        /* SHA3-256 não disponível via CNG — usar implementação em software */
        KdPrint(("ARKHE: SHA3-256 CNG não disponível, usando software\n"));
        g_sha3Alg = NULL;
        return STATUS_SUCCESS;  /* Continue com fallback */
    }

    KeInitializeSpinLock(&g_sha3Lock);
    g_sha3Initialized = TRUE;

    KdPrint(("ARKHE: SHA3-256 via CNG inicializado\n"));
    return STATUS_SUCCESS;
}

/*
 * Hash via CNG (se disponível)
 */
NTSTATUS ComputeSha3_256_CNG(
    _In_reads_bytes_(InputSize) PUCHAR Input,
    _In_ ULONG InputSize,
    _Out_writes_bytes_(ARKHE_HASH_SIZE) PUCHAR Output)
{
    NTSTATUS status;
    BCRYPT_HASH_HANDLE hashHandle = NULL;
    ULONG hashObjectSize = 0;
    ULONG hashSize = 0;
    PUCHAR hashObject = NULL;

    if (!g_sha3Initialized || !g_sha3Alg) {
        return STATUS_NOT_SUPPORTED;
    }

    /* Obter tamanho do objeto hash */
    status = BCryptGetProperty(
        g_sha3Alg,
        BCRYPT_OBJECT_LENGTH,
        (PUCHAR)&hashObjectSize,
        sizeof(hashObjectSize),
        &hashSize,
        0);
    if (!NT_SUCCESS(status)) goto cleanup;

    /* Obter tamanho do hash */
    status = BCryptGetProperty(
        g_sha3Alg,
        BCRYPT_HASH_LENGTH,
        (PUCHAR)&hashSize,
        sizeof(hashSize),
        &hashSize,
        0);
    if (!NT_SUCCESS(status)) goto cleanup;

    /* Alocar objeto hash */
    hashObject = ExAllocatePool2(POOL_FLAG_NON_PAGED,
                                  hashObjectSize, 'KHR1');
    if (!hashObject) {
        status = STATUS_INSUFFICIENT_RESOURCES;
        goto cleanup;
    }

    /* Criar hash */
    status = BCryptCreateHash(
        g_sha3Alg,
        &hashHandle,
        hashObject,
        hashObjectSize,
        NULL,
        0,
        0);
    if (!NT_SUCCESS(status)) goto cleanup;

    /* Hash os dados */
    status = BCryptHashData(
        hashHandle,
        Input,
        InputSize,
        0);
    if (!NT_SUCCESS(status)) goto cleanup;

    /* Finalizar hash */
    status = BCryptFinishHash(
        hashHandle,
        Output,
        ARKHE_HASH_SIZE,
        0);

cleanup:
    if (hashHandle) BCryptDestroyHash(hashHandle);
    if (hashObject) ExFreePool(hashObject);

    return status;
}

/*
 * SHA3-256 Software Fallback
 * Implementação Keccak-f[1600] em C puro para kernel
 * (mesma lógica que a versão userspace, mas sem alocação dinâmica)
 */

typedef struct _KECCAK_STATE {
    ULONGLONG state[25]; /* 1600 bits = 25 × 64 bits */
    ULONG rateBytes;     /* 136 bytes para SHA3-256 */
    ULONG capacityBytes; /* 64 bytes para SHA3-256 */
} KECCAK_STATE, *PKECCAK_STATE;

/* Round constants para Keccak-f[1600] */
static const ULONGLONG keccak_rc[24] = {
    0x0000000000000001ULL,
    0x0000000000008082ULL,
    0x800000000000808AULL,
    0x8000000080008000ULL,
    0x000000000000808BULL,
    0x0000000080000001ULL,
    0x8000000080008081ULL,
    0x8000000000008009ULL,
    0x000000000000008AULL,
    0x0000000000000088ULL,
    0x0000000080008009ULL,
    0x000000008000000AULL,
    0x0000000080008081ULL,
    0x8000000000008080ULL,
    0x0000000000000001ULL,
    0x8000000080008008ULL,
};

/* Rho offsets para as 25 lanes */
static const ULONG keccak_rho[25] = {
     0,  1, 62, 28, 27,
    36, 44,  6, 55, 20,
     3, 10, 43, 25, 39,
    41, 45, 15, 21,  8,
    18,  2, 61, 56, 14,
};

/* Pi offsets para permutação */
static const ULONG keccak_pi[25] = {
     0,  6, 12, 18, 24,
     3,  9, 10, 16, 22,
     1,  7, 13, 19, 20,
     4,  5, 11, 17, 23,
     2,  8, 14, 15, 21,
};

/*
 * Inicializar estado Keccak
 */
static VOID KeccakInit(PKECCAK_STATE State)
{
    RtlZeroMemory(State->state, sizeof(State->state));
}

/*
 * Absorver dados no estado Keccak
 * SHA3-256 usa rate = 1088 bits = 136 bytes
 */
static VOID KeccakAbsorb(
    PKECCAK_STATE State,
    _In_reads_bytes_(InputSize) PUCHAR Input,
    ULONG InputSize)
{
    ULONG rateBytes = 136; /* SHA3-256 rate */
    ULONG blockSize;

    while (InputSize > 0) {
        blockSize = min(InputSize, rateBytes);

        /* XOR dados no estado */
        for (ULONG i = 0; i < blockSize / 8; i++) {
            State->state[i] ^= ((PULONGLONG)Input)[i];
        }

        /* Aplicar padding se necessário */
        if (blockSize < rateBytes) {
            /* Pad10*1 */
            UCHAR pad = 0x06; /* Primeiro e último bit */
            State->state[blockSize / 8] ^= (ULONGLONG)pad <<
                                             ((blockSize % 8) * 8);
            State->state[rateBytes / 8 - 1] ^= 0x80ULL;

            /* Permutação */
            KeccakF1600(State);
            break;
        }

        /* Permutação */
        KeccakF1600(State);

        Input += rateBytes;
        InputSize -= rateBytes;
    }
}

/*
 * Extrair hash do estado
 */
static VOID KeccakSqueeze(
    PKECCAK_STATE State,
    _Out_writes_bytes_(OutputSize) PUCHAR Output,
    ULONG OutputSize)
{
    ULONG rateBytes = 136;
    ULONG offset = 0;

    while (offset < OutputSize) {
        ULONG toExtract = min(rateBytes, OutputSize - offset);

        RtlCopyMemory(
            &Output[offset],
            &State->state[0],
            toExtract);

        if (toExtract < rateBytes) break;

        KeccakF1600(State);
        offset += toExtract;
    }
}

/*
 * Keccak-f[1600] Permutação
 * 24 rounds de θ, ρ, π, χ, ι
 */
static VOID KeccakF1600(PKECCAK_STATE State)
{
    ULONGLONG C[5], D[5];
    ULONGLONG temp;
    ULONG round;

    for (round = 0; round < 24; round++) {
        /* θ step: Compute C and D */
        for (ULONG x = 0; x < 5; x++) {
            C[x] = State->state[x] ^
                   State->state[x + 5] ^
                   State->state[x + 10] ^
                   State->state[x + 15] ^
                   State->state[x + 20];
        }

        for (ULONG x = 0; x < 5; x++) {
            D[x] = C[(x + 4) % 5] ^
                   ROR64(C[(x + 1) % 5], 1);
        }

        for (ULONG x = 0; x < 5; x++) {
            for (ULONG y = 0; y < 5; y++) {
                State->state[x + 5*y] ^= D[x];
            }
        }

        /* ρ and π steps */
        {
            ULONGLONG B[25];

            for (ULONG i = 0; i < 25; i++) {
                ULONG pi_idx = keccak_pi[i];
                B[i] = ROR64(State->state[pi_idx], keccak_rho[pi_idx]);
            }

            RtlCopyMemory(State->state, B, sizeof(B));
        }

        /* χ step */
        for (ULONG y = 0; y < 5; y++) {
            for (ULONG x = 0; x < 5; x++) {
                ULONG idx = x + 5*y;
                ULONG next1 = ((x + 1) % 5) + 5*y;
                ULONG next2 = ((x + 2) % 5) + 5*y;

                temp = State->state[idx] ^
                       ((~State->state[next1]) & State->state[next2]);
                State->state[idx] = temp;
            }
        }

        /* ι step */
        State->state[0] ^= keccak_rc[round];
    }
}

/*
 * Rotação à direita de 64 bits
 */
static ULONGLONG ROR64(ULONGLONG value, ULONG shift)
{
    shift %= 64;
    return (value >> shift) | (value << (64 - shift));
}

/*
 * Exportada: computar SHA3-256 de dados
 * Usa CNG se disponível, senão fallback software
 */
NTSTATUS NTAPI ComputeSha3_256(
    _In_reads_bytes_(InputSize) PUCHAR Input,
    _In_ ULONG InputSize,
    _Out_writes_bytes_(ARKHE_HASH_SIZE) PUCHAR Output)
{
    NTSTATUS status;

    /* Tentar CNG primeiro */
    if (g_sha3Initialized) {
        status = ComputeSha3_256_CNG(Input, InputSize, Output);
        if (NT_SUCCESS(status)) return status;
    }

    /* Fallback software */
    {
        KECCAK_STATE state;
        KeccakInit(&state);
        KeccakAbsorb(&state, Input, InputSize);

        /* Squeeze apenas 32 bytes (256 bits) */
        UCHAR squeezed[136];
        KeccakSqueeze(&state, squeezed, 32);
        RtlCopyMemory(Output, squeezed, 32);
    }

    return STATUS_SUCCESS;
}
