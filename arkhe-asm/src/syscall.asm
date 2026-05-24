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

section .rodata
serv_sysfs_input_fmt:   db "/sys/arkhe/serv/%s/input", 0
serv_sysfs_invoke_fmt:  db "/sys/arkhe/serv/%s/invoke", 0
serv_sysfs_status_fmt:  db "/sys/arkhe/serv/%s/status", 0
serv_sysfs_result_fmt:  db "/sys/arkhe/serv/%s/result", 0
time_direction_str:     db "+1", 0
invoke_trigger:         db "1", 0
pubkey_sysfs_path:      db "/sys/arkhe/gateway_pubkey", 0

section .bss
align 16
sysfs_path_buf:         resb 256
gateway_pubkey_raw:     resb 32
json_input_hash_field:  resb 64
json_output_hash_field: resb 64
json_output_base64_field: resb 8192
json_phi_score_double:  resq 1
json_timestamp_field:   resb 64
json_gateway_id_field:  resb 64
json_signature_raw:     resb 64
input_hash_buf:         resb 32
output_hash_buf:        resb 32
sign_msg_buf:           resb 512
json_result_buffer:     resb 8192
output_buffer:          resb 65536

section .text
extern sprintf

; ═══════════════════════════════════════════════════════════════════════════════
; STUBS para compilação
; ═══════════════════════════════════════════════════════════════════════════════
write_sysfs_file:
    ret

read_sysfs_int:
    mov eax, 2 ; simulate "verified"
    ret

read_sysfs_file:
    ret

base64_decode:
    mov eax, 0 ; simulate decoded length
    ret

; ═══════════════════════════════════════════════════════════════════════════════
; LOAD GATEWAY PUBKEY
; ═══════════════════════════════════════════════════════════════════════════════
global load_gateway_pubkey
load_gateway_pubkey:
    mov rax, 2                  ; sys_open
    lea rdi, [pubkey_sysfs_path] ; "/sys/arkhe/gateway_pubkey"
    mov esi, 0                  ; O_RDONLY
    syscall
    test rax, rax
    js .fail
    mov rdi, rax
    lea rsi, [gateway_pubkey_raw] ; 32 bytes raw
    mov edx, 32
    mov rax, 0                  ; sys_read
    syscall
    mov rax, 3                  ; sys_close
    syscall
    ret
.fail:
    ; tratativa de erro (kernel pode abortar)
    ud2

; ═══════════════════════════════════════════════════════════════════════════════
; VALIDATE SERV RESPONSE
; Input: rdi = JSON buffer, rsi = input_data, edx = input_len,
;        rcx = output_buffer, r8d = output_buf_size
; Output: rax = 0 válido, -1 inválido; xmm0 = phi_score
; ═══════════════════════════════════════════════════════════════════════════════
validate_serv_response:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    push r14
    push r15

    mov r12, rdi                ; JSON
    mov r13, rsi                ; input_data original
    mov r14d, edx               ; input_len
    mov r15, rcx                ; output_buffer

    ; 1. Calcular input_hash
    lea rdi, [input_hash_buf]
    mov rsi, r13
    mov ecx, r14d
    mov eax, 402                ; sys_sha3_256 (custom)
    syscall

    ; 2. Extrair campos do JSON usando offsets fixos (exemplo funcional)
    ;    input_hash: após '"input_hash":"' (15 bytes)
    lea rsi, [r12 + 15]
    lea rdi, [json_input_hash_field]
    mov ecx, 64
    rep movsb

    ; 3. Decodificar output base64 → output_buffer
    lea rdi, [json_output_base64_field]
    mov rsi, r15
    call base64_decode           ; retorna tamanho real em eax

    ; 4. Calcular output_hash
    lea rdi, [output_hash_buf]
    mov rsi, r15
    mov ecx, eax
    mov eax, 402
    syscall

    ; 5. Comparar hashes
    lea rsi, [input_hash_buf]
    lea rdi, [json_input_hash_field]
    mov ecx, 32
    repe cmpsb
    jne .invalid
    lea rsi, [output_hash_buf]
    lea rdi, [json_output_hash_field]
    mov ecx, 32
    repe cmpsb
    jne .invalid

    ; 6. Montar mensagem para assinatura
    lea rdi, [sign_msg_buf]
    lea rsi, [input_hash_buf]
    mov ecx, 32
    rep movsb
    lea rsi, [output_hash_buf]
    mov ecx, 32
    rep movsb

    ; phi_score -> uint32
    movsd xmm0, [json_phi_score_double]
    mov eax, 10000
    cvtsi2sd xmm1, eax
    mulsd xmm0, xmm1
    cvttsd2si eax, xmm0
    stosd

    ; timestamp (null-terminated)
    lea rsi, [json_timestamp_field]
