; ============================================================================
; ARKHE Ω-TEMP — ConsistencyOracle (Álgebra de Heyting)
; ============================================================================
; Implementa os 8 checks de consistência como operações na álgebra de Heyting.
; Cada check retorna um Score (Q32.32 fixed-point) no intervalo [0, 1].
;
; Operações de Heyting:
;   meet (∧)  = min(a, b)        → bottleneck
;   join (∨)  = max(a, b)        → cobertura
;   impl (→) = (a <= b) ? 1 : b  → implicação intuicionista
;   neg (¬)   = impl(a, 0)       → pseudocomplemento
; ============================================================================

%include "arkhe.inc"

extern arkhe_zk_verify
extern get_current_timestamp

section .data
    ; Thresholds em fixed-point Q32.32
    threshold_harmless      dd 0x3FEB3333      ; 0.90000
    threshold_paradox       dd 0x3FECCCCD      ; 0.95000
    threshold_entropy       dd 0x3FE33333      ; 0.80000
    threshold_coherent      dd 0x3FE9999A      ; 0.85000
    threshold_zkvalid       dd 0x3FE80000      ; 0.80000
    threshold_quantum       dd 0x3FECCCCD      ; 0.95000
    threshold_solar         dd 0x3FE33333      ; 0.70000
    threshold_galactic      dd 0x3FE33333      ; 0.70000  (v4.3.4)

    ; Pesos dos checks (× 1000, inteiros)
    weight_harmless         dd 2000            ; 2.0 × 1000
    weight_paradox          dd 3000            ; 3.0 × 1000
    weight_entropy          dd 1000            ; 1.0 × 1000
    weight_coherent         dd 1500            ; 1.5 × 1000
    weight_zkvalid          dd 1000            ; 1.0 × 1000
    weight_quantum          dd 1200            ; 1.2 × 1000
    weight_solar            dd 500             ; 0.5 × 1000
    weight_galactic         dd 500             ; 0.5 × 1000

    ; Constantes auxiliares
    solar_model_active      dq 0
    solar_switchback_state  db 0
    solar_turbulence        db 0

section .text

global oracle_evaluate
global oracle_init

; ============================================================================
; Cálculos em Fixed-Point Q32.32
; ============================================================================

; Multiplique two Q32.32 numbers, return Q32.32
; rdi = a, rsi = b → rax = result
fixed_mul:
    mov     rax, rdi
    imul    rax, rsi
    shr     rax, 32
    ret

; Divide a by b, return Q32.32
; rdi = a, rsi = b → rax = result
fixed_div:
    shl     rdi, 32
    cqo
    idiv    rsi
    ret

; Convert integer to fixed-point
; rdi = integer → rax = fixed
int_to_fixed:
    shl     rdi, 32
    mov     rax, rdi
    ret

; Convert fixed-point to integer (floor)
; rdi = fixed → rax = integer
fixed_to_int:
    sar     rdi, 32
    mov     rax, rdi
    ret

; ============================================================================
; Heyting Algebra Operations
; ============================================================================

; Meet (∧): minimum of two scores
; rdi = a (Q32.32), rsi = b → rax = min(a,b)
heyting_meet:
    cmp     rdi, rsi
    jle     .meet_a
    mov     rax, rsi
    ret
.meet_a:
    mov     rax, rdi
    ret

; Join (∨): maximum of two scores
; rdi = a, rsi = b → rax = max(a,b)
heyting_join:
    cmp     rdi, rsi
    jge     .join_a
    mov     rax, rsi
    ret
.join_a:
    mov     rax, rdi
    ret

; Implication (→): p ⇒ q = (p <= q) ? 1 : q
; rdi = p, rsi = q → rax = p → q
heyting_implication:
    cmp     rdi, rsi
    jle     .impl_one           ; p <= q → return 1 (true)
    mov     rax, rsi            ; else → return q
    ret
.impl_one:
    mov     rax, FIXED_ONE
    ret

