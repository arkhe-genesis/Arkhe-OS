; ============================================================================
; ARKHE Ω-TEMP — Fibonacci Heap
; ============================================================================
; Operações:
;   - Insert: O(1)
;   - Extract-Min: O(log n) amortizado
;   - Decrease-Key: O(1) amortizado
; Crítico para o desempenho do Dijkstra no roteador
; ============================================================================

%include "arkhe.inc"

extern arkhe_malloc

section .data
    ; Golden ratio constant for max degree
    phi_squared  dq 2.61803398874989484820   ; φ²

section .text

global fibonacci_heap_create
global fh_create
global fh_insert
global fh_extract_min
global fh_decrease_key

fibonacci_heap_create:
    jmp fh_create

; ============================================================================
; fh_create — Cria uma Fibonacci Heap vazia
; Saída: rax = ponteiro para a heap (ou 0 em erro)
; ============================================================================
fh_create:
    FUNC_PROLOGUE

    ; Alocar estrutura da heap
    mov     rdi, 64                         ; FH struct: min ptr + count + n
    call    arkhe_malloc
    test    rax, rax
    jz      .fh_create_fail

    ; Zerar estrutura
    mov     rdi, rax
    xor     eax, eax
    mov     rcx, 64 / 8
    rep stosq

    ; FH[0] = min pointer (null)
    ; FH[8] = n (number of nodes) (already 0)

    mov     rax, rdi
.fh_create_fail:
    FUNC_EPILOGUE

; ============================================================================
; fh_insert — Insere nó na heap
; Entrada:
;   rdi = ponteiro para heap
;   rsi = chave (int)
;   rdx = valor (double, em Q32.32)
;   rcx = expired flag
; Saída: rdi = ponteiro para nó inserido
; ============================================================================
fh_insert:
    FUNC_PROLOGUE

    mov     r8, rdi                     ; heap
    mov     r9, rsi                     ; key
    mov     r10, rdx                    ; value
    mov     r11, rcx                    ; expired

    ; Alocar nó
    mov     rdi, FHN_SIZE
    call    arkhe_malloc
    test    rax, rax
    jz      .insert_fail

    ; Inicializar nó
    mov     [rax + FHN_KEY_OFFSET], r9w
    mov     [rax + FHN_VALUE_OFFSET], r10
    mov     QWORD [rax + FHN_PARENT_OFFSET], 0
    mov     QWORD [rax + FHN_CHILD_OFFSET], 0
    mov     [rax + FHN_LEFT_OFFSET], rax      ; circular: aponta para si mesmo
    mov     [rax + FHN_RIGHT_OFFSET], rax
    mov     DWORD [rax + FHN_DEGREE_OFFSET], 0
    mov     BYTE [rax + FHN_MARK_OFFSET], 0
    mov     BYTE [rax + FHN_EXPIRED_OFFSET], r11b

    ; Adicionar à lista de raízes
    mov     rdx, [r8]                   ; min pointer
    test    rdx, rdx
    jz      .insert_first               ; Heap vazia

    ; Inserir na lista circular de raízes (antes do min)
    mov     rcx, [rdx + FHN_LEFT_OFFSET]
    mov     [rax + FHN_RIGHT_OFFSET], rdx
    mov     [rax + FHN_LEFT_OFFSET], rcx
    mov     [rcx + FHN_RIGHT_OFFSET], rax
    mov     [rdx + FHN_LEFT_OFFSET], rax

    ; Atualizar min se necessário
    movsd xmm0, [rax + FHN_VALUE_OFFSET]
    comisd xmm0, [rdx + FHN_VALUE_OFFSET]
    jae .insert_no_min_update
    mov     [r8], rax                   ; new min

.insert_no_min_update:
    jmp     .insert_update_count

.insert_first:
    mov     [r8], rax                   ; min = rax
    mov     [rax + FHN_LEFT_OFFSET], rax
    mov     [rax + FHN_RIGHT_OFFSET], rax

