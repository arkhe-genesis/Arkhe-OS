; ============================================================================
; ARKHE Ω-TEMP — Syscall Wrappers
; ============================================================================

%include "arkhe.inc"

section .text

global arkhe_malloc
global arkhe_calloc
global arkhe_free
global get_current_timestamp
global arkhe_debug_write
global arkhe_exit

; ============================================================================
; arkhe_malloc — Alocação de memória com zeroing
; Entrada: rdi = tamanho
; Saída:   rax = ponteiro (0 em erro)
; ============================================================================
arkhe_malloc:
    FUNC_PROLOGUE

    ; brk syscall para obter endereço atual
    xor     edi, edi
    SYSCALL 12                          ; brk(0) = obter endereço atual
    mov     r12, rax                     ; current break

    ; Calcular novo break
    add     rdi, 4095
    and     rdi, -4096                   ; alinhar a página
    add     rdi, r12

    ; brk syscall para alocar
    mov     rdi, r12
    add     rdi, rsi                     ; rsi tem o tamanho original
    SYSCALL 12                          ; brk(addr)

    cmp     rax, -1
    je      .malloc_fail

    ; Retornar ponteiro original
    mov     rax, r12

.malloc_fail:
    FUNC_EPILOGUE

; Alternativa: usar mmap para alocações grandes
arkhe_mmap:
    FUNC_PROLOGUE

    ; mmap(NULL, len, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0)
    xor     edi, edi                     ; addr = NULL (kernel escolhe)
    mov     rsi, rdi                     ; len (já em rdi)
    mov     rdx, 0x03                    ; PROT_READ | PROT_WRITE
    mov     r10, 0x22                    ; MAP_PRIVATE | MAP_ANONYMOUS
    mov     r8, -1                       ; fd = -1
    xor     r9, r9                       ; offset = 0
    SYSCALL 9                           ; mmap

    cmp     rax, -1
    je      .mmap_fail

.mmap_fail:
    FUNC_EPILOGUE

; ============================================================================
; arkhe_free — Liberação de memória
; Entrada: rdi = ponteiro
; ============================================================================
arkhe_free:
    ; Para simplicidade, usar brk syscall
    ; Em produção: manter free list ou usar munmap
    push    rdi

    xor     edi, edi
    SYSCALL 12                          ; brk(0)

    pop     rdi
    cmp     rdi, rax                     ; Liberar endereço > brk?
    jb      .free_done                   ; Se não, ignorar

    ; Reduzir brk para liberar (simplificado)
    SYSCALL 12

.free_done:
    ret

; ============================================================================
; arkhe_calloc — Alocação com zero
; Entrada: rdi = número de elementos, rsi = tamanho de cada elemento
; Saída:   rax = ponteiro
; ============================================================================
arkhe_calloc:
    FUNC_PROLOGUE

    ; Calcular tamanho total
    mov     rax, rdi
    mul     rsi

    ; Alocar
    mov     rdi, rax
    call    arkhe_malloc
    test    rax, rax
    jz      .calloc_fail

    ; Zero memory
    push    rdi
    push    rax
    mov     rcx, rax
    shr     rcx, 3
    xor     eax, eax
    rep stosq
    pop     rax
    pop     rdi

.calloc_fail:
    FUNC_EPILOGUE

; ============================================================================
; get_current_timestamp — Nanosegundos desde boot (monotonic)
; Saída: rax = nanossegundos
; ============================================================================
get_current_timestamp:
    FUNC_PROLOGUE

    ; clock_gettime(CLOCK_MONOTONIC, &ts)
    ; rdi = relatório do kernel
    sub     rsp, 16
    mov     edi, 1
    lea     rsi, [rsp]
    SYSCALL 228                          ; clock_gettime

    ; Converter para nanossegundos
    mov     rax, [rsp]                    ; segundos
    mov     rbx, 1000000000
    mul     rbx                           ; rax = segundos × 1e9
    add     rax, [rsp + 8]               ; + nanossegundos

    add     rsp, 16
    FUNC_EPILOGUE

; ============================================================================
; arkhe_debug_write — Escrever string no stderr para debug
; Entrada: rdi = string, rsi = comprimento
; ============================================================================
arkhe_debug_write:
    FUNC_PROLOGUE

    ; write(STDERR_FILENO, buf, count)
    mov     rdx, rsi
    mov     rsi, rdi
    mov     edi, 2                        ; STDERR_FILENO
    mov     eax, 1                        ; sys_write
    syscall

    FUNC_EPILOGUE

; ============================================================================
; arkhe_exit — Encerrar processo
; Entrada: rdi = código de saída
; ============================================================================
arkhe_exit:
    ; exit(code)
    ; mov     edi, edi                     ; código de saída já em rdi (edi)
    SYSCALL 60                           ; sys_exit
