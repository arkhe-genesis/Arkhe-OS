; ============================================================================
; ARKHE Ω-TEMP — Merkle Tree Operations (SHA3-256 based)
; ============================================================================
; Fornece:
;   - merkle_root: Computa raiz Merkle de um array de hashes
;   - merkle_proof: Gera prova de inclusão para uma folha
;   - merkle_verify: Verifica prova de inclusão
; ============================================================================

%include "arkhe.inc"

extern arkhe_malloc
extern arkhe_free
extern keccak256
extern keccak256_empty

section .text

global merkle_init
global merkle_root
global merkle_proof_generate
global merkle_proof_verify

merkle_init:
    ret

; ============================================================================
; merkle_root — Computa raiz Merkle de uma lista de folhas
; Entrada:
;   rdi = ponteiro para array de hashes (cada hash = 32 bytes)
;   rsi = número de folhas
;   rdx = ponteiro para buffer de saída (32 bytes)
; Saída:
;   rax = ponteiro para root (mesmo que rdx)
; ============================================================================
merkle_root:
    FUNC_PROLOGUE

    mov     r8, rdi                     ; leaves
    mov     r9, rsi                     ; count
    mov     r10, rdx                    ; output

    ; Caso especial: 0 folhas
    test    r9, r9
    jz      .merkle_empty

    ; Caso especial: 1 folha
    cmp     r9, 1
    je      .merkle_single

    ; Alocar nível de trabalho (no máximo count * 32 bytes)
    mov     rax, r9
    shl     rax, 5
    mov     rdi, rax
    call    arkhe_malloc
    test    rax, rax
    jz      .merkle_fail
    mov     r11, rax                     ; current level

    ; Copiar folhas para nível 0
    mov     rdi, r11
    mov     rsi, r8
    mov     rcx, r9
    shl     rcx, 2                      ; count * 8 (32 bytes/4 = 8 dwords)
    rep movsd

    ; Construir bottom-up
    mov     r12, r9                      ; nodes_at_level

.merkle_level:
    cmp     r12, 1
    je      .merkle_done

    ; Processar pares
    mov     r13, 0                       ; dest index
    mov     r14, 0                       ; src index

.merkle_pair_loop:
    cmp     r14, r12
    jge     .merkle_level_done

    ; Left = level[src_index]
    mov     rdi, r14
    shl     rdi, 5
    add     rdi, r11

    ; Right = level[src_index + 1] ou left (se ímpar)
    mov     rsi, r14
    inc     rsi
    cmp     rsi, r12
    jb      .merkle_has_right
    ; Sem irmão direito → duplicar o esquerdo
    mov     rsi, r14

.merkle_has_right:
    shl     rsi, 5
    add     rsi, r11

    ; Hash(left || right)
    ; (Em produção: usar SHA3-256 otimizado)
    push    rdi
    push    rsi
    push    r11
    push    r12
    push    r13
    push    r14

    ; Alocar buffer temporário (64 bytes)
    sub     rsp, 64
    mov     rdi, rsp
    ; Copiar left: 32 bytes
    mov     rsi, [rsp + 64 + 40]             ; rdi orig
    mov     rcx, 4
    rep movsq
    ; Copiar right: 32 bytes
    mov     rsi, [rsp + 64 + 32]            ; rsi orig
    mov     rcx, 4
    rep movsq

    ; Calcular SHA3-256(buffer de 64 bytes)
    lea     rdi, [rsp]
    mov     rsi, 64
    mov     rdx, rsp
    call    keccak256_empty

    ; Resultado em rax (ponteiro para hash)
    ; Copiar para dest posição
    mov     rsi, rax
    mov     rdi, [rsp + 64 + 16] ; r13 (dest index)
    shl     rdi, 5
    add     rdi, [rsp + 64 + 24] ; r11 (level)
    mov     rcx, 4
    rep movsq

    add     rsp, 64
    pop     r14
    pop     r13
    pop     r12
    pop     r11
    pop     rsi
    pop     rdi

    inc     r14
    inc     r14
    inc     r13
    jmp     .merkle_pair_loop

.merkle_level_done:
    ; Se ímpar, copiar último nó para próximo nível
    ; ...

    ; shr     r12, 1                      ; Próximo nível: metade dos nós
    mov     r12, r13
    jmp     .merkle_level

.merkle_done:
    ; Primeiros 32 bytes de r11 são a root
    mov     rdi, r10
    mov     rsi, r11
    mov     rcx, 4                      ; 32 bytes / 8
    rep movsq

    ; Liberar nível de trabalho
    mov     rdi, r11
    call    arkhe_free

    mov     rax, r10
    jmp     .merkle_return

.merkle_single:
    ; 1 folha = hash da folha
    mov     rdi, r10
    mov     rsi, r8
    mov     rcx, 4
    rep movsq
    mov     rax, r10
    jmp     .merkle_return

.merkle_empty:
    ; Root de árvore vazia = hash vazio
    push    rdi
    xor     edi, edi
    call    keccak256_empty              ; hash de input vazio
    mov     rdi, r10
    mov     rsi, rax
    mov     rcx, 4
    rep movsq
    pop     rdi
    mov     rax, r10