.insert_update_count:
    inc     QWORD [r8 + 8]             ; n++

    ; Retornar ponteiro para nó (para decrease-key)
    mov     rax, rax

.insert_fail:
    FUNC_EPILOGUE

; ============================================================================
; fh_extract_min — Remove e retorna o nó mínimo
; Entrada: rdi = ponteiro para heap
; Saída:
;   rax = key do nó mínimo
;   rdx = value do nó mínimo
;   rcx = expired flag
; ============================================================================
fh_extract_min:
    FUNC_PROLOGUE

    mov     r8, rdi                     ; heap
    mov     rdx, [r8]                   ; min node

    ; Verificar se heap está vazia
    test    rdx, rdx
    jz      .extract_empty

    ; Retornar valores
    mov     rax, [rdx + FHN_KEY_OFFSET]
    mov     r12, [rdx + FHN_VALUE_OFFSET]
    movzx   ecx, BYTE [rdx + FHN_EXPIRED_OFFSET]
    ; ecx = expired flag

    ; ─── Consolidação ───
    ; Adicionar filhos à lista de raízes
    mov     rsi, [rdx + FHN_CHILD_OFFSET]
    test    rsi, rsi
    jz      .no_children

    ; ... Adicionar todos os filhos à lista de raízes
    ; (Implementação completa: iterar pela lista circular de filhos)

.no_children:
    ; Remover min da lista de raízes
    mov     rsi, [rdx + FHN_LEFT_OFFSET]
    mov     rcx, [rdx + FHN_RIGHT_OFFSET]
    mov     [rsi + FHN_RIGHT_OFFSET], rcx
    mov     [rcx + FHN_LEFT_OFFSET], rsi

    ; Se era o único nó
    cmp     rdx, rcx
    je      .heap_empty_after

    ; Consolidação: mesclar árvores de mesmo grau
    call    fh_consolidate

    ; Encontrar novo mínimo
    call    fh_find_min

    dec     QWORD [r8 + 8]             ; n--
    mov     rdx, r12
    jmp     .extract_done

.extract_empty:
    xor     eax, eax
    xor     edx, edx
    xor     ecx, ecx
    jmp     .extract_done

.heap_empty_after:
    mov     QWORD [r8], 0               ; min = null
    dec     QWORD [r8 + 8]             ; n--
    mov     rdx, r12

.extract_done:
    FUNC_EPILOGUE

; ============================================================================
; fh_consolidate — Mesclar árvores de mesmo grau
; ============================================================================
fh_consolidate:
    FUNC_PROLOGUE

    ; Calcular D(n) = floor(log_φ(n)) + 1
    ; Usando a fórmula: D(n) = floor(log2(n) / log2(φ)) + 1
    mov     rax, [r8 + 8]               ; n
    ; Bit scan reverse para encontrar ⌊log2(n)⌋
    bsr     rcx, rax
    inc     rcx                          ; ⌊log2(n)⌋ + 1
    imul    rcx, 3                       ; × (1/log2(φ)) ≈ × 1.44, simplificado × 3

    ; Alocar array A[0..D]
    mov rdi, rsp
    sub rdi, rcx
    sub rdi, rcx
    sub rdi, rcx
    sub rdi, rcx
    sub rdi, rcx
    sub rdi, rcx
    sub rdi, rcx
    sub rdi, rcx
    sub rdi, 16
    and     rsp, -16
    push    rdi                          ; salvar ponteiro do array

    ; Zerar array
    xor     eax, eax
    mov     rdx, rcx
    rep stosq

    ; Iterar sobre raízes
    mov     rsi, [r8]                    ; min
    mov     r9, rsi                      ; current

.consolidate_loop:
    test    r9, r9
    jz      .consolidate_done

    ; x = current root node
    mov     r10, r9
    mov     r11, [r9 + FHN_RIGHT_OFFSET] ; próxima raiz

    ; d = x.degree
    movzx   eax, WORD [r10 + FHN_DEGREE_OFFSET]

    ; while A[d] != null:
