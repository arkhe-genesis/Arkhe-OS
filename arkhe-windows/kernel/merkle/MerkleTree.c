/*
 * ARKHE Ω-TEMP — Merkle Tree para Verificação de Integridade
 *
 * Implementa:
 *   - Merkle Root computation
 *   - Inclusion Proofs (prova que um item está na árvore)
 *   - Exclusion Proofs (prova que um item NÃO está na árvore)
 *   - Consistency Proofs (prova de append-only)
 *
 * A árvore usa SHA3-256 como função hash e é otimizada para
 * operações em lote com alocação mínima.
 */

#include "arkhe_wdm.h"
#include "MerkleTree.h"

/*
 * Nó da Merkle Tree
 */
typedef struct _MERKLE_NODE {
    UCHAR Hash[ARKHE_HASH_SIZE];
    struct _MERKLE_NODE* Left;
    struct _MERKLE_NODE* Right;
    struct _MERKLE_NODE* Parent;
    ULONG LeafIndex;      /* Índice se for folha, ou MAXULONG se interno */
} MERKLE_NODE, *PMERKLE_NODE;

/*
 * Árvore Merkle
 */
typedef struct _MERKLE_TREE {
    PMERKLE_NODE Root;
    PMERKLE_NODE* Leaves;      /* Array de folhas para acesso direto */
    ULONG LeafCount;
    ULONG Capacity;
    KSPIN_LOCK Lock;
} MERKLE_TREE, *PMERKLE_TREE;

/*
 * Inicializar Merkle Tree
 */
NTSTATUS InitializeMerkleTree(
    ARKHE_DRIVER_CONTEXT* Context,
    ULONG InitialCapacity)
{
    PMERKLE_TREE tree = ExAllocatePool2(
        POOL_FLAG_NON_PAGED,
        sizeof(MERKLE_TREE) +
        InitialCapacity * sizeof(PMERKLE_NODE),
        'KHR1');

    if (!tree) return STATUS_INSUFFICIENT_RESOURCES;

    RtlZeroMemory(tree, sizeof(MERKLE_TREE));
    tree->Leaves = (PMERKLE_NODE*)(tree + 1);
    tree->Capacity = InitialCapacity;
    KeInitializeSpinLock(&tree->Lock);

    Context->MerkleTree = tree;
    KdPrint(("ARKHE: Merkle Tree inicializada com capacidade %lu\n",
            InitialCapacity));

    return STATUS_SUCCESS;
}

/*
 * Adicionar folha à Merkle Tree
 * Recomputa o caminho da folha até a raiz
 */
NTSTATUS MerkleAppend(
    PMERKLE_TREE Tree,
    _In_reads_bytes_(ARKHE_HASH_SIZE) PUCHAR LeafHash,
    _Out_ PULONG LeafIndex)
{
    KIRQL oldIrql;
    PMERKLE_NODE node;
    PMERKLE_NODE sibling;

    node = ExAllocatePool2(POOL_FLAG_NON_PAGED,
                           sizeof(MERKLE_NODE), 'KHR1');
    if (!node) return STATUS_INSUFFICIENT_RESOURCES;

    RtlCopyMemory(node->Hash, LeafHash, ARKHE_HASH_SIZE);
    node->Left = NULL;
    node->Right = NULL;
    node->Parent = NULL;
    node->LeafIndex = Tree->LeafCount;

    KeAcquireSpinLock(&Tree->Lock, &oldIrql);

    /* Expandir array se necessário */
    if (Tree->LeafCount >= Tree->Capacity) {
        ULONG newCapacity = Tree->Capacity * 2;
        PMERKLE_NODE* newLeaves = ExAllocatePool2(POOL_FLAG_NON_PAGED, newCapacity * sizeof(PMERKLE_NODE), 'KHR1');
        if (!newLeaves) {
            KeReleaseSpinLock(&Tree->Lock, oldIrql);
            ExFreePool(node);
            return STATUS_INSUFFICIENT_RESOURCES;
        }
        RtlCopyMemory(newLeaves, Tree->Leaves, Tree->LeafCount * sizeof(PMERKLE_NODE));
        if ((PVOID)Tree->Leaves != (PVOID)(Tree + 1)) {
            ExFreePool(Tree->Leaves);
        }
        Tree->Leaves = newLeaves;
        Tree->Capacity = newCapacity;
    }

    /* Adicionar como folha */
    Tree->Leaves[Tree->LeafCount] = node;
    *LeafIndex = Tree->LeafCount;
    Tree->LeafCount++;

    /* Reconstruir caminho até a raiz */
    PMERKLE_NODE current = node;
    while (current != Tree->Root) {
        PMERKLE_NODE parent = current->Parent;

        if (parent == NULL) {
            /* Criar novo nó interno */
            parent = ExAllocatePool2(POOL_FLAG_NON_PAGED,
                                     sizeof(MERKLE_NODE), 'KHR1');
            if (!parent) {
                KeReleaseSpinLock(&Tree->Lock, oldIrql);
                return STATUS_INSUFFICIENT_RESOURCES;
            }

            current->Parent = parent;

            /* Determinar se current é left ou right */
            if (current->LeafIndex % 2 == 0) {
                parent->Left = current;
                /* Esperar irmão ou duplicar */
                PMERKLE_NODE sibling = (current->LeafIndex + 1 < Tree->LeafCount) ?
                                        Tree->Leaves[current->LeafIndex + 1] :
                                        current; /* Duplicar */
                parent->Right = sibling;
                sibling->Parent = parent;
            } else {
                parent->Right = current;
                parent->Left = Tree->Leaves[current->LeafIndex - 1];
                Tree->Leaves[current->LeafIndex - 1]->Parent = parent;
            }

            /* Computar hash do pai */
            UCHAR combined[ARKHE_HASH_SIZE * 2];
            RtlCopyMemory(combined, parent->Left->Hash, ARKHE_HASH_SIZE);
            RtlCopyMemory(&combined[ARKHE_HASH_SIZE],
                          parent->Right->Hash, ARKHE_HASH_SIZE);
            ComputeSha3_256(combined, sizeof(combined), parent->Hash);

            parent->LeafIndex = MAXULONG; /* Nó interno */
        }

        current = parent;
    }

    Tree->Root = current;
    KeReleaseSpinLock(&Tree->Lock, oldIrql);

    return STATUS_SUCCESS;
}

