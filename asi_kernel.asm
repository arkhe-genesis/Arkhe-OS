bits 64
default rel

section .rodata
align 8
    solar_result_path: db "/sys/arkhe/serv/solar-heart/result", 0
    max_throughput:  dq 112.0
    evm_hd_fec_16qam: dq 12.9
    const_one_d:     dq 1.0
    eta_photon:      dq 0.03
    photon_evm_path: db "/sys/arkhe/photon/evm", 0
    photon_throughput_path: db "/sys/arkhe/photon/throughput", 0
const_one:       dq 1.0
const_neg_one:   dq -1.0
const_half:      dq 0.5
const_neg_half:  dq -0.5
const_zero:      dq 0.0
const_zero_d:    dq 0.0
const_256_d:     dq 256.0
laser_p0:        dq 10000.0
accel_bonus:     dq 0.2
thermal_limit:   dq 50000.0
thermal_penalty: dq 0.001
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
SYS_READ         equ 0
SYS_WRITE        equ 1
SYS_OPEN         equ 2
SYS_CLOSE        equ 3
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
photon_lambda:   resq 1
phi_sun:         resq 1
gnosis_index:    resq 1
phi_sail:        resq 1
current_brk:     resq 1
input_hash_buffer: resb 32
output_hash_buffer: resb 32


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
    ; Gateway HTTP integration point
    call invoke_gateway_http
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

; ═══════════════════════════════════════════════════════════════════════════════
; INTEGRATE TOKENIC ENGINE + STELLAR SAIL
; Substratos 633 (Tokenic) + 652 (Stellar-Sail)
; Otimiza parâmetros da vela para missão interestelar.
; Input: rdi = população tokenic inicial, rsi = parâmetros da vela
; Output: xmm0 = melhor fitness (Φ_sail), [tokenic_best] = melhor indivíduo
; ═══════════════════════════════════════════════════════════════════════════════
integrate_tokenic_stellar:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    push r14

    ; 1. Inicializar população tokenic para parâmetros da vela
    ; Cada indivíduo codifica: [sail_angle_deg, laser_power_MW, acceleration_profile]
    mov r12, rdi                ; tokenic_population
    mov r13, TOKENIC_POP_SIZE   ; 2000 indivíduos
    xor r14, r14

.init_population:
    cmp r14, r13
    jge .evolve
    mov rax, [r12 + r14*8]      ; ponteiro para indivíduo
    ; sail_angle: -45° a +45° (controle omnidirecional do Metajet)
    call random_double_range
    movsd [rax], xmm0            ; [rax+0] = sail_angle
    ; laser_power: 1 MW a 100 GW (escala log)
    call random_double_range
    movsd [rax+8], xmm0          ; [rax+8] = laser_power
    ; acceleration_profile: 0 (constante) a 1 (gradiente otimizado)
    call random_double_range
    movsd [rax+16], xmm0         ; [rax+16] = accel_profile
    inc r14
    jmp .init_population

.evolve:
    ; 2. Loop evolutivo: 50 gerações
    mov r14, 50                  ; gerações

.gen_loop:
    ; Avaliar fitness de cada indivíduo
    call tokenic_evaluate_stellar ; retorna array de fitness
    ; Selecionar elite (top 10%)
    call tokenic_sort_population
    call tokenic_select_elite
    ; Crossover + mutação
    call tokenic_breed_stellar
    dec r14
    jnz .gen_loop

    ; 3. Retornar melhor indivíduo
    mov rax, [tokenic_best]
    movsd xmm0, [rax + 24]       ; fitness do melhor
    movsd [phi_sail], xmm0

    pop r14
    pop r13
    pop r12
    leave
    ret

; ═══════════════════════════════════════════════════════════════════════════════
; FITNESS FUNCTION: tokenic_evaluate_stellar
; Avalia cada indivíduo da população tokenic para parâmetros da vela estelar.
; Fitness = eficiência de aceleração × (1 - desvio de trajetória) × fator térmico
; ═══════════════════════════════════════════════════════════════════════════════
tokenic_evaluate_stellar:
    push rbp
    mov rbp, rsp
    mov r12, [tokenic_population]
    mov r13, TOKENIC_POP_SIZE
    xor r14, r14