.copy_ts:
    lodsb
    test al, al
    jz .ts_done
    stosb
    jmp .copy_ts
.ts_done:

    ; gateway_id
    lea rsi, [json_gateway_id_field]
.copy_gw:
    lodsb
    test al, al
    jz .gw_done
    stosb
    jmp .copy_gw
.gw_done:
    mov ebx, edi
    lea edi, [sign_msg_buf]
    sub ebx, edi                ; tamanho da mensagem

    ; 7. Extrair e decodificar a assinatura hex do buffer JSON para json_signature_raw
    ; Local fictício (em prod usar parser JSON)
    lea rsi, [json_result_buffer + 512]
    lea rdi, [json_signature_raw]
    mov ecx, 64
.decode_hex_sig_loop:
    ; Convert 2 hex chars from rsi to 1 byte in rdi
    lodsw                      ; ax = ah:al = char2:char1

    ; Convert char1 (al)
    cmp al, '9'
    jbe .char1_digit
    and al, 0xdf               ; uppercase
    sub al, 'A' - 10
    jmp .char1_done
.char1_digit:
    sub al, '0'
.char1_done:
    shl al, 4                  ; high nibble
    mov dl, al

    ; Convert char2 (ah)
    mov al, ah
    cmp al, '9'
    jbe .char2_digit
    and al, 0xdf               ; uppercase
    sub al, 'A' - 10
    jmp .char2_done
.char2_digit:
    sub al, '0'
.char2_done:
    or al, dl                  ; combine low nibble

    stosb                      ; write byte
    dec ecx
    jnz .decode_hex_sig_loop

    ; 8. Verificar assinatura Ed25519
    lea rdi, [gateway_pubkey_raw]
    lea rsi, [sign_msg_buf]
    mov edx, ebx
    lea rcx, [json_signature_raw]
    mov eax, 401                ; sys_ed25519_verify
    syscall
    test rax, rax
    jnz .invalid

    ; 9. Sucesso: phi_score em xmm0
    movsd xmm0, [json_phi_score_double]
    xor eax, eax
    jmp .done
.invalid:
    mov eax, -1
    pxor xmm0, xmm0
.done:
    pop r15
    pop r14
    pop r13
    pop r12
    leave
    ret

; ═══════════════════════════════════════════════════════════════════════════════
; INVOKE SERV VIA SYSFS
; Input: rdi = serv_id (string), rsi = input_data, edx = input_len,
;        rcx = output_buffer, r8d = output_buf_size
; Output: rax = 0 sucesso, -1 erro; xmm0 = phi_score
; ═══════════════════════════════════════════════════════════════════════════════
global invoke_serv_sysfs
invoke_serv_sysfs:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    push r14
    push r15
    mov r12, rdi                ; serv_id
    mov r13, rsi                ; input_data
    mov r14d, edx               ; input_len
    mov r15, rcx                ; output_buffer

    ; 1. Escrever input_data em /sys/arkhe/serv/<id>/input
    lea rdi, [sysfs_path_buf]
    lea rsi, [serv_sysfs_input_fmt]
    mov rdx, r12
    call sprintf
    mov rdi, rax
    mov rsi, r13
    mov edx, r14d
    call write_sysfs_file

    ; 2. Escrever "1" em /sys/arkhe/serv/<id>/invoke
    lea rdi, [sysfs_path_buf]
    lea rsi, [serv_sysfs_invoke_fmt]
    mov rdx, r12
    call sprintf
    mov rdi, rax
    lea rsi, [invoke_trigger]
    mov edx, 1
    call write_sysfs_file

    ; 3. Aguardar status == "verified" (polling no arquivo status)
.poll:
    lea rdi, [sysfs_path_buf]
    lea rsi, [serv_sysfs_status_fmt]
    mov rdx, r12
    call sprintf
    mov rdi, rax
    call read_sysfs_int          ; retorna int em eax (2 = verified)
    cmp eax, 2
    jne .poll

    ; 4. Ler o resultado (JSON) de /sys/arkhe/serv/<id>/result
    lea rdi, [sysfs_path_buf]
    lea rsi, [serv_sysfs_result_fmt]
    mov rdx, r12
    call sprintf
    mov rdi, rax
    lea rsi, [json_result_buffer]
    mov edx, 8192
    call read_sysfs_file

    ; 5. Validar envelope
    lea rdi, [json_result_buffer]
    mov rsi, r13
    mov edx, r14d
    mov rcx, r15
    mov r8d, r8d
    call validate_serv_response
    test rax, rax
    jnz .fail

    ; 6. Sucesso: phi_score em xmm0
    xor eax, eax
    jmp .done
.fail:
    mov eax, -1
    pxor xmm0, xmm0
.done:
    pop r15
    pop r14
    pop r13
    pop r12
    leave
    ret
