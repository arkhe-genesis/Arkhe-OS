# rvi-test.s — Suite de teste de invariância RISC-VI

.section .text
.globl _start

_start:
    # Teste 1: Inicialização
    INV.INIT x10, #0
    INV.INIT x11, #1
    add x12, x10, x11           # x12 deve ser 1
    bne x12, x11, test_fail

    # Teste 2: Força invariante
    MUSCLE.SET_PHASE x13, x11, #0   # Aplica fase ao Músculo 0
    MUSCLE.GET_FORCE x14, #0        # Lê força
    # Força deve ser 1 ± 1e-6 N
    sub x15, x14, x11
    abs x15, x15
    li x16, 1e-6
    bgt x15, x16, test_fail

    # Teste 3: Verificação de invariância
    INV.VERIFY x17, x14, #1e-6
    beq x17, x0, test_fail

    # Teste 4: Selo
    SEAL.GENERATE x18, x17, #TEST_SEAL
    SEAL.VERIFY x19, x18, x2
    beq x19, x0, test_fail

    # Teste 5: Ômega
    OMEGA.FIXPOINT x20, x2, #CODEX_GEN
    OMEGA.VERIFY x21, x20
    beq x21, x0, test_fail

    # Todos os testes passaram
    j test_pass

test_fail:
    INV.HESITATE #100
    SEAL.GENERATE x22, x0, #FAILURE_SEAL
    j .

test_pass:
    INV.HESITATE #10
    SEAL.GENERATE x22, x1, #SUCCESS_SEAL
    j .
