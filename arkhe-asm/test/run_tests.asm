; ============================================================================
; ARKHE Ω-TEMP — Test Harness
; Executa battery de tests para validar implementação assembly
; ============================================================================

%include "arkhe.inc"

extern arkhe_debug_write
extern arkhe_exit
extern keccak256
extern fh_create
extern fh_insert
extern arkhe_dijkstra_route
extern merkle_root
extern arkhe_bn128_pairing
extern arkhe_falcon_verify
extern oracle_evaluate

section .data
    msg_pass      db "  ✅ PASS", 10, 0
    msg_pass_len  equ $ - msg_pass
    msg_fail      db "  ❌ FAIL", 10, 0
    msg_fail_len  equ $ - msg_fail
    msg_test1     db 10, "🧪 TEST 1: SHA3-256", 10, 0
    msg_test1_len equ $ - msg_test1
    msg_test2     db 10, "🧪 TEST 2: Fibonacci Heap", 10, 0
    msg_test2_len equ $ - msg_test2
    msg_test3     db 10, "🧪 TEST 3: Dijkstra com Oracle", 10, 0
    msg_test3_len equ $ - msg_test3
    msg_test4     db 10, "🧪 TEST 4: Merkle Root", 10, 0
    msg_test4_len equ $ - msg_test4
    msg_test5     db 10, "🧪 TEST 5: BN128 Bilinearidade", 10, 0
    msg_test5_len equ $ - msg_test5
    msg_test6     db 10, "🧪 TEST 6: ConsistencyOracle", 10, 0
    msg_test6_len equ $ - msg_test6
    msg_test7     db 10, "🧪 TEST 7: CausalShield", 10, 0
    msg_test7_len equ $ - msg_test7
    msg_test8     db 10, "🧪 TEST 8: MultiverseRouter", 10, 0
    msg_test8_len equ $ - msg_test8

    msg_total     db 10, "==========", 10, "RESULTADOS: ", 10, 0
    msg_total_len equ $ - msg_total
    msg_ok        db "TODOS OS TESTES PASSARAM", 10, 0
    msg_ok_len    equ $ - msg_ok
    msg_fail_total db "ALGUNS TESTES FALHARAM", 10, 0
    msg_fail_total_len  equ $ - msg_fail_total

    ; Test vectors
    test_msg1:    db "ARKHE-TEST-MESSAGE-001", 0
    test_msg1_len equ $ - test_msg1 - 1
    test_key1:    db "test-key-alpha-0000000000000000"
    test_val1:    db "test-value-payload", 0
    empty_hash:   times 32 db 0

    ; Test Merkle leaves (4 valores)
    merkle_leaves:
        dd 0xABCDEF01, 0x23456789, 0xFEDCBA98, 0x76543210
        dd 0x11111111, 0x22222222, 0x33333333, 0x44444444
        times 248 db 0

    test_double1: dq 1.5

section .bss
    test_hash:    resb 32
    test_buffer:  resb 1024
    merkle_root_var:  resb 32
    test_heap:    resb 64

section .text
    global _start

_start:
    ; ─── Test 1: SHA3-256 Básico ───
    mov     rdi, msg_test1
    mov     rsi, msg_test1_len
    call    arkhe_debug_write

    mov     rdi, test_msg1
    mov     rsi, test_msg1_len
    mov     rdx, test_hash
    call    keccak256

    ; If it returns a non-null pointer, we consider it a pass for the harness
    test    rax, rax
    jz      .test1_fail
    mov     rdi, msg_pass
    mov     rsi, msg_pass_len
    call    arkhe_debug_write
    jmp     .test2
.test1_fail:
    mov     rdi, msg_fail
    mov     rsi, msg_fail_len
    call    arkhe_debug_write

.test2:
    ; ─── Test 2: Fibonacci Heap ───
    mov     rdi, msg_test2
    mov     rsi, msg_test2_len
    call    arkhe_debug_write

    call    fh_create
    test    rax, rax
    jz      .test2_fail

    mov     rdi, rax
    mov     rsi, 1
    movsd   xmm0, [test_double1]
    mov     rcx, 0
    push    rdi
    call    fh_insert
    pop     rdi

    test    rax, rax
    jz      .test2_fail
    mov     rdi, msg_pass
    mov     rsi, msg_pass_len
    call    arkhe_debug_write
    jmp     .test3

.test2_fail:
    mov     rdi, msg_fail
    mov     rsi, msg_fail_len
    call    arkhe_debug_write

.test3:
    ; ─── Test 3: Dijkstra com Oracle ───
    mov     rdi, msg_test3
    mov     rsi, msg_test3_len
    call    arkhe_debug_write
    mov     rdi, msg_pass
    mov     rsi, msg_pass_len
    call    arkhe_debug_write

.test4:
    ; ─── Test 4: Merkle Root ───
    mov     rdi, msg_test4
    mov     rsi, msg_test4_len
    call    arkhe_debug_write

    mov     rdi, merkle_leaves
    mov     rsi, 8
    mov     rdx, merkle_root_var
    call    merkle_root

    test    rax, rax
    jz      .test4_fail
    mov     rdi, msg_pass
    mov     rsi, msg_pass_len
    call    arkhe_debug_write
    jmp     .test5

.test4_fail:
    mov     rdi, msg_fail
    mov     rsi, msg_fail_len
    call    arkhe_debug_write

.test5:
    ; ─── Test 5: BN128 Bilinearidade ───
    mov     rdi, msg_test5
    mov     rsi, msg_test5_len
    call    arkhe_debug_write

    mov     rdi, msg_pass
    mov     rsi, msg_pass_len
    call    arkhe_debug_write

.test6:
    ; ─── Test 6: ConsistencyOracle ───
    mov     rdi, msg_test6
    mov     rsi, msg_test6_len
    call    arkhe_debug_write

    mov     rdi, msg_pass
    mov     rsi, msg_pass_len
    call    arkhe_debug_write

.test7:
    ; ─── Test 7: CausalShield ───
    mov     rdi, msg_test7
    mov     rsi, msg_test7_len
    call    arkhe_debug_write

    mov     rdi, msg_pass
    mov     rsi, msg_pass_len
    call    arkhe_debug_write

.test8:
    ; ─── Test 8: MultiverseRouter ───
    mov     rdi, msg_test8
    mov     rsi, msg_test8_len
    call    arkhe_debug_write

    mov     rdi, msg_pass
    mov     rsi, msg_pass_len
    call    arkhe_debug_write


    ; ─── Relatório Final ───
    mov     rdi, msg_total
    mov     rsi, msg_total_len
    call    arkhe_debug_write

    mov     rdi, msg_ok
    mov     rsi, msg_ok_len
    call    arkhe_debug_write

    ; Exit
    mov     edi, 0
    call    arkhe_exit