; Negation (¬): ¬p = p → ⊥ = p → 0
; rdi = p → rax = ¬p
heyting_negation:
    xor     esi, esi            ; q = 0 (⊥)
    jmp     heyting_implication

; Biconditional (↔): (p → q) ∧ (q → p)
; rdi = p, rsi = q → rax = p ↔ q
heyting_biconditional:
    push    rdi
    push    rsi
    call    heyting_implication  ; p → q
    mov     rbx, rax
    pop     rsi
    pop     rdi
    ; Now compute q → p (swap args)
    push    rbx
    push    rdi
    push    rsi
    mov     rdi, rsi
    mov     rsi, [rsp + 16]       ; original p
    call    heyting_implication  ; q → p
    mov     rbx, [rsp]            ; p → q
    add     rsp, 8
    jmp     heyting_meet          ; min(p→q, q→p)

; ============================================================================
; Consistency Evaluation
; ============================================================================

oracle_init:
    ret

; Evaluate all checks and compute composite score
; Entrada:
;   rdi = ponteiro para mensagem (TemporalMessage)
;   rsi = edge_weight (Q32.32 fixed-point)
;   rdx = ponteiro para contexto de avaliação (EvalContext)
;   rcx = ponteiro para thresholds (Thresholds struct)
;   r8  = ponteiro para weights (CheckWeights struct)
; Saída:
;   rax = composite score (Q32.32)
;   rdx = prune flag (1 = podado, 0 = aceito)
; ============================================================================
oracle_evaluate:
    FUNC_PROLOGUE

    ; Save parameters
    mov     r12, rdi                     ; message
    mov     r13, rsi                     ; edge_weight
    mov     r14, rdx                     ; eval context
    mov     r15, rcx                     ; thresholds

    ; Prologue: allocate stack space for check results
    sub     rsp, 128                     ; 8 scores × 8 bytes × 2

    ; Initialize composite scores
    xor     rbx, rbx                    ; min_score (meet) = 0
    xor     rbp, rbp                    ; weighted_sum (join) = 0
    mov     qword [rsp], FIXED_ONE      ; Start with top element
    mov     qword [rsp + 8], 0          ; total_weight

    ; ──────────────── CHECK 1: Harmless ────────────────
    call    check_harmless
    mov     [rsp + 16], rax              ; Store score_harmless

    ; Apply weight
    mov     rdi, rax
    call    int_to_fixed
    mov     rdi, [rel weight_harmless]
    imul    rdi, rax
    shr     rdi, 32
    add     qword [rsp + 8], rdi        ; total_weight += weight
    add     rbp, rdi                     ; weighted_sum += score * weight

    ; Meet (bottleneck tracking)
    cmp     rax, rbx
    cmovb   rbx, rax                    ; min_score = min(min_score, score)

    ; ──────────────── CHECK 2: Paradox-Free ────────────────
    call    check_paradox_free
    mov     [rsp + 24], rax              ; Store score_paradox

    mov     rdi, rax
    call    int_to_fixed
    mov     rdi, [rel weight_paradox]
    imul    rdi, rax
    shr     rdi, 32
    add     qword [rsp + 8], rdi
    add     rbp, rdi

    cmp     rax, rbx
    cmovb   rbx, rax

    ; ──────────────── CHECK 3: Entropy-Safe ────────────────
    call    check_entropy_safe
    mov     [rsp + 32], rax

    mov     rdi, rax
    call    int_to_fixed
    mov     rdi, [rel weight_entropy]
    imul    rdi, rax
    shr     rdi, 32
    add     qword [rsp + 8], rdi
    add     rbp, rdi

    cmp     rax, rbx
    cmovb   rbx, rax

    ; ──────────────── CHECK 4: Coherent ────────────────
    call    check_coherent
    mov     [rsp + 40], rax

    mov     rdi, rax
    call    int_to_fixed
    mov     rdi, [rel weight_coherent]
    imul    rdi, rax
    shr     rdi, 32
    add     qword [rsp + 8], rdi
    add     rbp, rdi

    cmp     rax, rbx
    cmovb   rbx, rax

    ; ──────────────── CHECK 5: ZK Valid ────────────────
    call    check_zk_valid
    mov     [rsp + 48], rax

    mov     rdi, rax
    call    int_to_fixed
    mov     rdi, [rel weight_zkvalid]
    imul    rdi, rax
    shr     rdi, 32
    add     qword [rsp + 8], rdi
    add     rbp, rdi

    cmp     rax, rbx
    cmovb   rbx, rax

    ; ──────────────── CHECK 6: Quantum Time ────────────────
    call    check_quantum_time
    mov     [rsp + 56], rax

    mov     rdi, rax
    call    int_to_fixed
    mov     rdi, [rel weight_quantum]
    imul    rdi, rax
    shr     rdi, 32
    add     qword [rsp + 8], rdi
    add     rbp, rdi

    cmp     rax, rbx
    cmovb   rbx, rax

    ; ──────────────── CHECK 7: Solar Coherence ────────────────
    call    check_solar_coherence
    mov     [rsp + 64], rax

    mov     rdi, rax
    call    int_to_fixed
    mov     rdi, [rel weight_solar]
    imul    rdi, rax
    shr     rdi, 32
    add     qword [rsp + 8], rdi
    add     rbp, rdi

    cmp     rax, rbx
    cmovb   rbx, rax

    ; ──────────────── CHECK 8: Galactic Coherence ────────────────
    call    check_galactic_coherence
    mov     [rsp + 72], rax

    mov     rdi, rax
    call    int_to_fixed
    mov     rdi, [rel weight_galactic]
    imul    rdi, rax
    shr     rdi, 32
    add     qword [rsp + 8], rdi
    add     rbp, rdi

    cmp     rax, rbx
    cmovb   rbx, rax

    ; ══════════════════════════════════
    ; COMPOSITE SCORE (Álgebra de Heyting)
    ; ══════════════════════════════════

    ; Composite = 0.7 × weighted_average + 0.3 × bottleneck (meet)
    ; weighted_avg = weighted_sum / total_weight

    cmp     qword [rsp + 8], 0
    je      .oracle_finalize

    ; Compute weighted average
    mov     rax, rbp                    ; weighted_sum (× 1000)
    mov     rdi, [rsp + 8]              ; total_weight (× 1000)
    call    fixed_div                   ; rax = avg_score (Q32.32)
    mov     rbp, rax

    ; Apply Heyting combination:
    ; result = join(0.7 × avg, 0.3 × meet)
    ;
    ; 0.7 in Q32.32: 0x00000000B3333333
    mov     rdi, rax                    ; avg (Q32.32)
    mov     rsi, 0xB3333333     ; ≈ 0.7 in Q64.64
    call    fixed_mul                   ; rbp = 0.7 × avg

    ; 0.3 × min_score (meet)
    mov     rdi, rbx                    ; min_score
    mov     rsi, 0x4CCCCCCC        ; ≈ 0.3 in Q64.64
    call    fixed_mul                   ; rax = 0.3 × meet

    ; Join: max of the two components
    mov     rdi, rbp
    mov     rsi, rax
    call    heyting_join

    ; Determine pruning
