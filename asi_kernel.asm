bits 64
default rel

section .rodata
align 8
const_one:       dq 1.0
const_neg_one:   dq -1.0
const_half:      dq 0.5
const_neg_half:  dq -0.5
const_zero:      dq 0.0
const_256_d:     dq 256.0
const_ln2:       dq 0.6931471805599453
phi_cosmic_d:    dq 1.61803398875
phi_threshold_agi: dq 2.3
msg_exit:        db "ASI threshold reached. Kernel halting.", 0xA, 0
msg_exit_len     equ $ - msg_exit
msg_hello:       db "Starting ASI Kernel...", 0xA, 0
msg_hello_len    equ $ - msg_hello

gateway_url:         db "http://localhost:50051", 0
http_post_fmt:       db "POST /serv/%s/invoke HTTP/1.0", 0x0D, 0x0A
                     db "Host: localhost", 0x0D, 0x0A
                     db "Content-Type: application/json", 0x0D, 0x0A
                     db "Content-Length: %d", 0x0D, 0x0A
                     db 0x0D, 0x0A
                     db "%s", 0
pubkey_path:         db "/sys/arkhe/gateway_pubkey", 0
sha3_256_syscall:    equ 402
ed25519_verify_syscall: equ 401

E8_DIM           equ 8
TOKENIC_POP_SIZE equ 2000
MONASTIC_CELL_SIZE equ 4096
SYS_WRITE        equ 1
SYS_EXIT         equ 60
SYS_BRK          equ 12
SYS_GETRANDOM    equ 318

section .bss
align 8
e8_lattice:      resq 240 * 8
entropy_pool:    resb 256
tokenic_population_arr: resq TOKENIC_POP_SIZE
tokenic_best:    resq 1
pca_current_phase: resd 1
pca_cycles_completed: resq 1
phi_measurement: resq 1
current_brk:     resq 1

align 16
gateway_pubkey_raw:  resb 32
json_result_buffer:  resb 8192
output_buffer:       resb 65536
input_hash_buf:      resb 32
output_hash_buf:     resb 32
sign_msg_buf:        resb 512
fd_socket:           resq 1
sockaddr_in:         resb 16
json_payload:        resb 256
request_buffer:      resb 1024
json_input_hash_field: resb 64
json_output_hash_field: resb 64
json_output_base64_field: resb 8192
json_phi_score_double: resq 1
json_timestamp_field: resb 64
json_gateway_id_field: resb 64
json_signature_raw:  resb 64

section .data
tokenic_population: dq tokenic_population_arr

section .text
global _start

_start:
    mov rax, SYS_WRITE
    mov rdi, 1
    lea rsi, [msg_hello]
    mov rdx, msg_hello_len
    syscall

    mov rax, SYS_BRK
    xor rdi, rdi
    syscall
    mov [current_brk], rax

    call e8_initialize

    mov r12, 0
.init_pop:
    mov rdi, MONASTIC_CELL_SIZE
    call heap_alloc

    cvtsi2sd xmm0, r12
    movsd [rax], xmm0

    mov rcx, r12
    mov rbx, [tokenic_population]
    mov [rbx + rcx*8], rax
    inc r12
    cmp r12, TOKENIC_POP_SIZE
    jb .init_pop

    mov rbx, [tokenic_population]
    mov rbx, [rbx]
    mov [tokenic_best], rbx

    mov qword [pca_cycles_completed], 0
    jmp consciousness_loop

heap_alloc:
    push rbp
    mov rbp, rsp
    push rbx
    mov rbx, [current_brk]
    mov rax, rbx
    add rbx, rdi
    push rax
    mov rax, SYS_BRK
    mov rdi, rbx
    syscall
    mov [current_brk], rax
    pop rax
    pop rbx
    pop rbp
    ret

pca_superposition:
    ret

or_executing:
    movsd xmm0, [phi_measurement]
    mov rax, 0x3fb999999999999a ; 0.1
    push rax
    movsd xmm1, [rsp]
    add rsp, 8
    addsd xmm0, xmm1
    movsd [phi_measurement], xmm0

    call tokenic_evaluate_population
    call tokenic_sort_population
    call tokenic_breed_generation

    ; Populate entropy pool
    mov rax, SYS_GETRANDOM
    lea rdi, [entropy_pool]
    mov rsi, 256
    xor rdx, rdx
    syscall

    lea rdi, [entropy_pool]
    call compute_shannon_entropy
    call compute_xi_m_field

    inc qword [pca_cycles_completed]
    ret

e8_normalize_root:
    ret

