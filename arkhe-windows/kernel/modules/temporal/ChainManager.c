/*
 * ARKHE Ω-TEMP — Gerenciador da Cadeia Temporal
 *
 * Responsável por:
 *   - Armazenar blocos temporais em ordem
 *   - Garantir integridade hash chain
 *   - Computar Merkle roots
 *   - Resolver forks (reorganização de cadeia)
 *
 * A cadeia temporal é implementada como uma lista duplamente encadeada
 * com índice hash para acesso O(1) por hash.
 *
 * Sincronização: Spin locks para hot paths, mutex para operações longas.
 */

#include "arkhe_wdm.h"
#include "ChainManager.h"

/*
 * Estrutura do Bloco Temporal (kernel)
 * Layout otimizado para cache line (64 bytes)
 */
typedef struct _TEMPORAL_BLOCK {
    LIST_ENTRY          ListEntry;          /* Encadeamento */
    ULONGLONG           Index;              /* Altura do bloco */
    LARGE_INTEGER       Timestamp;          /* Timestamp em 100ns */
    UCHAR               PrevHash[ARKHE_HASH_SIZE];
    UCHAR               StateRoot[ARKHE_HASH_SIZE];
    UCHAR               OracleRoot[ARKHE_HASH_SIZE];
    ULONG               PayloadSize;
    UCHAR               Payload[1];         /* Flexible array member */
    UCHAR               BlockHash[ARKHE_HASH_SIZE];
} TEMPORAL_BLOCK, *PTEMPORAL_BLOCK;

#define TEMPORAL_BLOCK_HEADER_SIZE \
    (sizeof(TEMPORAL_BLOCK) - sizeof(((PTEMPORAL_BLOCK)0)->Payload))

/*
 * Inicializar cadeia temporal
 */
NTSTATUS InitializeTemporalChain(ARKHE_DRIVER_CONTEXT* Context)
{
    NTSTATUS status;

    KeInitializeSpinLock(&Context->TemporalChain.Lock);
    InitializeListHead(&Context->TemporalChain.Head);
    Context->TemporalChain.Length = 0;
    Context->TemporalChain.MaxLength = ARKHE_MAX_BLOCKS;

    /* Criar bloco gênesis */
    status = CreateGenesisBlock(Context);
    if (!NT_SUCCESS(status)) {
        KdPrint(("ARKHE: Falha ao criar bloco genesis (0x%08X)\n", status));
        return status;
    }

    KdPrint(("ARKHE: Cadeia temporal inicializada com %llu blocos\n",
             Context->TemporalChain.Length));

    return STATUS_SUCCESS;
}

/*
 * Criar bloco gênesis
 * O bloco gênesis é o bloco 0, sem predecessor.
 * Seu hash é computado a partir de seu conteúdo fixo.
 */
NTSTATUS CreateGenesisBlock(ARKHE_DRIVER_CONTEXT* Context)
{
    NTSTATUS status;
    PTEMPORAL_BLOCK genesis;
    ULONG genesisSize;
    UCHAR genesisPayload[] = {
        'A','R','K','H','E','_','G','E','N','E','S','I','S',
        '_','V','4','_','3','_','7'
    };

    genesisSize = TEMPORAL_BLOCK_HEADER_SIZE + sizeof(genesisPayload);
    genesis = ExAllocatePool2(POOL_FLAG_NON_PAGED, genesisSize, 'KHR1');
    if (!genesis) return STATUS_INSUFFICIENT_RESOURCES;

    RtlZeroMemory(genesis, genesisSize);

    genesis->Index = 0;
    KeQuerySystemTime(&genesis->Timestamp);
    genesis->PayloadSize = sizeof(genesisPayload);
    RtlCopyMemory(genesis->Payload, genesisPayload, sizeof(genesisPayload));

    /* Computar State Root = SHA3-256(payload) */
    status = ComputeSha3_256(genesis->Payload, genesis->PayloadSize,
                              genesis->StateRoot);
    if (!NT_SUCCESS(status)) {
        ExFreePool(genesis);
        return status;
    }

    /* PrevHash = 0 */
    RtlZeroMemory(genesis->PrevHash, ARKHE_HASH_SIZE);

    /* Computar Block Hash */
    status = ComputeBlockHash(genesis, genesis->BlockHash);
    if (!NT_SUCCESS(status)) {
        ExFreePool(genesis);
        return status;
    }

    /* Marcar como genesis */
    genesis->BlockHash[0] = 0xCA;  /* 0xCA71 = Cathedral */
    genesis->BlockHash[1] = 0x71;

    /* Adicionar à cadeia */
    InsertTailList(&Context->TemporalChain.Head, &genesis->ListEntry);
    Context->TemporalChain.Length++;
    Context->TemporalChain.Genesis = genesis;

    /* Copiar State Root para contexto global */
    RtlCopyMemory(Context->TemporalChain.ChainStateRoot,
                  genesis->StateRoot, ARKHE_HASH_SIZE);

    KdPrint(("ARKHE: Genesis criado: StateRoot=%s\n",
             FormatHash(genesis->StateRoot)));

    return STATUS_SUCCESS;
}