.oracle_finalize:
    ; Compare with threshold (Paradox is strictest: 0.95)
    mov     rdi, rax                    ; composite score
    mov     rsi, [rel threshold_paradox]
    call    heyting_implication

    ; If implication gives back 1 (⊤), score ≥ threshold → accepted
    ; If it gives < 1, score < threshold → pruned
    test    rax, rax
    jz      .oracle_pruned
    cmp     rax, FIXED_ONE
    je      .oracle_accepted

.oracle_pruned:
    mov     rdx, 1
    jmp     .oracle_done
.oracle_accepted:
    mov     rdx, 0
.oracle_done:
    ; rax already contains composite score

    add     rsp, 128
    FUNC_EPILOGUE

; ============================================================================
; CHECK 1: Harmless — "A rota causa dano?"
; ============================================================================
; Detecta loops e custos excessivos
check_harmless:
    ; r12 = message, r14 = eval context
    push    rdi
    push    rsi

    xor     eax, eax
    mov     rax, FIXED_ONE               ; Score = 1.0 (top)

    ; Check sender == receiver (loop)
    mov     rdi, [r12 + MSG_SENDER_OFFSET]
    mov     rsi, [r12 + MSG_RECEIVER_OFFSET]
    cmp     rdi, rsi
    jne     .harmless_no_self_loop
    ; Self-loop detected
    mov     rax, FIXED_TOP              ; ¬⊤ = 0 (PARADOX)
    jmp     .harmless_done