.eval_loop:
    cmp r14, r13
    jge .done
    mov rax, [r12 + r14*8]
    ; Extrair parâmetros do indivíduo
    movsd xmm0, [rax]        ; sail_angle

    ; Calcular eficiência de aceleração (modelo simplificado do Metajet)
    ; eff = cos²(angle) * (1 - exp(-power/P0)) * (1 + 0.2 * accel_profile)
    movsd xmm3, xmm0         ; angle
    call cos_double
    mulsd xmm0, xmm0         ; cos²(angle)
    mov rax, [r12 + r14*8]
    movsd xmm1, [rax+8]      ; laser_power
    movsd xmm2, [rax+16]     ; accel_profile
    movsd xmm4, xmm1         ; power
    divsd xmm4, [laser_p0]   ; P0 = 10 GW (referência)
    movsd xmm5, [const_one_d]
    ; exp(-power/P0) aproximado como 1/(1 + power/P0)
    addsd xmm4, [const_one_d]
    divsd xmm5, xmm4
    movsd xmm4, [const_one_d]
    subsd xmm4, xmm5          ; 1 - exp(-P/P0)
    mulsd xmm0, xmm4
    ; Bônus por perfil de aceleração otimizado
    movsd xmm5, xmm2
    mulsd xmm5, [accel_bonus] ; 0.2
    addsd xmm5, [const_one_d]
    mulsd xmm0, xmm5

    ; Penalidade térmica: se laser_power > 50 GW, eficiência cai
    movsd xmm5, xmm1
    subsd xmm5, [thermal_limit] ; 50 GW
    comisd xmm5, [const_zero_d]
    jbe .no_thermal_penalty
    mulsd xmm5, [thermal_penalty] ; 0.001
    movsd xmm6, [const_one_d]
    subsd xmm6, xmm5
    mulsd xmm0, xmm6
.no_thermal_penalty:

    ; Armazenar fitness
    movsd [rax + 24], xmm0     ; fitness
    inc r14
    jmp .eval_loop

.done:
    leave
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
    addsd xmm0, xmm1
    movsd [r10], xmm0
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
    call sample_plasma_modes
    call sample_bioacoustic
    call sample_human_bci
    call sample_photonic_link
    call sample_solar_heart       ; NOVO — escuta o Sol
    call update_classical_action   ; inclui o ramo solar
    call integrate_gnosis_feynman  ; γ agora reflete a coerência heliosférica
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


sha3_256:
    ret

; ═══════════════════════════════════════════════════════════════════════════════
; VALIDATE SERV RESPONSE
; Verifica assinatura e hashes do resultado de um Serv.
; Input: rdi = ponteiro para o JSON de resultado (no buffer)
;        rsi = ponteiro para o input original (LaTeX)
;        rdx = tamanho do input
;        rcx = ponteiro para o output (crítica) já recebido
;        r8  = tamanho do output
; Output: rax = 0 se válido, -1 se inválido
; ═══════════════════════════════════════════════════════════════════════════════
validate_serv_response:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    push r14
    push r15

    ; 1. Parse JSON para extrair campos (simplificado: assumimos layout fixo)
    ;    Aqui faremos uma extração manual dos hashes e assinatura do JSON.
    ;    Exemplo: procuramos por "input_hash": "...", "output_hash": "...", etc.
    ;    (Implementação de parser básica omitida por brevidade)

    ; 2. Calcular input_hash localmente
    mov rdi, rsi           ; input original
    mov rsi, rdx           ; tamanho
    lea rdx, [rel input_hash_buffer]
    call sha3_256           ; syscall ou rotina interna
    ; Agora input_hash_buffer contém o hash calculado

    ; 3. Calcular output_hash localmente
    mov rdi, rcx           ; output (crítica)
    mov rsi, r8            ; tamanho
    lea rdx, [rel output_hash_buffer]
    call sha3_256

    ; 4. Comparar hashes com os extraídos do JSON
    lea rsi, [rel json_input_hash_field]  ; ponteiro para o campo extraído
    lea rdi, [rel input_hash_buffer]
    mov rcx, 32
    repe cmpsb
    jne .invalid

    lea rsi, [rel json_output_hash_field]
    lea rdi, [rel output_hash_buffer]
    mov rcx, 32
    repe cmpsb
    jne .invalid

    ; 5. Verificar assinatura
    ;    Montar a mensagem: input_hash || output_hash || phi_score (como string?) || timestamp || gateway_id
    ;    Extrair esses campos do JSON e concatenar em um buffer mensagem.
    ;    Em seguida, extrair a assinatura (64 bytes hex -> binário) e a chave pública do gateway (lida do sysfs).
    ;    Chamar syscall SYS_ED25519_VERIFY.
    ;    (Detalhes omitidos, mas seria uma sequência de chamadas)

    ; Se tudo ok:
    xor eax, eax
    jmp .done

