; ============================================================================
; ARKHE Ω-TEMP — Entry Point e Dispatcher
; ============================================================================
; Este é o coração em silício puro do ARKHE.
; Recebe mensagens temporais e as processa através de toda a cadeia:
;   hash → oracle → roteamento → consensus
; ============================================================================

%include "arkhe.inc"

extern arkhe_malloc
extern arkhe_free
extern arkhe_zk_verify
extern keccak256
extern keccak256_empty
extern oracle_evaluate
extern merkle_root
extern merkle_init
extern fibonacci_heap_create
extern oracle_init
extern falcon_verify_batch
extern get_current_timestamp

section .text

; ============================================================================
; arkhe_init — Inicializa o sistema ARKHE
; ============================================================================
; Entrada:
;   rdi — ponteiro para configuração (arkhe_config_t)
;   rsi — número de nós iniciais
;   rdx — seed para geração de chaves (32 bytes)
; Saída:
;   rax — handle do contexto ARKHE (ou 0 em erro)
; ============================================================================
arkhe_init:
    FUNC_PROLOGUE

    ; Salvar parâmetros
    mov     r12, rdi                     ; config
    mov     r13, rsi                     ; num_nodes
    mov     r14, rdx                     ; seed

    ; Verificar parâmetros
    test    rdi, rdi
    jz      init_error
    test    rsi, rsi
    jz      init_error

    ; Alocar contexto ARKHE
    mov     rdi, ARKHE_CTX_SIZE
    call    arkhe_malloc
    test    rax, rax
    jz      init_error
    mov     r15, rax                     ; ctx = rax

    ; Inicializar hash chain (genesis block)
    mov     rdi, rax
    call    init_genesis_block
    test    rax, rax
    jz      init_error_free_ctx

    ; Inicializar Merkle tree vazia
    mov     rdi, [r15 + ARKHE_CTX_MERKLE_OFFSET]
    call    merkle_init

    ; Inicializar Fibonacci heap de roteamento
    lea     rdi, [r15 + ARKHE_CTX_HEAP_OFFSET]
    call    fibonacci_heap_create

    ; Inicializar oracle de consistência
    lea     rdi, [r15 + ARKHE_CTX_ORACLE_OFFSET]
    lea     rsi, [r12]                    ; config thresholds
    call    oracle_init

    ; Derivar chaves criptográficas do seed
    ; (Simplificado: SHA3-256 do seed → root key)
    mov     rdi, r14                     ; seed
    mov     rsi, 32                      ; seed size
    lea     rdx, [r15 + ARKHE_CTX_ROOT_KEY_OFFSET]
    call    keccak256_empty

    ; Inicializar contadores
    mov     QWORD [r15 + ARKHE_CTX_MSG_COUNT], 0
    mov     QWORD [r15 + ARKHE_CTX_BLOCK_COUNT], 0
    mov     QWORD [r15 + ARKHE_CTX_EPOCH], 0

    ; Retornar handle
    mov     rax, r15
    jmp     init_done

init_error:
.init_error:
    xor     eax, eax
    jmp     init_done

init_error_free_ctx:
    mov     rdi, rax
    call    arkhe_free
    xor     eax, eax

init_done:
    FUNC_EPILOGUE

; ============================================================================
; arkhe_process_message — Processa uma mensagem temporal
; ============================================================================
; Entrada:
;   rdi — handle do contexto ARKHE
;   rsi — ponteiro para a mensagem (serializada)
;   rdx — tamanho da mensagem
; Saída:
;   rax — 0 se aceita, -1 se rejeitada (ver rcx para razão)
;   rcx — motivo da rejeição (0 = sucesso)
; ============================================================================
arkhe_process_message:
    FUNC_PROLOGUE

    ; r12 = ctx, r13 = msg_ptr, r14 = msg_len
    mov     r12, rdi
    mov     r13, rsi
    mov     r14, rdx

    ; ──────────────── PASSO 1: Hash da mensagem ────────────────
    ; Calcular SHA3-256 da mensagem
    lea     rdi, [rsp - 64]              ; buffer para hash (red zone)
    and     rsp, -16                     ; alinhar stack
    mov     rsi, r13                     ; mensagem
    mov     rdx, r14                     ; tamanho
    call    keccak256_empty
    mov     r8, rax                      ; msg_hash

    ; ──────────────── PASSO 2: Verificar duplicata (loop detection) ────────────────
    ; Usar bloom filter (simulação)
    mov     rdi, r12
    mov     rsi, r8
    call    check_duplicate
    test    al, al
    jnz     .reject_loop

    ; ──────────────── PASSO 3: Hashing temporal ────────────────
    ; Extrair timestamps e verificar ordem temporal
    mov     rax, [r13 + MSG_SRC_TS_OFFSET]
    mov     rbx, [r13 + MSG_TGT_TS_OFFSET]
    cmp     rax, rbx
    jg      .reject_paradox              ; source > target = paradoxo temporal

    ; Verificar se timestamp é futuro (relativo ao epoch atual)
    call    get_current_timestamp
    cmp     rax, [r13 + MSG_TGT_TS_OFFSET]
    jg      .reject_expired              ; mensagem expirou

    ; ──────────────── PASSO 4: Consistência via Oracle ────────────────
    mov     rdi, r12
    mov     rsi, r13
    call    oracle_evaluate

    ; rax contém o score (Q32.32 fixed point)
    ; Verificar se score >= threshold
    cmp     eax, DWORD [r12 + ARKHE_CTX_ORACLE_THRESHOLD]
    jb      .reject_inconsistent

    ; ──────────────── PASSO 5: Verificação ZK (se presente) ────────────────
    ; Verificar se há prova ZK anexada
    mov     al, [r13 + MSG_ZK_PRESENT_OFFSET]
    test    al, al
    jz      .skip_zk_check

    lea     rdi, [r13 + MSG_ZK_PROOF_OFFSET]
    lea     rsi, [rsp - 64]              ; msg_hash
    mov     rdx, [r13 + MSG_ZK_PROOF_LEN_OFFSET]
    call    arkhe_zk_verify
    test    al, al
    jz      .reject_zk_invalid