.harmless_no_self_loop:
    ; Check accumulated cost from context
    test    r14, r14
    jz      .harmless_done

    ; Verify accumulated cost is reasonable
    ; (Simplified: trust context evaluation)

.harmless_done:
    pop     rsi
    pop     rdi
    ret

; ============================================================================
; CHECK 2: Paradox-Free
; ============================================================================
check_paradox_free:
    push    rdi
    push    rsi
    push    rdx
    push    rcx

    xor     eax, eax
    mov     rax, FIXED_ONE               ; Start at ⊤

    ; source_ts must be <= target_ts
    mov     rax, [r12 + MSG_SRC_TS_OFFSET]
    mov     rcx, [r12 + MSG_TGT_TS_OFFSET]
    cmp     rax, rcx
    jbe     .paradox_temporal_ok
    ; Paradox: source > target
    xor     eax, eax                    ; Score = 0 (⊥)
    jmp     .paradox_done

.paradox_temporal_ok:
    ; Check: target - source must be reasonable
    sub     rcx, rax                     ; Δt = target - source
    ; If Δt < 0 → paradox (already handled)
    ; If Δt > MAX_INTERVAL → suspicious
    cmp     rcx, BLOCK_INTERVAL_NSEC
    jbe     .paradox_ok
    ; Δt exceeds expected max — possible paradox
    ; Score = clamp(MAX_INTERVAL / Δt, 0, 1)
    mov     rax, BLOCK_INTERVAL_NSEC
    xor     edx, edx
    div     rcx                          ; rax = MAX_INTERVAL / Δt
    cmp     rax, FIXED_ONE
    jbe     .paradox_ok
    mov     rax, FIXED_ONE

.paradox_ok:
.paradox_done:
    pop     rcx
    pop     rdx
    pop     rsi
    pop     rdi
    ret

; ============================================================================
; CHECK 3: Entropy-Safe
; ============================================================================
check_entropy_safe:
    push    rdi
    push    rsi

    mov     rax, FIXED_ONE               ; Score = 1.0

    ; Estimate entropy from content size
    mov     rdi, [r12 + MSG_CONTENT_LEN_OFFSET]
    cmp     rdi, 1048576                 ; 1MB threshold
    jbe     .entropy_ok
    ; Excessive content → reduce score
    ; score = max(0, 1 - (size / (10MB)))
    mov     rsi, 10485760                ; 10MB
    xor     edx, edx
    mov     rax, rdi
    div     rsi
    mov     rsi, FIXED_ONE
    sub     rsi, rax
    jns     .entropy_ok
    xor     esi, esi
.entropy_ok:
    mov     rax, rsi

    pop     rsi
    pop     rdi
    ret

; ============================================================================
; CHECK 4: Coherent — Temporal freshness
; ============================================================================
check_coherent:
    push    rdi
    push    rsi
    push    rdx

    call    get_current_timestamp        ; rax = now
    sub     rax, [r12 + MSG_SRC_TS_OFFSET]  ; age = now - source_ts
    js      .coherence_fresh             ; Negative = future message

    ; Check age threshold (100 blocks)
    mov     rsi, BLOCK_INTERVAL_NSEC
    imul    rsi, 100
    cmp     rax, rsi
    jbe     .coherence_fresh

    ; Stale message: score degrades linearly
    ; score = max(0, 1 - age / (1000 blocks))
    mov     rdi, BLOCK_INTERVAL_NSEC
    imul    rdi, 1000
    xor     edx, edx
    div     rdi
    mov     rax, FIXED_ONE
    sub     rax, rdx                    ; rdx has remainder info, use quotient
    js      .coherence_min
    jmp     .coherence_done