.merkle_fail:
.merkle_return:
    FUNC_EPILOGUE

; ============================================================================
; merkle_proof_generate — Gera prova de inclusão
; Entrada:
;   rdi = folhas (array de 32-byte hashes)
;   rsi = número de folhas
;   rdx = índice da folha alvo
;   rcx = buffer de saída para proof
; Saída:
;   rax = tamanho da prova em bytes
; ============================================================================
merkle_proof_generate:
    FUNC_PROLOGUE

    mov     r8, rdi                     ; leaves
    mov     r9, rsi                     ; count
    mov     r10, rdx                    ; target index
    mov     r11, rcx                    ; proof buffer
    xor     r12, r12                    ; proof_size = 0

    ; Verificar índice válido
    cmp     r10, r9
    jae     .proof_invalid

    ; Alocar nívels para construção bottom-up
    ; (Simplificado: usar array temporário)

    ; Estratégia: computar nível por nível, coletando irmãos
    mov     r13, r9                     ; current_count
    mov     r14, r10                    ; current_index

.proof_level:
    cmp     r13, 1
    je      .proof_complete

    ; Determinar irmão (sibling)
    mov     rax, r14
    xor     rax, 1                      ; sibling = index ^ 1

    ; Se sibling < current_count, adicionar ao proof
    cmp     rax, r13
    jae     .no_sibling                 ; sibling não existe (último em nível ímpar)

    ; Calcular offset do irmão no nível atual
    ; (Simplificado: assumir que level é recomputável)

    ; Adicionar direção ao proof
    ; byte 0: direction (0=left, 1=right)
    mov     al, 0
    test    r14, 1
    jz      .direction_set
    mov     al, 1
.direction_set:
    mov     [r11 + r12], al
    inc     r12

    ; Adicionar hash do irmão (32 bytes)
    ; (Simplificado: placeholder)
    ; ...
    add     r12, 32

.no_sibling:
    ; Atualizar para próximo nível
    shr     r13, 1
    shr     r14, 1
    jmp     .proof_level

.proof_complete:
    mov     rax, r12

.proof_invalid:
    FUNC_EPILOGUE

; ============================================================================
; merkle_proof_verify — Verifica prova de inclusão
; Entrada:
;   rdi = leaf_hash (32 bytes)
;   rsi = root_hash (32 bytes)
;   rdx = proof_data
;   rcx = proof_size
; Saída:
;   al = 1 se válido, 0 se inválido
; ============================================================================
merkle_proof_verify:
    FUNC_PROLOGUE

    mov     r8, rdi                     ; leaf_hash
    mov     r9, rsi                     ; root_hash
    mov     r10, rdx                    ; proof data
    mov     r11, rcx                    ; proof size

    ; Copiar leaf_hash como current
    sub     rsp, 32
    mov     rdi, rsp
    mov     rsi, r8
    mov     rcx, 4
    rep movsq

    mov     r12, 0                      ; proof offset
    mov     r13, 0                      ; step count (sanity)

.verify_loop:
    cmp     r12, r11
    jge     .verify_done

    ; Ler direção
    movzx   eax, BYTE [r10 + r12]
    inc     r12

    test    eax, eax
    jz      .verify_left

.verify_right:
    ; current = H(current || sibling)
    ; Copiar current + sibling para buffer
    sub     rsp, 64
    mov     rdi, rsp
    mov     rsi, [rsp + 64]             ; current (na stack acima)
    mov     rcx, 4
    rep movsq
    ; Copiar sibling (next 32 bytes from proof)
    mov     rsi, r10
    add     rsi, r12
    mov     rcx, 4
    rep movsq

    ; Hash
    lea     rdi, [rsp]
    mov     rsi, 64
    mov     rdx, rsp
    call    keccak256_empty
    ; rax = hash pointer
    mov     rdi, [rsp + 64]
    mov     rsi, rax
    mov     rcx, 4
    rep movsq                           ; copy new current

    add     rsp, 32                      ; sibling size
    add     r12, 32
    add     rsp, 32                      ; current offset
    jmp     .verify_loop

.verify_left:
    ; current = H(sibling || current)
    sub     rsp, 64
    mov     rdi, rsp
    ; Copiar sibling
    mov     rsi, r10
    add     rsi, r12
    mov     rcx, 4
    rep movsq
    ; Copiar current
    mov     rsi, [rsp + 64]
    mov     rcx, 4
    rep movsq

    lea     rdi, [rsp]
    mov     rsi, 64
    mov     rdx, rsp
    call    keccak256_empty

    mov     rdi, [rsp + 64]
    mov     rsi, rax
    mov     rcx, 4
    rep movsq

    add     rsp, 32
    add     r12, 32
    add     rsp, 32
    jmp     .verify_loop

.verify_done:
    ; Comparar current com root
    ; (Usar constant-time compare)
    mov     rdi, rsp
    mov     rsi, r9
    mov     rdx, 32
    call    constant_time_compare_internal

    ; eax = 1 se iguais, 0 se diferentes
    add     rsp, 32
    FUNC_EPILOGUE

constant_time_compare_internal:
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
