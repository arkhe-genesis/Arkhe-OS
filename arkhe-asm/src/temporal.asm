; ============================================================================
; ARKHE Ω-TEMP — Tipos Temporais (Mensagens e Blocos)
; ============================================================================

%include "arkhe.inc"

extern keccak256

section .text

; ============================================================================
; Criar uma mensagem temporal
; ============================================================================
; Entrada:
;   rdi — ponteiro para buffer de saída (mínimo 1024 bytes)
;   rsi — string ID
;   rdx — comprimento do ID
;   rcx — string conteúdo
;   r8  — comprimento do conteúdo
;   r9  — sender address (32 bytes)
;   [rsp+48] — receiver address (32 bytes)
;   [rsp+56] — source timestamp (int64)
;   [rsp+64] — target timestamp (int64)
; Saída:
;   rax — tamanho total da mensagem
; ============================================================================
temporal_message_create:
    FUNC_PROLOGUE

    ; Salvar parâmetros adicionais
    mov     r10, [rsp + 48 + 16]         ; receiver address
    mov     r11, [rsp + 56 + 16]         ; source timestamp
    mov     r12, [rsp + 64 + 16]         ; target timestamp

    ; Copiar ID
    mov     [rdi + MSG_ID_OFFSET], rdx   ; comprimento do ID
    ; mov     rsi_backup, rsi
    ; mov     rdx_backup, rdx
    lea     rsi, [rdi + MSG_ID_OFFSET + 8]
    ; TODO: copiar bytes do ID

    ; Copiar sender
    lea     rdi, [rdi + MSG_SENDER_OFFSET]
    mov     rcx, 32 / 8
    rep movsq

    ; Copiar receiver
    mov     rdi, r10
    ; ... (contínuo)

    ; Definir timestamps
    mov     rax, r11
    mov     [rdi + MSG_SRC_TS_OFFSET], rax
    mov     rax, r12
    mov     [rdi + MSG_TGT_TS_OFFSET], rax

    ; Calcular hash
    lea     rdi, [rdi]                   ; início da mensagem
    lea     rsi, [rsp - 64]              ; buffer para hash
    mov     rdx, MSG_CONTENT_OFFSET      ; até o conteúdo (tamanho fixo)
    call    keccak256

    ; Guardar hash cache
    ; ...

    xor     eax, eax
    FUNC_EPILOGUE

; ============================================================================
; Validar ordem temporal de uma mensagem
; ============================================================================
; Retorna: 1 se válida, 0 se inválida
; ============================================================================
temporal_message_validate_temporal:
    ; rdi = ponteiro para mensagem

    mov     rax, [rdi + MSG_SRC_TS_OFFSET]
    mov     rbx, [rdi + MSG_TGT_TS_OFFSET]

    ; source_timestamp deve ser <= target_timestamp
    cmp     rax, rbx
    jg      .temporal_invalid

    ; target_timestamp não pode ser mais que 1000 blocos no futuro
    mov     rbx, BLOCK_INTERVAL_NSEC
    imul    rbx, 1000
    add     rax, rbx
    cmp     [rdi + MSG_TGT_TS_OFFSET], rax
    ja      .temporal_invalid

    mov     eax, 1
    ret

.temporal_invalid:
    xor     eax, eax
    ret

; ============================================================================
; Comparar duas mensagens temporalmente
; Retorna: -1 se a < b, 0 se a == b, 1 se a > b
; ============================================================================
temporal_message_compare:
    ; rdi = msg_a, rsi = msg_b

    mov     rax, [rdi + MSG_SRC_TS_OFFSET]
    mov     rbx, [rsi + MSG_SRC_TS_OFFSET]

    cmp     rax, rbx
    jb      .msg_a_earlier
    ja      .msg_a_later

    ; Timestamps iguais — comparar por ID
    ; ...

.msg_a_earlier:
    mov     eax, -1
    ret
.msg_a_later:
    mov     eax, 1
    ret