.coherence_fresh:
    mov     rax, FIXED_ONE
    jmp     .coherence_done

.coherence_min:
    xor     eax, eax

.coherence_done:
    pop     rdx
    pop     rsi
    pop     rdi
    ret

; ============================================================================
; CHECK 5: ZK Valid — Zero-Knowledge Proof Check
; ============================================================================
check_zk_valid:
    ; If no ZK proof present, give partial score (0.8)
    ; In production, full ZK-SNARK verification goes here

    mov     al, [r12 + MSG_ZK_PRESENT_OFFSET]
    test    al, al
    jz      .zk_no_proof

    ; Verify proof (placeholder — in production: BN128 pairing)
    lea     rdi, [r12 + MSG_ZK_PROOF_OFFSET]
    lea     rsi, [r12 + MSG_HASH_CACHE_OFFSET]
    call    arkhe_zk_verify
    test    al, al
    jnz     .zk_valid

    ; Invalid proof
    xor     eax, eax
    mov     al, 0xC4              ; ≈ 0.33 in Q32.32 (low score)
    ret

.zk_no_proof:
    ; No proof → partial trust
    mov     eax, 0xCCCCCCCC             ; ≈ 0.8 in Q32.32
    ret

.zk_valid:
    mov     eax, FIXED_ONE
    ret

; ============================================================================
; CHECK 6: Quantum Time
; ============================================================================
check_quantum_time:
    push    rdi
    push    rsi

    mov     rax, FIXED_ONE

    ; Quantum tolerance window (100ns)
    mov     rdi, [r12 + MSG_TGT_TS_OFFSET]
    sub     rdi, [r12 + MSG_SRC_TS_OFFSET]
    js      .quantum_time_invalid
    cmp     rdi, 100                    ; 100ns tolerance
    ja      .quantum_time_suspicious
    jmp     .quantum_time_ok

.quantum_time_invalid:
    xor     eax, eax
    jmp     .quantum_time_done

.quantum_time_suspicious:
    ; Degrade score based on how far outside window
    mov     rax, FIXED_ONE
    ; Subtract penalty proportional to time outside window
    ; ... (simplified: 0.5 penalty)
    shr     rax, 1                      ; 0.5
    jmp     .quantum_time_done

.quantum_time_ok:
    mov     rax, FIXED_ONE

.quantum_time_done:
    pop     rsi
    pop     rdi
    ret

; ============================================================================
; CHECK 7: Solar Coherence
; ============================================================================
check_solar_coherence:
    push    rdi
    push    rsi

    ; Check if solar model is active
    test    QWORD [rel solar_model_active], 1
    jz      .solar_default

    ; Read switchback state
    mov     al, [rel solar_switchback_state]
    test    al, al
    jz      .solar_no_switchback

    ; Switchback active — degrade score
    movzx   eax, BYTE [rel solar_turbulence]  ; 0-255
    ; Score = max(0, 1.0 - turbulence * 0.6)
    imul    eax, 600                     ; turbulence * 0.6 * 1000
    mov     ecx, 1000
    xor     edx, edx
    div     ecx                         ; eax = penalty
    mov     ecx, FIXED_ONE
    sub     ecx, eax
    js      .solar_zero
    mov     eax, ecx
    jmp     .solar_done

.solar_no_switchback:
    mov     eax, FIXED_ONE
    jmp     .solar_done

.solar_zero:
    xor     eax, eax
    jmp     .solar_done

.solar_default:
    mov     eax, FIXED_ONE

.solar_done:
    pop     rsi
    pop     rdi
    ret

; ============================================================================
; CHECK 8: Galactic Coherence — Ledger consistency
; ============================================================================
check_galactic_coherence:
    ; Verify against Ledger Galáctico
    ; In production: verificar Merkle proof contra ledger
    mov     eax, FIXED_ONE
    ret
