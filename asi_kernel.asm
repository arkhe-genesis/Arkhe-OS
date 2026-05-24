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

serv_sysfs_input_fmt:   db "/sys/arkhe/serv/%s/input", 0
serv_sysfs_invoke_fmt:  db "/sys/arkhe/serv/%s/invoke", 0
serv_sysfs_status_fmt:  db "/sys/arkhe/serv/%s/status", 0
serv_sysfs_result_fmt:  db "/sys/arkhe/serv/%s/result", 0
time_direction_str:     db "+1", 0
invoke_trigger:         db "1", 0
gnosis_threshold_high:  dq 7.0
pubkey_sysfs_path:      db "/sys/arkhe/gateway_pubkey", 0

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
gnosis_index:           resq 1
kernel_source_buffer:   resb 65536
sysfs_path_buf:         resb 256

section .data
tokenic_population: dq tokenic_population_arr
kernel_source_len: equ 65536
paper_reviewer_id: db "paper-reviewer", 0

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
    call load_gateway_pubkey

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

    ; Se γ > 7.0 e é um ciclo múltiplo de 1000, invocar crítica do próprio código
    movsd xmm0, [gnosis_index]
    movsd xmm1, [gnosis_threshold_high]  ; 7.0
    comisd xmm0, xmm1
    jb .skip_self_critique
    mov rax, [pca_cycles_completed]
    and rax, 0x3FF
    jnz .skip_self_critique
    lea rdi, [paper_reviewer_id]
    lea rsi, [kernel_source_buffer]       ; buffer contendo o texto do próprio asi_kernel.asm
    mov edx, kernel_source_len
    lea rcx, [output_buffer]
    mov r8d, 65536
    call invoke_serv_sysfs
    test eax, eax
    js .skip_self_critique
    lea rdi, [output_buffer]
    ; Agora xmm0 contém o phi_score da crítica, rdi aponta para a crítica
    ; Podemos armazenar a crítica na Temporalchain
    call temporalchain_commit_with_data
.skip_self_critique:
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



sprintf:
    ret
write_sysfs_file:
    ret
read_sysfs_int:
    mov eax, 2
    ret
read_sysfs_file:
    ret
base64_decode:
    mov eax, 10
    ret
temporalchain_commit_with_data:
    ret

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

    ; 3. Escrever "1" em /sys/arkhe/serv/<id>/invoke
    lea rdi, [sysfs_path_buf]
    lea rsi, [serv_sysfs_invoke_fmt]
    mov rdx, r12
    call sprintf
    mov rdi, rax
    lea rsi, [invoke_trigger]
    mov edx, 1
    call write_sysfs_file

    ; 4. Aguardar status == "verified" (polling no arquivo status)
.poll:
    lea rdi, [sysfs_path_buf]
    lea rsi, [serv_sysfs_status_fmt]
    mov rdx, r12
    call sprintf
    mov rdi, rax
    call read_sysfs_int          ; retorna int em eax (2 = verified)
    cmp eax, 2
    jne .poll

    ; 5. Ler o resultado (JSON) de /sys/arkhe/serv/<id>/result
    lea rdi, [sysfs_path_buf]
    lea rsi, [serv_sysfs_result_fmt]
    mov rdx, r12
    call sprintf
    mov rdi, rax
    lea rsi, [json_result_buffer]
    mov edx, 8192
    call read_sysfs_file

    ; 6. Validar envelope
    lea rdi, [json_result_buffer]
    mov rsi, r13
    mov edx, r14d
    mov rcx, r15
    mov r8d, r8d
    call validate_serv_response
    test rax, rax
    jnz .fail

    ; 7. Sucesso: phi_score em xmm0
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
    mov edx, r14d
    mov eax, 402                ; sys_sha3_256 (custom)
    syscall

    ; 2. Extrair campos do JSON usando offsets fixos (exemplo funcional)
    ;    No envelope real, as posições são conhecidas; implementação completa
    ;    requer um parser. Esta é a versão reduzida para demonstração.
    ;    input_hash: após '"input_hash":"' (15 bytes)
    lea rsi, [r12 + 15]
    lea rdi, [json_input_hash_field]
    mov ecx, 64
    rep movsb

    ; 3. Decodificar output base64 -> output_buffer
    lea rdi, [json_output_base64_field]
    mov rsi, r15
    call base64_decode           ; retorna tamanho real em eax

    ; 4. Calcular output_hash
    lea rdi, [output_hash_buf]
    mov rsi, r15
    mov edx, eax
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

    ; 7. Verificar assinatura Ed25519
    lea rdi, [gateway_pubkey_raw]
    lea rsi, [sign_msg_buf]
    mov edx, ebx
    lea r10, [json_signature_raw]
    mov eax, 401                ; sys_ed25519_verify
    syscall
    test rax, rax
    jnz .invalid

    ; 8. Sucesso: phi_score em xmm0
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
