; ============================================================================
; ARKHE Ω-TEMP — Constantes e Macros
; ============================================================================

; ============================================================================
; Constantes de Rede
; ============================================================================
BLOCK_SIZE_MAX         equ     4194304          ; 4 MB
MAX_MESSAGES_PER_BLOCK equ     8192
BLOCK_INTERVAL_NSEC    equ     10000000000       ; 10 segundos em nanossegundos
CONSISTENCY_THRESHOLD  equ     0x3F333333        ; 0.85 em fixed-point Q32.32
PARADOX_SCORE          equ     0x3E99999A        ; 0.30 em fixed-point Q32.32

; ============================================================================
; Constantes criptográficas
; ============================================================================
SHA3_RATE_BYTES        equ     136               ; SHA3-256 rate = 1088 bits
SHA3_CAPACITY_BYTES    equ     64                ; SHA3-256 capacity = 512 bits
SHA3_OUTPUT_BYTES      equ     32                ; 256 bits
FALCON_PUBKEY_SIZE     equ     1792              ; ML-DSA-1024
FALCON_SECRET_SIZE     equ     3584              ; ML-DSA-1024
FALCON_SIGNATURE_SIZE  equ     1330              ; ML-DSA-1024 (máx)
MERKLE_LEAF_SIZE       equ     32                ; SHA3-256
MERKLE_MAX_DEPTH       equ     64                ; Suporta até 2^64 folhas

; ============================================================================
; Constantes BN128
; ============================================================================
BN128_P_LOW                equ     0xFEFFFFFC2F
BN128_R_LOW                equ     0xCD0364141
BN128_G1_GX            equ     1
BN128_G1_GY            equ     2
BN128_N                equ     1024              ; Dimensão do lattice Falcon

; ============================================================================
; Constantes de Endereçamento
; ============================================================================
ADDR_SIZE              equ     32               ; 256 bits
STATE_ROOT_SIZE        equ     32
MERKLE_ROOT_SIZE       equ     32

; ============================================================================
; Offsets de Estruturas
; ============================================================================
; TemporalMessage Layout (em bytes desde o início)
MSG_ID_OFFSET          equ     0
MSG_ID_LEN_OFFSET      equ     8
MSG_SENDER_OFFSET      equ     16               ; 32 bytes
MSG_RECEIVER_OFFSET    equ     48               ; 32 bytes
MSG_SRC_TS_OFFSET      equ     80               ; 8 bytes (int64)
MSG_TGT_TS_OFFSET      equ     88               ; 8 bytes (int64)
MSG_CONTENT_LEN_OFFSET equ     96               ; 4 bytes (uint32)
MSG_CONTENT_OFFSET     equ     104              ; variável
MSG_HASH_CACHE_OFFSET  equ     MSG_CONTENT_OFFSET + 2048 ; 32 bytes (cache)
MSG_ZK_PRESENT_OFFSET  equ     MSG_HASH_CACHE_OFFSET + 32
MSG_ZK_PROOF_LEN_OFFSET equ    MSG_ZK_PRESENT_OFFSET + 1
MSG_ZK_PROOF_OFFSET    equ     MSG_ZK_PROOF_LEN_OFFSET + 8

; TemporalBlock Layout
BLOCK_INDEX_OFFSET     equ     0               ; 8 bytes (uint64)
BLOCK_PREV_HASH_OFFSET equ     8               ; 32 bytes
BLOCK_TIMESTAMP_OFFSET equ     40              ; 8 bytes
BLOCK_MSG_COUNT_OFFSET equ     48              ; 4 bytes
BLOCK_MSGS_OFFSET      equ     56              ; ponteiro para array
BLOCK_STATE_ROOT_OFFSET equ    64              ; 32 bytes
BLOCK_ORACLE_ROOT_OFFSET equ   96              ; 32 bytes
BLOCK_SIZE              equ    128

; ConsistencyReport Layout
CR_SCORE_OFFSET        equ     0               ; 8 bytes (double)
CR_PRUNED_OFFSET       equ     8               ; 4 bytes (int32)
CR_CHECKS_OFFSET       equ     16              ; array