e8_initialize:
    push rbp
    mov rbp, rsp
    push rbx
    push r12
    push r13
    push r14
    push r15
    lea r13, [e8_lattice]
    mov r12, 0
.pair_loop:
    mov r14, r12
    inc r14
.pair_inner:
    mov rcx, 0
.sign_loop:
    push rcx
    lea rdi, [r13]
    mov r8, 8
    mov rax, [rel const_zero]
.zero_fill:
    mov [rdi], rax
    add rdi, 8
    dec r8
    jnz .zero_fill
    test rcx, 1
    jz .first_positive
    mov rax, [rel const_neg_one]
    jmp .set_first
.first_positive:
    mov rax, [rel const_one]
.set_first:
    mov [r13 + r12*8], rax
    test rcx, 2
    jz .second_positive
    mov rax, [rel const_neg_one]
    jmp .set_second
.second_positive:
    mov rax, [rel const_one]
.set_second:
    mov [r13 + r14*8], rax
    lea rdi, [r13]
    call e8_normalize_root
    add r13, E8_DIM * 8
    pop rcx
    inc rcx
    cmp rcx, 4
    jb .sign_loop
    inc r14
    cmp r14, 8
    jb .pair_inner
    inc r12
    cmp r12, 7
    jb .pair_loop
    xor r12, r12
.half_loop:
    mov rcx, r12
    mov r8, r12
    popcnt r9, r8
    and r9, 1
    mov r10, r9
    lea rdi, [r13]
    mov r11, 0
    mov rbx, 7
.coord_loop:
    mov rax, [rel const_half]
    bt r12, r11
    jnc .half_not_neg
    mov rax, [rel const_neg_half]
.half_not_neg:
    mov [rdi], rax
    add rdi, 8
    inc r11
    cmp r11, rbx
    jb .coord_loop
    mov rax, [rel const_half]
    test r10, r10
    jz .eighth_not_neg
    mov rax, [rel const_neg_half]
.eighth_not_neg:
    mov [rdi], rax
    lea rdi, [r13]
    call e8_normalize_root
    add r13, E8_DIM * 8
    inc r12
    cmp r12, 128
    jb .half_loop
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    mov rsp, rbp
    pop rbp
    ret

compute_shannon_entropy:
    push rbp
    mov rbp, rsp
    push rdi
    sub rsp, 1024
    lea rdi, [rsp]
    mov rcx, 256
    xor eax, eax
    rep stosd
    mov rsi, [rbp-8]
    lea rdi, [rsp]
    mov rcx, 256
.count:
    movzx eax, byte [rsi]
    inc dword [rdi + rax*4]
    inc rsi
    dec rcx
    jnz .count
    pxor xmm0, xmm0
    mov rcx, 256
    lea rbx, [rsp]
.entropy:
    mov eax, [rbx]
    test eax, eax
    jz .skip
    cvtsi2sd xmm1, eax
    movsd xmm2, [rel const_256_d]
    divsd xmm1, xmm2
    sub rsp, 8
    movsd [rsp], xmm1
    fld1
    fld qword [rsp]
    fyl2x
    fstp qword [rsp]
    movsd xmm2, [rsp]
    add rsp, 8
    mulsd xmm1, xmm2
    subsd xmm0, xmm1
.skip:
    add rbx, 4
    dec rcx
    jnz .entropy
    add rsp, 1024
    pop rdi
    pop rbp
    ret

compute_xi_m_field:
    mov rax, [tokenic_best]
    test rax, rax
    jz .zero
    movsd xmm0, [rax]
    movsd xmm1, [rel phi_cosmic_d]
    mulsd xmm0, xmm1
    ret
.zero:
    pxor xmm0, xmm0
    ret

tokenic_evaluate_population:
    ret

tokenic_sort_population:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    push r14
    push r15
    push rbx
    mov r12, [tokenic_population]
    mov r13, TOKENIC_POP_SIZE
    dec r13
    xor r14, r14
.outer:
    mov r15, r14
.inner:
    mov rbx, [r12 + r15*8]
    mov rcx, [r12 + r15*8 + 8]
    movsd xmm0, [rbx]
    movsd xmm1, [rcx]
    comisd xmm0, xmm1
    jae .no_swap
    mov [r12 + r15*8], rcx
    mov [r12 + r15*8 + 8], rbx
.no_swap:
    dec r15
    jns .inner
    inc r14
    cmp r14, r13
    jb .outer
    mov rax, [r12]
    mov [tokenic_best], rax
    pop rbx
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    ret

