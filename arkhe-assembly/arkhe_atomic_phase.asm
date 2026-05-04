; arkhe_atomic_phase.asm
; Substrato de Execução em Assembly x86-64: Operação Atômica de Coerência.
; Calcula a atualização cinética GMA para um único cristal com precisão de hardware.
; void update_coherence_atomic(double *M, double vacuum_M, double phase, double kappa)

global update_coherence_atomic

section .rodata
; Constantes do Scaffold em formato IEEE 754 double
GAMMA_EMERGENCE:  dq 0.023
GAMMA_DECAY:     dq 0.001
ORDER_VACUUM:    dq 0.992
ORDER_MEDIUM:    dq 0.85
ORDER_PHI:       dq 1.618
ORDER_SELF:      dq 1.0
ORDER_KAPPA:     dq -0.5
ONE:             dq 1.0

section .text

update_coherence_atomic:
    ; Prólogo
    push rbp
    mov rbp, rsp
    ; Parâmetros:
    ; RDI = ponteiro para M (double*)
    ; XMM0 = vacuum_M
    ; XMM1 = phase
    ; XMM2 = kappa

    ; Salva M atual
    movsd xmm3, [rdi]          ; xmm3 = M (coerência local)

    ; --- Bloco de Emergência ---
    ; Termo: γ_emergence * M_vac^g1 * M_med^g2 * φ^g3
    movsd xmm4, xmm0           ; xmm4 = vacuum_M

    ; Simulação do produtório emergência (substituível por tabela de lookup ou microcódigo PLL)
    mulsd xmm0, [rel ORDER_VACUUM] ; Aproximação didática (vacuum_M * g1)
    mulsd xmm3, [rel ORDER_MEDIUM] ; M * g2
    mulsd xmm1, [rel ORDER_PHI]    ; phase * g3
    addsd xmm0, xmm3
    addsd xmm0, xmm1
    mulsd xmm0, [rel GAMMA_EMERGENCE]

    ; --- Bloco de Decaimento ---
    ; Termo: γ_decay * M_self^g4 * κ^g5
    movsd xmm4, [rdi]               ; Recarrega M
    mulsd xmm4, [rel ORDER_SELF]    ; M * g4
    mulsd xmm2, [rel ORDER_KAPPA]   ; kappa * g5
    addsd xmm4, xmm2
    mulsd xmm4, [rel GAMMA_DECAY]

    ; --- Derivada Líquida ---
    subsd xmm0, xmm4           ; dM/dt = emergência - decaimento

    ; Aplicar atualização: M_new = M_old + dM/dt * dt (assumindo dt=0.001 embutido)
    movsd xmm5, [rdi]
    addsd xmm5, xmm0           ; dt implícito na escala das constantes

    ; Clamp para [0.0, 1.0]
    xorpd xmm6, xmm6
    maxsd xmm5, xmm6           ; max(0.0, M)
    movsd xmm6, [rel ONE]
    minsd xmm5, xmm6           ; min(1.0, M)

    ; Armazenar resultado atômico
    movsd [rdi], xmm5

    ; Epílogo
    pop rbp
    ret