.merge_loop:
    lea     rcx, [rsp - 16]
    lea     rcx, [rcx + rax * 8]
    cmp     QWORD [rcx], 0
    je      .store_no_merge

    ; y = A[d]
    mov     rdx, [rcx]

    ; if x.value > y.value: swap(x, y)
    movsd xmm0, [r10 + FHN_VALUE_OFFSET]
    comisd xmm0, [rdx + FHN_VALUE_OFFSET]
    jbe .no_swap
    xchg r10, rdx
.no_swap:
    ; link(y, x): tornar y filho de x
    call    fh_link

    ; A[d] = null
    mov     QWORD [rcx], 0

    ; d++
    inc     eax
    jmp     .merge_loop

.store_no_merge:
    ; A[d] = x
    lea     rcx, [rsp - 16]
    lea     rcx, [rcx + rax * 8]
    mov     [rcx], r10

    ; next root
    mov     r9, r11
    jmp     .consolidate_loop

.consolidate_done:
    ; Reconstruir lista de raízes a partir de A[]
    mov     QWORD [r8], 0               ; min = null

    ; Iterar sobre A e adicionar não-nulos à lista de raízes
    ; ...

    add     rsp, 16
    FUNC_EPILOGUE

; ============================================================================
; fh_link — Torna y filho de x (usado na consolidação)
; ============================================================================
fh_link:
    ; Remove y da lista de raízes
    mov     rax, [r11 + FHN_LEFT_OFFSET]
    mov     rcx, [r11 + FHN_RIGHT_OFFSET]
    mov     [rax + FHN_RIGHT_OFFSET], rcx
    mov     [rcx + FHN_LEFT_OFFSET], rax

    ; Adicionar y à lista de filhos de x
    mov     rax, [r10 + FHN_CHILD_OFFSET]
    test    rax, rax
    jnz     .link_add_child
    ; y é o primeiro filho
    mov     [r10 + FHN_CHILD_OFFSET], r11
    mov     [r11 + FHN_LEFT_OFFSET], r11
    mov     [r11 + FHN_RIGHT_OFFSET], r11
    jmp     .link_done_child

.link_add_child:
    ; Inserir y na lista circular de filhos
    mov     rcx, [rax + FHN_LEFT_OFFSET]
    mov     [r11 + FHN_RIGHT_OFFSET], rax
    mov     [r11 + FHN_LEFT_OFFSET], rcx
    mov     [rcx + FHN_RIGHT_OFFSET], r11
    mov     [rax + FHN_LEFT_OFFSET], r11

.link_done_child:
    mov     QWORD [r11 + FHN_PARENT_OFFSET], r10
    inc     WORD [r10 + FHN_DEGREE_OFFSET]
    mov     BYTE [r11 + FHN_MARK_OFFSET], 0
    ret

; ============================================================================
; fh_find_min — Encontra o nó mínimo na lista de raízes
; ============================================================================
fh_find_min:
    FUNC_PROLOGUE

    mov     rsi, [r8]                   ; start from any root
    test    rsi, rsi
    jz      .find_min_done

    mov     r9, rsi                      ; min_node = start
    fld     QWORD [rsi + FHN_VALUE_OFFSET]
    movsd xmm0, [r10 + FHN_VALUE_OFFSET]
    movsd [rsp - 8], xmm0              ; min_value

    mov     r10, [rsi + FHN_RIGHT_OFFSET]
.find_min_loop:
    cmp     r10, rsi                     ; voltou ao início?
    je      .find_min_done

    movsd xmm0, [rsp - 8]
    comisd xmm0, [r10 + FHN_VALUE_OFFSET]
    jbe .find_min_next

    ; Nova mínimo encontrado
    mov     r9, r10
    movsd xmm0, [r10 + FHN_VALUE_OFFSET]
    movsd [rsp - 8], xmm0
    jmp     .find_min_next

.find_min_next:
    mov     r10, [r10 + FHN_RIGHT_OFFSET]
    jmp     .find_min_loop

.find_min_done:
    mov     [r8], r9
    FUNC_EPILOGUE