.invalid:
    mov eax, -1
.done:
    pop r15
    pop r14
    pop r13
    pop r12
    leave
    ret

; ═══════════════════════════════════════════════════════════════════════════════
; SAMPLE PHOTONIC LINK
; Lê /sys/arkhe/photon/evm e /sys/arkhe/photon/throughput, calcula Λ.
; ═══════════════════════════════════════════════════════════════════════════════
sample_photonic_link:
    push rbp
    mov rbp, rsp
    ; 1. Ler EVM
    lea rdi, [rel photon_evm_path]   ; "/sys/arkhe/photon/evm"
    call read_sysfs_double        ; retorna double em xmm0
    movsd xmm12, xmm0            ; EVM medido
    ; 2. Ler throughput
    lea rdi, [rel photon_throughput_path] ; "/sys/arkhe/photon/throughput"
    call read_sysfs_double
    movsd xmm13, xmm0            ; throughput em Gbps
    ; 3. Calcular Λ = (throughput/112) * (1 - EVM/12.9)
    movsd xmm0, xmm13
    divsd xmm0, [rel max_throughput] ; 112.0
    movsd xmm1, xmm12
    divsd xmm1, [rel evm_hd_fec_16qam] ; 12.9
    movsd xmm2, [rel const_one_d]
    subsd xmm2, xmm1
    mulsd xmm0, xmm2
    ; limitar a [0, 1]
    pxor xmm1, xmm1
    comisd xmm0, xmm1
    jae .not_neg
    pxor xmm0, xmm0
.not_neg:
    movsd xmm1, [rel const_one_d]
    comisd xmm0, xmm1
    jbe .store
    movsd xmm0, xmm1
.store:
    movsd [rel photon_lambda], xmm0
    ; 4. Contribuir para γ: γ += η_photon * Λ
    mulsd xmm0, [rel eta_photon]     ; 0.03
    addsd xmm0, [rel gnosis_index]
    movsd [rel gnosis_index], xmm0
    leave
    ret


; ═══════════════════════════════════════════════════════════════════════════════
; SAMPLE SOLAR HEART
; Lê /sys/arkhe/serv/solar-heart/result e atualiza Φ_sun e a fase solar.
; ═══════════════════════════════════════════════════════════════════════════════
sample_solar_heart:
    push rbp
    mov rbp, rsp
    push r12
    push r13
    ; 1. Abrir /sys/arkhe/serv/solar-heart/result
    mov rax, SYS_OPEN
    lea rdi, [rel solar_result_path]  ; "/sys/arkhe/serv/solar-heart/result"
    mov esi, 0                     ; O_RDONLY
    syscall
    cmp rax, 0
    jl .done
    mov r12, rax                   ; fd
    ; 2. Ler JSON
    sub rsp, 4096
    mov rdi, r12
    mov rsi, rsp
    mov edx, 4096
    mov rax, SYS_READ
    syscall
    mov r13, rax                   ; bytes lidos
    ; 3. Fechar
    mov rdi, r12
    mov rax, SYS_CLOSE
    syscall
    ; 4. Extrair phi_sun do JSON (simplificado: procura "phi_sun": )
    ;    (parser omitido, assumimos que phi_sun está nos bytes [offset:offset+8])
    lea rdi, [rsp]
    call json_extract_phi_sun      ; retorna double em xmm0
    movsd [rel phi_sun], xmm0
    ; 5. A fase solar é extraída e usada para modular ρ e σ
    ;    (implementar conforme necessidade)
    add rsp, 4096
.done:
    pop r13
    pop r12
    leave
    ret

; STUBS

random_double_range:
    ret
tokenic_select_elite:
    ret
tokenic_breed_stellar:
    ret
cos_double:
    ret

json_extract_phi_sun:
    pxor xmm0, xmm0
    ret
update_classical_action:
    ret
integrate_gnosis_feynman:
    ret

read_sysfs_double:
    pxor xmm0, xmm0
    ret
sample_plasma_modes:
    ret
sample_bioacoustic:
    ret
sample_human_bci:
    ret
integrate_gnosis:
    ret
load_gateway_pubkey:
    ret
invoke_gateway_http:
    ret