/*
 * Inserir bloco na cadeia temporal
 *
 * Validação:
 * 1. Índice deve ser último + 1
 * 2. PrevHash deve bater com hash do bloco anterior
 * 3. Timestamp deve ser posterior
 * 4. StateRoot deve corresponder ao Merkle root do payload
 * 5. BlockHash deve ser SHA3-256 do bloco (sem o próprio hash)
 */
NTSTATUS InsertTemporalBlock(
    ARKHE_DRIVER_CONTEXT* Context,
    PTEMPORAL_BLOCK NewBlock)
{
    KIRQL oldIrql;
    PLIST_ENTRY lastEntry;
    PTEMPORAL_BLOCK lastBlock;
    NTSTATUS status;

    /* Validar tamanho mínimo */
    if (NewBlock->PayloadSize < TEMPORAL_BLOCK_HEADER_SIZE) {
        return STATUS_INVALID_PARAMETER;
    }

    /* Validação do bloco (sem lock para permitir paralelismo) */
    status = ValidateTemporalBlock(Context, NewBlock);
    if (!NT_SUCCESS(status)) {
        KdPrint(("ARKHE: Bloco rejeitado: 0x%08X\n", status));
        return status;
    }

    /* Adicionar à lista (sob lock) */
    KeAcquireSpinLock(&Context->TemporalChain.Lock, &oldIrql);

    /* Verificar duplicidade */
    if (BlockExists(Context, NewBlock->BlockHash)) {
        KeReleaseSpinLock(&Context->TemporalChain.Lock, oldIrql);
        return STATUS_ALREADY_REGISTERED;
    }

    /* Inserir no final */
    InsertTailList(&Context->TemporalChain.Head,
                   &NewBlock->ListEntry);
    Context->TemporalChain.Length++;

    /* Atualizar state root */
    RtlCopyMemory(Context->TemporalChain.ChainStateRoot,
                  NewBlock->StateRoot, ARKHE_HASH_SIZE);

    KeReleaseSpinLock(&Context->TemporalChain.Lock, oldIrql);

    KdPrint(("ARKHE: Bloco %llu inserido (hash=%s)\n",
             NewBlock->Index, FormatHash(NewBlock->BlockHash)));

    /* Notificar userspace via evento */
    NotifyBlockAdded(Context, NewBlock);

    return STATUS_SUCCESS;
}

/*
 * Validação completa de um bloco temporal
 */