.skip_zk_check:
    ; ──────────────── PASSO 6: Verificação de assinatura ────────────────
    mov     rdi, r13
    lea     rsi, [r12 + ARKHE_CTX_TRUSTED_KEYS]
    call    falcon_verify_batch
    test    al, al
    jz      .reject_bad_sig

    ; ──────────────── PASSO 7: Aceitar mensagem ────────────────
    ; Marcar como duplicata
    mov     rdi, r12
    mov     rsi, r8
    call     mark_seen

    ; Inserir no buffer de mensagens do bloco atual
    mov     rdi, r12
    mov     rsi, r13
    mov     rdx, r14
    call    insert_message

    xor     eax, eax                    ; sucesso
    xor     ecx, ecx                    ; razão: nenhuma
    jmp     .process_done

.reject_loop:
    mov     eax, -1
    mov     ecx, 1                       ; REASON_LOOP
    jmp     .process_done

.reject_paradox:
    mov     eax, -1
    mov     ecx, 2                       ; REASON_PARADOX
    jmp     .process_done

.reject_expired:
    mov     eax, -1
    mov     ecx, 3                       ; REASON_EXPIRED
    jmp     .process_done

.reject_inconsistent:
    mov     eax, -1
    mov     ecx, 4                       ; REASON_INCONSISTENT
    jmp     .process_done

.reject_zk_invalid:
    mov     eax, -1
    mov     ecx, 5                       ; REASON_ZK_INVALID
    jmp     .process_done

.reject_bad_sig:
    mov     eax, -1
    mov     ecx, 6                       ; REASON_BAD_SIGNATURE

.process_done:
    MEMBAR
    FUNC_EPILOGUE

; ============================================================================
; arkhe_validate_block — Valida um bloco temporal completo
; ============================================================================
; Entrada:
;   rdi — handle do contexto ARKHE
;   rsi — ponteiro para o bloco
;   rdx — tamanho do bloco
; Saída:
;   rax — 0 se válido, -1 se inválido
;   r8  — Merkle root calculado (se válido)
; ============================================================================
arkhe_validate_block:
    FUNC_PROLOGUE

    mov     r12, rdi                     ; ctx
    mov     r13, rsi                     ; block
    mov     r14, rdx                     ; size

    ; Verificar tamanho mínimo
    cmp     r14, BLOCK_SIZE
    jb      .invalid_block

    ; Extrair campos do bloco
    mov     r8,  [r13 + BLOCK_INDEX_OFFSET]       ; index
    mov     r9,  [r13 + BLOCK_PREV_HASH_OFFSET]   ; prev_hash (32 bytes)
    mov     r10, [r13 + BLOCK_TIMESTAMP_OFFSET]    ; timestamp
    mov     r11d, [r13 + BLOCK_MSG_COUNT_OFFSET]   ; msg_count

    ; ──────────────── PASSO 1: Verificar índice ────────────────
    ; O índice deve ser = último índice + 1
    cmp     r8, [r12 + ARKHE_CTX_LAST_INDEX]
    jne     .invalid_block

    ; ──────────────── PASSO 2: Verificar prev_hash ────────────────
    ; Comparar com o hash do bloco anterior
    ; (Em produção: carregar do storage)
    lea     rdi, [r12 + ARKHE_CTX_LAST_HASH]
    mov     rsi, r9
    mov     rdx, 32
    call    .constant_time_compare
    test    al, al
    jz      .invalid_block

    ; ──────────────── PASSO 3: Verificar timestamp ────────────────
    ; Deve ser > timestamp do bloco anterior
    cmp     r10, [r12 + ARKHE_CTX_LAST_TIMESTAMP]
    jbe     .invalid_block

    ; ──────────────── PASSO 4: Verificar mensagens ────────────────
    ; Iterar sobre cada mensagem e avaliar o oracle
    lea     rdi, [r13 + BLOCK_MSGS_OFFSET]
    mov     rcx, r11                      ; contador

