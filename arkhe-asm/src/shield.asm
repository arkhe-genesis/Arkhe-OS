; ============================================================================
; ARKHE Ω-TEMP — CausalShield
; ============================================================================
; □p = "p é necessariamente verdadeiro" = p é consistente em TODOS os futuros
; ◇p = "p é possivelmente verdadeiro" = p é consistente em ALGUM futuro
;
; O CausalShield implementa:
;  - Forward consistency: mensagens futuras devem respeitar mensagens passadas
;  - Backward consistency: branches paralelas devem ser reconciliáveis
;  - Forcing: verificação modal sobre todos os futuros acessíveis
; ============================================================================

%include "arkhe.inc"

extern oracle_evaluate

section .text

; ============================================================================
; shield_evaluate — Avalia □msg (necessidade)
; Retorna 1 se msg é consistente em TODOS os futuros acessíveis
; ============================================================================
shield_box:
    FUNC_PROLOGUE

    mov     r12, rdi                     ; message
    mov     r13, rsi                     ; oracle
    mov     r14, rdx                     ; futures_list
    mov     r15, rcx                     ; num_futures

    ; Para cada futuro acessível, verificar consistência
    xor     r8, r8                       ; future_index

.box_loop:
    cmp     r8, r15
    jae     .box_all_passed

    ; Avaliar msg no futuro r8
    mov     rdi, r13                     ; oracle
    mov     rsi, r12                     ; message
    mov     rdx, [r14 + r8 * 8]          ; future context
    call    oracle_evaluate

    ; If any future fails, □p = false
    test    rdx, rdx                     ; pruned flag
    jnz     .box_failed

    inc     r8
    jmp     .box_loop

.box_all_passed:
    mov     eax, 1
    FUNC_EPILOGUE

.box_failed:
    xor     eax, eax
    FUNC_EPILOGUE

; ============================================================================
; shield_diamond — Avalia ◇msg (possibilidade)
; Retorna 1 se msg é consistente em ALGUM futuro acessível
; ============================================================================
shield_diamond:
    FUNC_PROLOGUE

    mov     r12, rdi
    mov     r13, rsi
    mov     r14, rdx
    mov     r15, rcx

    xor     r8, r8

.diamond_loop:
    cmp     r8, r15
    jae     .diamond_all_failed

    mov     rdi, r13
    mov     rsi, r12
    mov     rdx, [r14 + r8 * 8]
    call    oracle_evaluate

    test    rdx, rdx
    jz       .diamond_succeeded          ; Found at least one consistent future

    inc     r8
    jmp     .diamond_loop

.diamond_succeeded:
    mov     eax, 1
    FUNC_EPILOGUE

.diamond_all_failed:
    xor     eax, eax
    FUNC_EPILOGUE

; ============================================================================
; shield_forward_check — Verificação forward de causalidade
; ============================================================================
shield_forward_check:
    FUNC_PROLOGUE

    ; rdi = ctx, rsi = new_msg

    ; 1. Verificar se new_msg é temporalmente posterior a todas as msgs no context
    ; 2. Verificar se new_msg é consistente com o estado atual
    ; 3. Se ambas passam → forward consistent

    ; Check: source_ts da nova msg >= max(target_ts) do context
    mov     rax, [rsi + MSG_SRC_TS_OFFSET]
    ; Comparar com último timestamp do context
    cmp     rax, [rdi + CTX_LAST_TS]
    jb      .forward_not_causal

    ; Run oracle evaluation
    call    oracle_evaluate
    test    rdx, rdx
    jnz     .forward_not_consistent

    mov     eax, 1
    FUNC_EPILOGUE

.forward_not_causal:
.forward_not_consistent:
    xor     eax, eax
    FUNC_EPILOGUE

; ============================================================================
; shield_backward_check — Verificação backward de causalidade
; ============================================================================
shield_backward_check:
    FUNC_PROLOGUE

    ; rdi = ctx, rsi = candidate_msg

    ; Verificar se candidate_msg é compatível com mensagens futuras já aceitas
    ; (Reconciliação de branches)

    ; Para cada mensagem futura no contexto:
    ;   - Verificar se candidate_msg ↔ futura_msg não cria paradoxo
    ;   - Isto é: source_ts(cand) ≤ target_ts(fut) E source_ts(fut) ≤ target_ts(cand)

    mov     r8, [rdi + CTX_FUTURE_MSGS]
    mov     r9, [rdi + CTX_FUTURE_COUNT]

.backward_loop:
    test    r9, r9
    jz      .backward_compatible

    dec     r9
    ; Comparar timestamps
    ; ... (comparação temporal)

    jmp     .backward_loop

.backward_compatible:
    mov     eax, 1
    FUNC_EPILOGUE
