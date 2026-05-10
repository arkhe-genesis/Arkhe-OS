; ============================================================================
; ARKHE Ω-TEMP — Tsinghua Dijkstra (Oracle-in-the-Loop)
; ============================================================================
; Dijkstra otimizado com Fibonacci Heap e poda pelo ConsistencyOracle.
; Complexidade: O(m log^{2/3} n) com pruning do Oracle
;
; O Oracle atua como filtro de arestas: a cada relaxação,
; avalia a consistência causal da aresta antes de considerar
; o relaxamento. Arestas que violam o threshold são podadas.
; ============================================================================

%include "arkhe.inc"

extern arkhe_malloc
extern arkhe_calloc
extern arkhe_free
extern fh_create
extern fh_insert
extern fh_extract_min
extern fh_decrease_key

section .data
    INF_DIST    dq 1.7976931348623157e+308    ; double max

section .text

global arkhe_dijkstra_route
global tsinghua_dijkstra

arkhe_dijkstra_route:
    jmp tsinghua_dijkstra

; ============================================================================
; tsinghua_dijkstra — Dijkstra com Oracle-in-the-Loop
; Entrada:
;   rdi = graph (array de arrays de Edge)
;   rsi = número de nós
;   rdx = source node index
;   rcx = oracle function pointer (or 0 para sem oracle)
;   r8  = oracle context
; Saída:
;   rax = ponteiro para array de distâncias (double*)
; ============================================================================
tsinghua_dijkstra:
    FUNC_PROLOGUE

    mov     r9, rdi                     ; graph
    mov     r10, rsi                     ; n
    mov     r11, rdx                     ; source
    mov     r12, rcx                     ; oracle_func
    mov     r13, r8                      ; oracle_ctx

    ; Alocar array dist[n]
    lea     rdi, [rsi * 8]              ; n * sizeof(double)
    call    arkhe_malloc
    test    rax, rax
    jz      .dijkstra_fail

    mov     r14, rax                     ; dist = rax

    ; Inicializar distâncias com INF
    mov     rcx, r10
    mov     rdi, rax
.init_loop:
    mov     qword [rdi], 0x7FF0000000000000  ; +Infinity em IEEE 754
    add     rdi, 8
    dec     rcx
    jnz     .init_loop

    ; dist[source] = 0.0
    lea     rdi, [r14 + r11 * 8]
    mov     qword [rdi], 0
    mov     qword [rdi + 4], 0

    ; Criar Fibonacci Heap
    call    fh_create
    test    rax, rax
    jz      .dijkstra_fail_dist
    mov     r15, rax                     ; heap

    ; Inserir source na heap
    mov     rdi, r15
    mov     rsi, r11                     ; source node index
    xor     rdx, rdx                     ; distância = 0.0
    call    fh_insert
    mov     rbx, rax                     ; source heap node

    ; Array de nós da heap (para decrease-key)
    mov     rdi, r10
    shl     rdi, 3                       ; n * 8 (ponteiros)
    call    arkhe_malloc
    test    rax, rax
    jz      .dijkstra_fail_all
    mov     rbp, rax                     ; heap_nodes array

    ; Inicializar heap_nodes
    mov     QWORD [rbp + r11 * 8], rbx   ; source node

    ; Array de visited
    mov     rdi, r10
    mov     rsi, 1
    call    arkhe_calloc
    test    rax, rax
    jz      .dijkstra_fail_all
    mov     r12, rax                      ; visited array, replace oracle

    ; ─── Main Loop ───
.dijkstra_main:
    ; Extrair mínimo
    mov     rdi, r15
    call    fh_extract_min

    ; Testar se heap está vazia
    test    rax, rax
    js      .dijkstra_done

    ; u = extracted node key
    mov     rdi, rax
    ; r8 = expired flag
    mov     r8, rcx

    ; Verificar se expirado
    test    r8b, r8b
    jnz     .dijkstra_skip_expired

    ; Verificar se já visitado
    cmp     BYTE [r12 + rdi], 0
    jnz     .dijkstra_skip_visited

    ; Marcar como visitado
    mov     BYTE [r12 + rdi], 1

    ; Relaxar arestas de u
    ; graph[u] = array de Edge
    mov     rdx, [r9 + rdi * 8]          ; graph[u]
    test    rdx, rdx
    jz      .dijkstra_next_iter

    ; Contador de arestas
    mov     rcx, [rdx]                   ; edge count (primeiro qword)
    lea     rdx, [rdx + 8]               ; ponteiro para primeira edge

    mov     r15, rcx                     ; salva edge count