.validate_messages_loop:
    test    rcx, rcx
    jz      .messages_validated

    push    rcx
    push    rdi
    push    r12
    call    oracle_evaluate
    pop     r12
    pop     rdi
    pop     rcx

    ; Verificar se mensagem é consistente
    ; (oracle_evaluate retorna score em rax)
    cmp     eax, DWORD [r12 + ARKHE_CTX_ORACLE_THRESHOLD]
    jb      .invalid_block

    dec     rcx
    jmp     .validate_messages_loop

.messages_validated:
    ; ──────────────── PASSO 5: Calcular Merkle root ────────────────
    lea     rdi, [r13 + BLOCK_MSGS_OFFSET]
    mov     rsi, r11                      ; número de mensagens
    lea     rdx, [rsp - 64]              ; buffer para root
    call    merkle_root

    ; ──────────────── PASSO 6: Comparar Merkle root ────────────────
    lea     rdi, [rsp - 64]              ; root calculado
    lea     rsi, [r13 + BLOCK_STATE_ROOT_OFFSET]
    mov     rdx, 32
    call    .constant_time_compare
    test    al, al
    jz      .invalid_block

    ; Sucesso!
    ; r8 já contém o Merkle root (calculado no passo 5)
    xor     eax, eax
    jmp     .validate_done

.invalid_block:
    mov     eax, -1

.validate_done:
    MEMBAR
    FUNC_EPILOGUE

; ============================================================================
; Constant-time memory comparison
; ============================================================================
; Compara dois blocos de memória em tempo constante para evitar timing attacks
; Entrada: rdi = ptr1, rsi = ptr2, rdx = len
; Saída: al = 0 se iguais, 1 se diferentes
; ============================================================================
.constant_time_compare:
    xor     eax, eax
    xor     ecx, ecx
    test    rdx, rdx
    jz      .ct_compare_done

.ct_compare_loop:
    movzx   r8d, BYTE [rdi + rcx]
    movzx   r9d, BYTE [rsi + rcx]
    xor     r8d, r9d
    or      eax, r8d
    inc     rcx
    cmp     rcx, rdx
    jb      .ct_compare_loop

    ; Converter eax para 0 ou 1
    neg     eax
    sbb     eax, eax
    and     eax, 1

.ct_compare_done:
    ret

; ============================================================================
; Inicializar bloco gênesis
; ============================================================================
init_genesis_block:
    ; Criar bloco gênesis com estado inicial
    mov     rdi, BLOCK_SIZE
    call    arkhe_malloc
    test    rax, rax
    jz      init_error

    ; index = 0
    mov     QWORD [rax + BLOCK_INDEX_OFFSET], 0

    ; prev_hash = zeros (não tem predecessor)
    lea     rdi, [rax + BLOCK_PREV_HASH_OFFSET]
    mov     rcx, 4                      ; 32 bytes / 8
    xor     eax, eax
    rep stosq

    ; timestamp = launch time (passado em r13)
    mov     rax, [r13]
    mov     QWORD [rax + BLOCK_TIMESTAMP_OFFSET], rax

    ; msg_count = 0
    mov     DWORD [rax + BLOCK_MSG_COUNT_OFFSET], 0

    ; state_root = hash("ARKHE_GENESIS")
    ; (pré-computado)
    mov     rdi, rax
    call    compute_state_root

    ret

; ============================================================================
; Dummy stubs
; ============================================================================
check_duplicate:
    xor al, al
    ret
mark_seen:
    ret
insert_message:
    ret
compute_state_root:
    ret

; ============================================================================
; Helper: Obter timestamp atual (nanossegundos)
; ============================================================================
; get_current_timestamp implemented in syscall.asm

; ============================================================================
; Debug logging (via write syscall)
; ============================================================================
arkhe_debug_log:
    ; rdi = format string, rsi = args...
    ; Simplificado: apenas escreve string no stderr
    push    rbp
    mov     rbp, rsp
    push    rdi
    push    rsi

    ; calcular comprimento da string
    mov     rdi, [rbp + 16]             ; string
    xor     rcx, rcx
.strlen_loop:
    cmp     BYTE [rdi + rcx], 0
    je      .strlen_done
    inc     rcx
    jmp     .strlen_loop
.strlen_done:

    ; write(STDERR_FILENO, msg, len)
    mov     rax, 1                      ; sys_write
    mov     rdi, 2                      ; STDERR_FILENO
    mov     rsi, [rbp + 16]             ; string
    mov     rdx, rcx                    ; length
    syscall

    pop     rsi
    pop     rdi
    leave
    ret