; Fibonacci Heap Node Layout
FHN_KEY_OFFSET         equ     0
FHN_VALUE_OFFSET       equ     8               ; double
FHN_PARENT_OFFSET      equ     16              ; ponteiro
FHN_CHILD_OFFSET       equ     24              ; ponteiro
FHN_LEFT_OFFSET        equ     32              ; ponteiro
FHN_RIGHT_OFFSET       equ     40              ; ponteiro
FHN_DEGREE_OFFSET      equ     48              ; int
FHN_MARK_OFFSET        equ     52              ; bool (1 byte)
FHN_EXPIRED_OFFSET     equ     53              ; bool (1 byte)
FHN_SIZE               equ     56              ; com padding

ARKHE_CTX_SIZE         equ     1024
ARKHE_CTX_MERKLE_OFFSET equ    0
ARKHE_CTX_HEAP_OFFSET   equ    8
ARKHE_CTX_ORACLE_OFFSET equ    16
ARKHE_CTX_ROOT_KEY_OFFSET equ  24
ARKHE_CTX_MSG_COUNT     equ    56
ARKHE_CTX_BLOCK_COUNT   equ    64
ARKHE_CTX_EPOCH         equ    72
ARKHE_CTX_ORACLE_THRESHOLD equ 80
ARKHE_CTX_TRUSTED_KEYS  equ    84
ARKHE_CTX_LAST_INDEX    equ    100
ARKHE_CTX_LAST_HASH     equ    108
ARKHE_CTX_LAST_TIMESTAMP equ   140

CTX_LAST_TS             equ    0
CTX_FUTURE_MSGS         equ    8
CTX_FUTURE_COUNT        equ    16

MR_SHARDS_OFFSET        equ    0
MR_ASSIGNMENTS_OFFSET   equ    8
MR_BORDER_OFFSET        equ    16
MR_NUM_SHARDS           equ    24
MR_TOTAL_NODES          equ    32
AN_NAME_OFFSET          equ    0
AN_IS_BORDER            equ    8

FIXED_TOP               equ    0

; ============================================================================
; Registradores Convenção (System V AMD64 ABI)
; ============================================================================
; rdi, rsi, rdx, rcx, r8, r9 — argumentos inteiros
; xmm0, xmm1 — argumentos float/double
; rax — retorno
; rbx, rbp, r12-r15 — callee-saved
; r10, r11 — caller-saved temporários
; rsp — stack pointer
; rbp — frame pointer
; ============================================================================

; ============================================================================
; Macros
; ============================================================================

; Macro para prologo de função (frame padrão)
%macro FUNC_PROLOGUE 0
    push    rbp
    mov     rbp, rsp
    push    rbx
    push    r12
    push    r13
    push    r14
    push    r15
    sub     rsp, 8                      ; alinhar stack a 16 bytes
%endmacro

; Macro para epilogo de função
%macro FUNC_EPILOGUE 0
    add     rsp, 8
    pop     r15
    pop     r14
    pop     r13
    pop     r12
    pop     rbx
    leave
    ret
%endmacro

; Macro para syscalls
%macro SYSCALL 1
    mov     rax, %1
    syscall
%endmacro

; Macro para fixed-point multiply (Q32.32 × Q32.32 → Q32.32)
; rdhi:rdlo = a * b, resultado em rdlo (parte fracionária)
%macro FP_MUL 3
    ; %1 = dest, %2 = a, %3 = b
    mov     rax, %2
    imul    rax, %3
    ; resultado em rdx:rax, parte fracionária é em rax
    ; (os 32 bits inferiores de rdx contêm a parte alta fracionária)
    ; Para Q32.32, tomamos rdx como resultado
    mov     %1, rdx
%endmacro

; Macro para ler timestamp (RDTSC)
%macro RDTSC 0
    lfence
    rdtscp
    shl     rdx, 32
    or      rax, rdx
%endmacro

; Macro para memory barrier
%macro MEMBAR 0
    mfence
%endmacro

; Macro para constante PI em Q32.32
%define FIXED_ONE    0x100000000
%define FIXED_HALF   0x80000000
%define PI_Q32       0x3243F6A88         ; π × 2^32

; ============================================================================
; Seção de código principal
; ============================================================================
section .text
    global arkhe_init
    global arkhe_process_message
    global arkhe_validate_block
    global arkhe_dijkstra_route
    global arkhe_merkle_root
    global arkhe_bn128_pairing
    global arkhe_falcon_verify
    global arkhe_consistency_evaluate
    global arkhe_hash_message
    global arkhe_fibonacci_heap_insert
    global arkhe_fibonacci_heap_extract_min
    global arkhe_fibonacci_heap_decrease_key