; ============================================================================
; fh_decrease_key — Diminui o valor de um nó
; Entrada:
;   rdi = heap pointer
;   rsi = nó
;   xmm0 = novo valor (Q32.32)
; ============================================================================
fh_decrease_key:
    FUNC_PROLOGUE

    mov     r8, rdi                     ; heap
    mov     r9, rsi                     ; node
    movq    r10, xmm0                    ; new value

    ; Verificar se novo valor é menor
    movsd xmm1, [r9 + FHN_VALUE_OFFSET]
    comisd xmm0, xmm1
    jae .dk_not_smaller

    ; Atualizar valor
    movq    [r9 + FHN_VALUE_OFFSET], xmm0

    ; Cortar se heap property violada
    mov     rdx, [r9 + FHN_PARENT_OFFSET]
    test    rdx, rdx
    jz      .dk_no_cut                   ; nó raiz, sem violação

    movsd xmm1, [rdx + FHN_VALUE_OFFSET]
    comisd xmm1, xmm0
    jbe .dk_no_cut                   ; parent <= new value, OK

    ; Precisa cortar (cut + cascading cut)
    call    fh_cut
    call    fh_cascading_cut

.dk_no_cut:
    ; Atualizar min se necessário
    mov r11, [r8]
    movsd xmm1, [r11 + FHN_VALUE_OFFSET]
    comisd xmm1, xmm0
    jbe .dk_done
    mov     [r8], r9

.dk_not_smaller:
.dk_done:
    FUNC_EPILOGUE

; ============================================================================
; fh_cut — Remove nó do pai e adiciona à lista de raízes
; ============================================================================
fh_cut:
    ; Remove node da lista de filhos do pai
    mov     rax, [r9 + FHN_LEFT_OFFSET]
    mov     rcx, [r9 + FHN_RIGHT_OFFSET]
    mov     [rax + FHN_RIGHT_OFFSET], rcx
    mov     [rcx + FHN_LEFT_OFFSET], rax

    ; Decrementar grau do pai
    dec     WORD [rdx + FHN_DEGREE_OFFSET]

    ; Verificar se era o filho marcado
    mov     rax, [rdx + FHN_CHILD_OFFSET]
    cmp     rax, r9
    jne     .cut_child_ok
    ; Era o filho direto, atualizar
    mov     [rdx + FHN_CHILD_OFFSET], rcx
    cmp     rcx, r9                      ; era o único filho?
    jne     .cut_child_ok
    mov     QWORD [rdx + FHN_CHILD_OFFSET], 0

.cut_child_ok:
    ; Adicionar node à lista de raízes
    mov     rdi, [r8]                    ; min
    mov     rcx, [rdi + FHN_LEFT_OFFSET]
    mov     [r9 + FHN_RIGHT_OFFSET], rdi
    mov     [r9 + FHN_LEFT_OFFSET], rcx
    mov     [rcx + FHN_RIGHT_OFFSET], r9
    mov     [rdi + FHN_LEFT_OFFSET], r9

    ; Reset mark
    mov     BYTE [r9 + FHN_MARK_OFFSET], 0
    mov     QWORD [r9 + FHN_PARENT_OFFSET], 0
    ret

; ============================================================================
; fh_cascading_cut — Corte em cascata
; ============================================================================
fh_cascading_cut:
    mov     rdx, [r9 + FHN_PARENT_OFFSET]
    test    rdx, rdx
    jz      .cascading_done

    cmp     BYTE [rdx + FHN_MARK_OFFSET], 0
    jz      .cascading_mark

    ; Já marcado → cortar recursivamente
    push    r9
    mov     r9, rdx
    call    fh_cut
    pop     r9

    ; Continuar cascata
    mov     rdx, [r9 + FHN_PARENT_OFFSET]
    call    fh_cascading_cut
    jmp     .cascading_done

.cascading_mark:
    ; Primeira vez que perde filho → marcar
    mov     BYTE [rdx + FHN_MARK_OFFSET], 1

.cascading_done:
    ret