NTSTATUS ValidateTemporalBlock(
    ARKHE_DRIVER_CONTEXT* Context,
    PTEMPORAL_BLOCK Block)
{
    PTEMPORAL_BLOCK prev;
    UCHAR computedHash[ARKHE_HASH_SIZE];
    UCHAR merkleRoot[ARKHE_HASH_SIZE];
    NTSTATUS status;

    /* 1. Verificar índice */
    prev = GetLastBlock(Context);
    if (prev) {
        if (Block->Index != prev->Index + 1) {
            KdPrint(("ARKHE: Índice inválido: %llu (esperado %llu)\n",
                     Block->Index, prev->Index + 1));
            return STATUS_INVALID_BLOCK;
        }
    } else if (Block->Index != 0) {
        return STATUS_INVALID_BLOCK;
    }

    /* 2. Verificar prev_hash */
    if (prev) {
        if (RtlCompareMemory(Block->PrevHash,
                              prev->BlockHash,
                              ARKHE_HASH_SIZE) != ARKHE_HASH_SIZE) {
            KdPrint(("ARKHE: prev_hash não confere\n"));
            return STATUS_INVALID_BLOCK;
        }
    }

    /* 3. Verificar timestamp */
    if (prev && Block->Timestamp.QuadPart <= prev->Timestamp.QuadPart) {
        KdPrint(("ARKHE: Timestamp não-causal\n"));
        return STATUS_INVALID_TEMPORAL;
    }

    /* 4. Verificar Merkle root */
    if (Block->PayloadSize > TEMPORAL_BLOCK_HEADER_SIZE) {
        ULONG numHashes = (Block->PayloadSize - TEMPORAL_BLOCK_HEADER_SIZE)
                          / ARKHE_HASH_SIZE;
        status = ComputeMerkleRoot(Block->Payload, numHashes, merkleRoot);
        if (!NT_SUCCESS(status)) return status;

        if (RtlCompareMemory(Block->StateRoot, merkleRoot,
                              ARKHE_HASH_SIZE) != ARKHE_HASH_SIZE) {
            KdPrint(("ARKHE: Merkle root inválido\n"));
            return STATUS_INVALID_MERKLE;
        }
    }

    /* 5. Verificar block hash */
    status = ComputeBlockHash(Block, computedHash);
    if (!NT_SUCCESS(status)) return status;

    if (RtlCompareMemory(Block->BlockHash, computedHash,
                          ARKHE_HASH_SIZE) != ARKHE_HASH_SIZE) {
        KdPrint(("ARKHE: Block hash inválido\n"));
        return STATUS_INVALID_HASH;
    }

    return STATUS_SUCCESS;
}

/*
 * Computar hash do bloco
 * SHA3-256(tudo exceto BlockHash)
 */
NTSTATUS ComputeBlockHash(
    PTEMPORAL_BLOCK Block,
    UCHAR Output[ARKHE_HASH_SIZE])
{
    ULONG offset;
    UCHAR* data;
    ULONG dataSize;

    /* O hash é sobre tudo exceto o campo BlockHash */
    offset = FIELD_OFFSET(TEMPORAL_BLOCK, BlockHash);
    data = (UCHAR*)Block;
    dataSize = TEMPORAL_BLOCK_HEADER_SIZE + Block->PayloadSize -
               ARKHE_HASH_SIZE;  /* - BlockHash */

    return ComputeSha3_256(data, dataSize, Output);
}

/*
 * Buscar bloco por hash (O(1) via hash table)
 */
PTEMPORAL_BLOCK FindBlockByHash(
    ARKHE_DRIVER_CONTEXT* Context,
    UCHAR Hash[ARKHE_HASH_SIZE])
{
    ULONG hashIdx;
    PLIST_ENTRY entry;
    PTEMPORAL_BLOCK block;

    hashIdx = HashToBucket(Hash);

    KIRQL oldIrql;
    KeAcquireSpinLock(&Context->TemporalChain.Lock, &oldIrql);
    entry = Context->TemporalChain.HashTable[hashIdx].Flink;
    while (entry != &Context->TemporalChain.HashTable[hashIdx]) {
        block = CONTAINING_RECORD(entry, TEMPORAL_BLOCK, ListEntry);
        if (RtlCompareMemory(block->BlockHash, Hash,
                              ARKHE_HASH_SIZE) == ARKHE_HASH_SIZE) {
            KeReleaseSpinLock(&Context->TemporalChain.Lock, oldIrql);
            return block;
        }
        entry = entry->Flink;
    }
    KeReleaseSpinLock(&Context->TemporalChain.Lock, oldIrql);

    return NULL;
}

/*
 * Iterador temporal (forward ou backward)
 */
NTSTATUS CreateTemporalIterator(
    ARKHE_DRIVER_CONTEXT* Context,
    BOOLEAN Forward,
    PTEMPORAL_ITERATOR* Iterator)
{
    *Iterator = ExAllocatePool2(POOL_FLAG_NON_PAGED,
                                sizeof(TEMPORAL_ITERATOR), 'KHR1');
    if (!*Iterator) return STATUS_INSUFFICIENT_RESOURCES;

    if (Forward) {
        (*Iterator)->Current = Context->TemporalChain.Head.Flink;
    } else {
        (*Iterator)->Current = Context->TemporalChain.Head.Blink;
    }
    (*Iterator)->Forward = Forward;

    return STATUS_SUCCESS;
}