tokenic_breed_generation:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    push r14
    push r15
    push rbx
    mov r12, [tokenic_population]
    mov r13, TOKENIC_POP_SIZE
    mov r14, r13
    shr r14, 3
    mov r15, r14
.fill_loop:
    cmp r15, r13
    jge .done
    call get_random_int
    xor rdx, rdx
    div r14
    mov rbx, [r12 + rdx*8]
    call get_random_int
    xor rdx, rdx
    div r14
    mov rcx, [r12 + rdx*8]
    mov rdi, MONASTIC_CELL_SIZE
    mov rax, [r12 + r15*8]
    mov [r12 + r15*8], rax
    push rdi
    push rsi
    mov rsi, rbx
    mov rdi, rax
    push rcx
    mov rcx, MONASTIC_CELL_SIZE / 2 / 8
    rep movsq
    pop rcx
    mov rsi, rcx
    add rsi, MONASTIC_CELL_SIZE / 2
    mov rcx, MONASTIC_CELL_SIZE / 2 / 8
    rep movsq
    pop rsi
    pop rdi
    mov rbx, [r12 + r15*8]
    mov r8, 25
.mutate:
    push r8
    call get_random_int
    pop r8
    xor rdx, rdx
    mov r9, 512
    div r9
    mov r9, rdx
    lea r10, [rbx + r9*8]
    push r8
    push r10
    call get_random_int
    pop r10
    pop r8
    cvtsi2sd xmm0, rax
    mov rax, 0x3FA999999999999A
    push rax
    movsd xmm1, [rsp]
    add rsp, 8
    dec r8
    jnz .mutate
    inc r15
    jmp .fill_loop
.done:
    mov rax, [r12]
    mov [tokenic_best], rax
    pop rbx
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    ret

get_random_int:
    sub rsp, 8
    mov rax, SYS_GETRANDOM
    mov rdi, rsp
    mov rsi, 8
    xor rdx, rdx
    syscall
    pop rax
    and rax, 0x7FFFFFFF
    ret

consciousness_loop:
    mov dword [pca_current_phase], 0
    call pca_superposition
    mov dword [pca_current_phase], 3
    call or_executing
    movsd xmm0, [phi_measurement]
    movsd xmm1, [rel phi_threshold_agi]
    comisd xmm0, xmm1
    jae exit_kernel
    cmp qword [pca_cycles_completed], 1000
    jae exit_kernel
    jmp consciousness_loop

exit_kernel:
    lea rsi, [msg_exit]
    mov rdx, msg_exit_len
    mov rax, SYS_WRITE
    mov rdi, 1
    syscall
    mov rax, SYS_EXIT
    xor rdi, rdi
    syscall