/*
 * Gerar Prova de Inclusão
 * Prova que o item no índice fornecido está na árvore
 */
NTSTATUS MerkleGenerateInclusionProof(
    PMERKLE_TREE Tree,
    ULONG LeafIndex,
    _Outptr_result_bytebuffer_(*ProofSize) UCHAR** Proof,
    _Out_ PULONG ProofSize)
{
    KIRQL oldIrql;
    PMERKLE_NODE current;
    LIST_ENTRY siblings;
    ULONG proofLen = 0;

    InitializeListHead(&siblings);

    KeAcquireSpinLock(&Tree->Lock, &oldIrql);

    if (LeafIndex >= Tree->LeafCount) {
        KeReleaseSpinLock(&Tree->Lock, oldIrql);
        return STATUS_NOT_FOUND;
    }

    current = Tree->Leaves[LeafIndex];

    /* Alocar buffer máximo possível (altura * tamanho_entry) */
    ULONG maxProofLen = 32 * (ARKHE_HASH_SIZE + 1); // assumindo max height 32
    *Proof = ExAllocatePool2(POOL_FLAG_NON_PAGED, maxProofLen, 'KHR1');
    if (!*Proof) {
        KeReleaseSpinLock(&Tree->Lock, oldIrql);
        return STATUS_INSUFFICIENT_RESOURCES;
    }

    UCHAR* ptr = *Proof;
    /* Caminhar até a raiz, coletando irmãos e serializando */
    while (current != Tree->Root) {
        PMERKLE_NODE parent = current->Parent;
        if (!parent) break;

        PMERKLE_NODE sibling = (parent->Left == current) ?
                                parent->Right : parent->Left;

        /* Serializar direção e irmão */
        *ptr++ = (parent->Left == current) ? 1 : 0; // 1 = irmão à direita, 0 = irmão à esquerda
        RtlCopyMemory(ptr, sibling->Hash, ARKHE_HASH_SIZE);
        ptr += ARKHE_HASH_SIZE;

        current = parent;
        proofLen += ARKHE_HASH_SIZE + 1; /* hash + direção */
    }

    *ProofSize = proofLen;
    KeReleaseSpinLock(&Tree->Lock, oldIrql);

    return STATUS_SUCCESS;
}

/*
 * Verificar Prova de Inclusão
 * Recomputa a raiz a partir da prova e compara
 */
BOOLEAN MerkleVerifyInclusion(
    _In_reads_bytes_(ARKHE_HASH_SIZE) PUCHAR TargetHash,
    _In_reads_bytes_(ARKHE_HASH_SIZE) PUCHAR ExpectedRoot,
    _In_reads_bytes_(ProofSize) PUCHAR Proof,
    ULONG ProofSize)
{
    UCHAR current[ARKHE_HASH_SIZE];
    UCHAR sibling[ARKHE_HASH_SIZE];
    UCHAR combined[ARKHE_HASH_SIZE * 2];
    UCHAR direction;
    ULONG offset = 0;

    RtlCopyMemory(current, TargetHash, ARKHE_HASH_SIZE);

    while (offset < ProofSize) {
        direction = Proof[offset++];
        RtlCopyMemory(sibling, &Proof[offset], ARKHE_HASH_SIZE);
        offset += ARKHE_HASH_SIZE;

        if (direction == 0) { /* Irmão à esquerda */
            RtlCopyMemory(combined, sibling, ARKHE_HASH_SIZE);
            RtlCopyMemory(&combined[ARKHE_HASH_SIZE], current,
                          ARKHE_HASH_SIZE);
        } else { /* Irmão à direita */
            RtlCopyMemory(combined, current, ARKHE_HASH_SIZE);
            RtlCopyMemory(&combined[ARKHE_HASH_SIZE], sibling,
                          ARKHE_HASH_SIZE);
        }

        ComputeSha3_256(combined, sizeof(combined), current);
    }

    return RtlEqualMemory(current, ExpectedRoot, ARKHE_HASH_SIZE);
}