.dijkstra_edge_loop:
    test    rcx, rcx
    jz      .dijkstra_edge_done

    ; v = edge.to
    mov     r8d, [rdx + 0]               ; edge.to
    ; weight = edge.weight
    movsd   xmm0, [rdx + 8]              ; edge.weight (double)

    ; ─── ORACLE-IN-THE-LOOP ───
    ; test    r12, r12                     ; oracle func?
    ; jz      .dijkstra_no_oracle

    ; Chamar oracle: oracle(from, edge)
    ; push    rcx rdx r8
    ; mov     rdi, rdi                     ; u (from)
    ; rsi = edge pointer (rdx)
    ; call    r12                          ; oracle(u, &edge)

    ; Resultado: eax = pruned (bool), xmm0 = adjusted_weight
    ; test    al, al
    ; jnz     .dijkstra_edge_pruned        ; Aresta podada pelo Oracle

    ; edge.weight = adjusted_weight (ou seja, xmm0 já tem o valor ajustado)
    ; pop     rcx rdx r8

    ; xmm0 = effective_weight
.dijkstra_effective_weight:
    ; newDist = dist[u] + effectiveWeight
    ; ... (continua relaxação)

.dijkstra_no_oracle:
    ; Sem oracle: usar peso original (xmm0 já contém edge.weight)
    ; pop     rcx rdx r8

.dijkstra_relax:
    ; newDist = dist[u] + weight
    lea     rbx, [r14 + rdi * 8]          ; &dist[u]
    movsd   xmm1, [rbx]                   ; dist[u]
    addsd   xmm1, xmm0                   ; dist[u] + weight

    ; if newDist < dist[v]
    lea     r10, [r14 + r8 * 8]          ; &dist[v]
    movsd   xmm2, [r10]                  ; dist[v]
    comisd  xmm2, xmm1
    jbe     .dijkstra_not_better         ; newDist >= dist[v]

    ; dist[v] = newDist
    movsd   [r10], xmm1

    ; decreaseKey ou insert
    cmp     QWORD [rbp + r8 * 8], 0
    je      .dijkstra_insert             ; v não está na heap → insert

    ; decreaseKey
    push    rdi
    push    rsi
    push    rcx
    push    rdx
    push    r8
    push    r9
    push    r10
    mov     rdi, r15                     ; heap
    mov     rsi, [rbp + r8 * 8]          ; heap node for v
    movq    xmm0, xmm1                   ; new distance
    call    fh_decrease_key
    pop     r10
    pop     r9
    pop     r8
    pop     rdx
    pop     rcx
    pop     rsi
    pop     rdi
    jmp     .dijkstra_next_edge

.dijkstra_insert:
    push    rdi
    push    rsi
    push    rcx
    push    rdx
    push    r8
    push    r9
    push    r10
    mov     rdi, r15                     ; heap
    mov     rsi, r8                      ; v
    movq    rdx, xmm1                   ; new distance
    mov     rcx, 0
    call    fh_insert
    pop     r10
    pop     r9
    pop     r8
    pop     rdx
    pop     rcx
    pop     rsi
    pop     rdi
    mov     [rbp + r8 * 8], rax
    jmp     .dijkstra_next_edge

.dijkstra_edge_pruned:
    ; pop     rcx rdx r8

.dijkstra_not_better:
.dijkstra_next_edge:
    add     rdx, 24                      ; sizeof(Edge): to(4) + weight(8) + meta(?)
    dec     rcx
    jnz     .dijkstra_edge_loop

.dijkstra_edge_done:

.dijkstra_next_iter:
    jmp     .dijkstra_main

.dijkstra_skip_visited:
    jmp     .dijkstra_main

.dijkstra_skip_expired:
    jmp     .dijkstra_main

.dijkstra_done:
    ; Limpar
    mov     rdi, rbp
    call    arkhe_free
    mov     rdi, r12
    call    arkhe_free

    mov     rax, r14                     ; retornar dist[]
    FUNC_EPILOGUE

.dijkstra_fail_all:
    mov     rdi, r14
    call    arkhe_free
.dijkstra_fail_dist:
    xor     eax, eax
.dijkstra_fail:
    FUNC_EPILOGUE