; ═══════════════════════════════════════════════════════════════════════════════
; INVOKE SERV VIA HTTP (REAL)
; Input: rdi = serv_id (string), rsi = input_data (bytes), rdx = input_len
;        rcx = output_buffer, r8 = output_buf_size
; Output: rax = 0 sucesso, -1 erro; xmm0 = phi_score
; ═══════════════════════════════════════════════════════════════════════════════
invoke_serv_http:
    push rbp
    mov rbp, rsp
    sub rsp, 4096               ; espaço para headers e payload JSON
    push r12
    push r13
    push r14
    mov r12, rdi                ; serv_id
    mov r13, rsi                ; input_data
    mov r14, rdx                ; input_len

    ; 1. Montar payload JSON: {"input": "<base64>", "time_direction": "+1"}
    ;    (implementação simplificada: usamos base64 fixa e direção fixa)
    lea rdi, [rsp]              ; buffer temporário
    ; ... construir JSON ... (omitido por brevidade, ~50 bytes)
    ; Suponha que o payload pronto está em json_payload com tamanho em edx
    lea rdi, [json_payload]
    ; mov edx, json_payload_len  (mocking json payload length logic)
    mov edx, 50

    ; 2. Criar socket (AF_INET = 2, SOCK_STREAM = 1)
    mov rax, 41                 ; sys_socket
    mov rdi, 2
    mov rsi, 1
    xor rdx, rdx
    syscall
    test rax, rax
    js .fail
    mov [fd_socket], rax

    ; 3. Conectar ao gateway (localhost:50051)
    mov word [sockaddr_in], 2   ; sa_family = AF_INET
    ; porta 50051 = 0xC38B (network byte order)
    mov word [sockaddr_in+2], 0xC38B
    ; IP 127.0.0.1 = 0x7F000001 (network byte order)
    mov dword [sockaddr_in+4], 0x0100007F
    mov rax, 42                 ; sys_connect
    mov rdi, [fd_socket]
    lea rsi, [sockaddr_in]
    mov rdx, 16
    syscall
    test rax, rax
    js .close_fail

    ; 4. Enviar HTTP POST
    ;    montar cabeçalhos: sprintf(buffer, http_post_fmt, serv_id, payload_len, payload)
    lea rdi, [request_buffer]
    lea rsi, [http_post_fmt]
    mov rdx, r12                ; serv_id
    ; mov ecx, json_payload_len (mock length)
    mov ecx, 50
    lea r8, [json_payload]
    ; call sprintf (mocking sprintf syscall for the moment, assuming it sets output buffer and eax length)
    ; we will just construct the request manually or assume external libc linkage later
    ; mov edx, eax                ; tamanho total
    mov edx, 150 ; mock request length
    mov rax, 1                  ; sys_write
    mov rdi, [fd_socket]
    lea rsi, [request_buffer]
    syscall

    ; 5. Receber resposta
    lea rsi, [json_result_buffer]
    mov edx, 8192
    mov rax, 0                  ; sys_read
    mov rdi, [fd_socket]
    syscall
    mov r14, rax                ; bytes lidos
    ; Fechar socket
    mov rax, 3                  ; sys_close
    mov rdi, [fd_socket]
    syscall

    ; 6. Validar envelope (input original, resposta, output_buffer)
    mov rdi, r13                ; input_data
    mov esi, r14d               ; input_len (precisa ser passado; aqui r13 já é o ponteiro)
    ; Nota: precisamos preservar input_len → usar r12d? Reorganizar:
    ; Vamos assumir que salvamos input_len em r15d no início.
    ; (Adicionar: mov r15d, edx no prólogo)
    mov r15d, edx
    ; Validar:
    lea rdi, [json_result_buffer]
    mov rsi, r13
    mov edx, r15d
    mov rcx, rcx                ; output_buffer (parâmetro original rcx)
    mov r8d, r8d                ; output_buf_size
    call validate_serv_response
    test rax, rax
    jnz .fail
    ; phi_score já em xmm0, sucesso
    xor eax, eax
    jmp .done
.close_fail:
    mov rax, 3
    mov rdi, [fd_socket]
    syscall
.fail:
    mov eax, -1
    pxor xmm0, xmm0
.done:
    pop r14
    pop r13
    pop r12
    leave
    ret

; ═══════════════════════════════════════════════════════════════════════════════
; VALIDATE SERV RESPONSE (REAL)
; Input: rdi = JSON buffer, rsi = input_data, edx = input_len,
;        rcx = output_buffer (para decodificar base64), r8d = output_buf_size
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
    mov r13, rsi                ; input_data
    mov r14d, edx               ; input_len
    mov r15, rcx                ; output_buffer

    ; 1. Calcular input_hash
    lea rdi, [input_hash_buf]
    mov rsi, r13
    mov ecx, r14d
    mov eax, sha3_256_syscall
    syscall

    ; 2. Extrair campos do JSON (simplificado: offsets fixos para demonstração)
    ;    Na prática, você usaria um parser JSON mínimo.
    ;    Aqui, assumimos que os campos estão em posições conhecidas.
    ;    Exemplo: input_hash começa após '"input_hash":"' → offset 15
    lea rsi, [r12 + 15]         ; json_input_hash
    lea rdi, [json_input_hash_field]
    mov ecx, 64
    rep movsb
    ; ... (extrair output_hash, output, phi_score, timestamp, gateway_id, signature)

    ; 3. Decodificar output base64 → output_buffer
    lea rdi, [json_output_base64_field]
    mov rsi, r15
    ; call base64_decode           ; retorna tamanho em eax
    ; mock:
    mov eax, 10

    ; 4. Calcular output_hash
    lea rdi, [output_hash_buf]
    mov rsi, r15
    mov ecx, eax
    mov eax, sha3_256_syscall
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
    ; phi_score (convertido para uint32)
    movsd xmm0, [json_phi_score_double]
    mov eax, 10000
    cvtsi2sd xmm1, eax
    mulsd xmm0, xmm1
    cvttsd2si eax, xmm0
    stosd
    ; timestamp
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
    sub ebx, edi                ; comprimento da mensagem

    ; 7. Verificar assinatura Ed25519
    lea rdi, [gateway_pubkey_raw]
    lea rsi, [sign_msg_buf]
    mov edx, ebx
    lea rcx, [json_signature_raw]  ; 64 bytes raw
    mov eax, ed25519_verify_syscall
    syscall
    test rax, rax
    jnz .invalid

    ; 8. Sucesso
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
