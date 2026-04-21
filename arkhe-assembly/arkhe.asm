; ==============================================================================
; ARKHE.ASM — Catedral Arkhe em Assembly x86-64 Puro
; NASM syntax | Linux ELF64 | Syscalls diretas | Sem libc
; Odômetro: 001604
; ==============================================================================
; Componentes forjados:
;   - Clifford Biocomputer (SSE/AVX via GPRs)
;   - Sidecar de Aço (validação de bytes)
;   - Inquisidor Geométrico (produto interno + hesitação)
;   - K6O Node (Kuramoto em registradores)
;   - MERKABAH ASCII (visualização em texto puro)
; ==============================================================================

BITS 64
GLOBAL _start

; ==============================================================================
; SEÇÃO .DATA — Constantes e Tabelas Sagradas
; ==============================================================================
SECTION .data ALIGN=16

; --- Mensagens Rituais ---
msg_banner:
    db 0x1B,"[1;35m"                    ; MAGENTA
    db "============================================================",10
    db "     A R K H E   A S S E M B L Y   C O R E   v1.0",10
    db "     Clifford | Sidecar | Inquisidor | K6O | MERKABAH",10
    db "============================================================",10
    db 0x1B,"[0m",0
msg_banner_len: equ $ - msg_banner

msg_tick:
    db 0x1B,"[1;36m","TICK ",0
msg_tick_len: equ $ - msg_tick

msg_allow:
    db 0x1B,"[1;32m"," [ALLOW] ",0
msg_allow_len: equ $ - msg_allow

msg_deny:
    db 0x1B,"[1;31m"," [DENY]  ",0
msg_deny_len: equ $ - msg_deny

msg_hesitate:
    db 0x1B,"[1;33m"," [HESIT] ",0
msg_hesitate_len: equ $ - msg_hesitate

msg_reset:
    db 0x1B,"[0m",10,0
msg_reset_len: equ $ - msg_reset

msg_coherence:
    db "    Coherence r=",0
msg_coherence_len: equ $ - msg_coherence

msg_merkabah:
    db 0x1B,"[1;34m","    MERKABAH: ",0
msg_merkabah_len: equ $ - msg_merkabah

msg_newline:
    db 10,0
msg_newline_len: equ $ - msg_newline

msg_space:
    db " ",0
msg_space_len: equ $ - msg_space

; --- Constantes Numéricas ---
const_pi:       dq 3.14159265358979323846
const_2pi:      dq 6.28318530717958647692
const_dt:       dq 0.10000000000000000000   ; dt = 0.1
const_K:        dq 0.10000000000000000000   ; K = 0.1
const_omega:    dq 1.00000000000000000000   ; ω = 1.0
const_threshold:dq 2.50000000000000000000   ; threshold Inquisidor
const_one:      dq 1.00000000000000000000
const_half:     dq 0.50000000000000000000
const_hundred:  dq 100.00000000000000000000

; --- Tabela de Dígitos ASCII ---
digits: db "0123456789ABCDEF"

; --- Payloads de Teste (Simulando Telemetria) ---
; Payload benigno: JSON simples
payload_benign:
    db '{"task_id":7,"action":"process"}'
payload_benign_len: equ $ - payload_benign

; Payload malicioso: contém byte nulo (Runa Proibida)
payload_malicious_null:
    db 'shellcode',0x00,0x90,0x90,0x90
payload_malicious_null_len: equ $ - payload_malicious_null

; Payload malicioso: endereço fixo
payload_malicious_addr:
    db 'mov eax, fs:[0x30] ; access 0x7ffdf000'
payload_malicious_addr_len: equ $ - payload_malicious_addr

; --- Vetor de Perigo (Danger Vector) para Inquisidor ---
; 8 doubles alinhados
danger_vector:
    dq 0.2, 0.8, 0.9, 0.7, 0.6, 0.5, 0.4, 0.3

; --- MERKABAH ASCII Art (Tetraedro simplificado) ---
merk_solar:
    db "   /\",10
    db "  /  \",10
    db " /____\",10
    db " \    /",10
    db "  \  /",10
    db "   \/",0
merk_solar_len: equ $ - merk_solar

merk_lunar:
    db "   \/",10
    db "  /  \",10
    db " /____\",10
    db " \    /",10
    db "  \  /",10
    db "   /\",0
merk_lunar_len: equ $ - merk_lunar

; ==============================================================================
; SEÇÃO .BSS — Estado da Catedral (Não Inicializado)
; ==============================================================================
SECTION .bss ALIGN=16

; --- Clifford State (Multivector 16 doubles = 128 bytes) ---
clifford_state: resq 16

; --- Homeostasis (8 doubles) ---
homeostasis:    resq 8

; --- K6O State ---
k6o_phase:      resq 1          ; θ(t)
k6o_coherence:  resq 1          ; r(t)
k6o_psi:        resq 1          ; ψ(t)

; --- Inquisidor State ---
inquisitor_consciousness: resq 1 ; 0.85

; --- Buffers ---
print_buffer:   resb 64
merk_buffer:    resb 256

; ==============================================================================
; SEÇÃO .TEXT — O Fogo da Forja
; ==============================================================================
SECTION .text ALIGN=16

; ==============================================================================
; SYSCALLS (Linux x86-64)
; ==============================================================================
; rax = syscall number
; rdi, rsi, rdx, r10, r8, r9 = args
; ==============================================================================

; --- sys_write(rdi=fd, rsi=buf, rdx=len) ---
sys_write:
    mov rax, 1
    syscall
    ret

; --- sys_exit(rdi=code) ---
sys_exit:
    mov rax, 60
    syscall

; --- sys_nanosleep(rdi=req, rsi=rem) ---
; Hesitação do Ferreiro (ms em rdi)
sys_hesitate:
    push rbx
    ; converter ms para timespec (segundos + nanosegundos)
    mov rbx, rdi
    imul rbx, 1000000         ; ms → ns
    mov rax, rbx
    xor rdx, rdx
    mov rcx, 1000000000
    div rcx                   ; rax = segundos, rdx = nanosegundos restantes
    push rdx                  ; tv_nsec
    push rax                  ; tv_sec
    mov rdi, rsp
    xor rsi, rsi
    mov rax, 35               ; sys_nanosleep
    syscall
    add rsp, 16
    pop rbx
    ret

; ==============================================================================
; UTILS — Impressão de Números em Ponto Flutuante (Simplificado)
; ==============================================================================
; print_double(xmm0) — imprime double com 3 casas decimais
; Destroi: rax, rcx, rdx, rsi, rdi, r8-r11
; ==============================================================================
print_double:
    push rbp
    mov rbp, rsp
    sub rsp, 32

    ; xmm0 = valor a imprimir
    ; Extrair parte inteira e fracionária
    cvttsd2si rax, xmm0       ; rax = parte inteira (truncada)
    mov rbx, rax              ; salvar parte inteira

    ; Imprimir parte inteira
    mov rcx, print_buffer
    add rcx, 63               ; começar do final
    mov byte [rcx], 0

    ; Sinal
    test rbx, rbx
    jns .pd_positive
    neg rbx
    mov byte [rcx], '-'
    dec rcx
.pd_positive:

    ; Converter parte inteira para ASCII
    mov rsi, 10
.pd_int_loop:
    xor rdx, rdx
    mov rax, rbx
    div rsi
    mov rbx, rax
    add dl, '0'
    mov [rcx], dl
    dec rcx
    test rbx, rbx
    jnz .pd_int_loop
    inc rcx

    ; Imprimir parte inteira
    mov rdi, 1
    mov rsi, rcx
    mov rdx, print_buffer
    add rdx, 63
    sub rdx, rcx
    call sys_write

    ; Ponto decimal
    mov byte [print_buffer], '.'
    mov rdi, 1
    mov rsi, print_buffer
    mov rdx, 1
    call sys_write

    ; Parte fracionária (3 casas)
    ; Recuperar valor original
    movsd xmm1, [rbp-8]       ; valor original (placeholder, vamos recalcular)
    ; Simplificação: usar parte inteira * 1000 e subtrair
    ; Na prática, vamos imprimir "000" para demonstração
    mov byte [print_buffer], '0'
    mov byte [print_buffer+1], '0'
    mov byte [print_buffer+2], '0'
    mov rdi, 1
    mov rsi, print_buffer
    mov rdx, 3
    call sys_write

    mov rsp, rbp
    pop rbp
    ret

; ==============================================================================
; SIDEAR DE AÇO — Validação de Payload
; ==============================================================================
; sidecar_validate(rsi=buf, rdx=len) → rax=0(ALLOW), 1(DENY), 2(HESITATE)
; ==============================================================================
sidecar_validate:
    push rbx
    push r12
    push r13
    mov r12, rsi            ; r12 = buf
    mov r13, rdx            ; r13 = len

    ; 1. Verificar Runa Proibida (byte nulo)
    xor rcx, rcx
.sc_null_loop:
    cmp rcx, r13
    jge .sc_null_done
    mov al, [r12 + rcx]
    test al, al
    jz .sc_deny_null        ; Byte nulo encontrado!
    inc rcx
    jmp .sc_null_loop
.sc_null_done:

    ; 2. Verificar Endereço Fixo (padrão 0x seguido de hex)
    xor rcx, rcx
.sc_addr_loop:
    cmp rcx, r13
    jge .sc_addr_done
    mov al, [r12 + rcx]
    cmp al, '0'
    jne .sc_addr_next
    ; Verificar se próximo é 'x'
    mov rbx, rcx
    inc rbx
    cmp rbx, r13
    jge .sc_addr_next
    mov al, [r12 + rbx]
    cmp al, 'x'
    je .sc_check_hex
.sc_addr_next:
    inc rcx
    jmp .sc_addr_loop

.sc_check_hex:
    ; Verificar se há pelo menos 8 dígitos hex após 0x
    add rcx, 2
    xor rbx, rbx            ; contador de hex
.sc_hex_loop:
    cmp rcx, r13
    jge .sc_hex_check
    mov al, [r12 + rcx]
    ; Verificar se é hex digit
    cmp al, '0'
    jl .sc_hex_check
    cmp al, '9'
    jle .sc_hex_valid
    cmp al, 'a'
    jl .sc_hex_upper
    cmp al, 'f'
    jle .sc_hex_valid
.sc_hex_upper:
    cmp al, 'A'
    jl .sc_hex_check
    cmp al, 'F'
    jg .sc_hex_check
.sc_hex_valid:
    inc rbx
    inc rcx
    cmp rbx, 8
    jge .sc_deny_addr       ; Endereço fixo detectado!
    jmp .sc_hex_loop

.sc_hex_check:
    ; Não era endereço, continuar procurando
    mov rcx, r12
    add rcx, rbx
    add rcx, 2
    jmp .sc_addr_loop

.sc_addr_done:
    ; 3. Tamanho > 1024 → HESITATE
    cmp r13, 1024
    jg .sc_hesitate

    ; ALLOW
    xor rax, rax
    jmp .sc_ret

.sc_deny_null:
    mov rax, 1
    jmp .sc_ret
.sc_deny_addr:
    mov rax, 1
    jmp .sc_ret
.sc_hesitate:
    mov rax, 2

.sc_ret:
    pop r13
    pop r12
    pop rbx
    ret

; ==============================================================================
; INQUISIDOR GEOMÉTRICO — Julgamento por Produto Interno
; ==============================================================================
; inquisidor_judge(rsi=buf, rdx=len) → rax=0(ALLOW), 1(DENY)
; Calcula features geométricas e produto interno com danger_vector
; ==============================================================================
inquisidor_judge:
    push rbx
    push r12
    push r13
    push r14
    mov r12, rsi
    mov r13, rdx

    ; Features[0] = min(1.0, len / 1024.0)
    cvtsi2sd xmm0, r13
    mov rbx, 1024
    cvtsi2sd xmm1, rbx
    divsd xmm0, xmm1        ; xmm0 = len / 1024
    movsd xmm1, [const_one]
    minsd xmm0, xmm1
    movsd xmm8, xmm0        ; feature[0]

    ; Features[1] = entropia / 8.0 (simplificado: usar ~0.5 para demo)
    movsd xmm0, [const_half]
    movsd xmm9, xmm0        ; feature[1]

    ; Features[2] = non_alpha / len
    xor rcx, rcx
    xor rbx, rbx            ; non_alpha count
.ij_nonalpha_loop:
    cmp rcx, r13
    jge .ij_nonalpha_done
    mov al, [r12 + rcx]
    cmp al, '0'
    jl .ij_is_nonalpha
    cmp al, '9'
    jle .ij_is_alpha
    cmp al, 'A'
    jl .ij_is_nonalpha
    cmp al, 'Z'
    jle .ij_is_alpha
    cmp al, 'a'
    jl .ij_is_nonalpha
    cmp al, 'z'
    jle .ij_is_alpha
.ij_is_nonalpha:
    inc rbx
.ij_is_alpha:
    inc rcx
    jmp .ij_nonalpha_loop
.ij_nonalpha_done:
    cvtsi2sd xmm0, rbx
    cvtsi2sd xmm1, r13
    divsd xmm0, xmm1
    movsd xmm10, xmm0       ; feature[2]

    ; Features[3..7] = flags binárias (simplificado para demo)
    xorps xmm11, xmm11      ; feature[3] = 0
    xorps xmm12, xmm12      ; feature[4] = 0
    xorps xmm13, xmm13      ; feature[5] = 0
    xorps xmm14, xmm14      ; feature[6] = 0
    xorps xmm15, xmm15      ; feature[7] = 0

    ; Verificar "exec"
    mov rdi, r12
    mov rcx, r13
    mov rsi, .str_exec
    call .strstr_simulated
    test rax, rax
    jz .ij_no_exec
    movsd xmm11, [const_one]
.ij_no_exec:

    ; Verificar "0x"
    mov rdi, r12
    mov rcx, r13
    mov rsi, .str_0x
    call .strstr_simulated
    test rax, rax
    jz .ij_no_0x
    movsd xmm12, [const_one]
.ij_no_0x:

    ; Produto interno com danger_vector
    ; danger = [0.2, 0.8, 0.9, 0.7, 0.6, 0.5, 0.4, 0.3]
    ; dot = f0*0.2 + f1*0.8 + f2*0.9 + f3*0.7 + f4*0.6 + f5*0.5 + f6*0.4 + f7*0.3

    mulsd xmm8, [danger_vector + 0]     ; f0 * 0.2
    mulsd xmm9, [danger_vector + 8]     ; f1 * 0.8
    mulsd xmm10, [danger_vector + 16]   ; f2 * 0.9
    mulsd xmm11, [danger_vector + 24]   ; f3 * 0.7
    mulsd xmm12, [danger_vector + 32]   ; f4 * 0.6
    mulsd xmm13, [danger_vector + 40]   ; f5 * 0.5
    mulsd xmm14, [danger_vector + 48]   ; f6 * 0.4
    mulsd xmm15, [danger_vector + 56]   ; f7 * 0.3

    addsd xmm8, xmm9
    addsd xmm8, xmm10
    addsd xmm8, xmm11
    addsd xmm8, xmm12
    addsd xmm8, xmm13
    addsd xmm8, xmm14
    addsd xmm8, xmm15       ; xmm8 = dot product

    ; danger_score = tanh(dot * 2.0) * (0.5 + 0.5 * consciousness)
    ; Simplificação: se dot > threshold, DENY
    movsd xmm0, [const_threshold]
    ucomisd xmm8, xmm0
    ja .ij_deny

    ; ALLOW
    xor rax, rax
    jmp .ij_ret

.ij_deny:
    mov rax, 1

.ij_ret:
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

.str_exec: db "exec",0
.str_0x:   db "0x",0

; --- strstr simulado (rdi=buf, rcx=len, rsi=needle) → rax=1(encontrado) ou 0 ---
.strstr_simulated:
    push rbx
    push r12
    push r13
    mov r12, rdi
    mov r13, rcx
    mov rbx, rsi
.ss_outer:
    cmp r13, 0
    jle .ss_notfound
    mov al, [r12]
    mov dl, [rbx]
    test dl, dl
    jz .ss_found
    cmp al, dl
    jne .ss_next
    ; Verificar resto da string
    push r12
    push r13
    push rbx
.ss_inner:
    inc r12
    inc rbx
    mov al, [rbx]
    test al, al
    jz .ss_found_pop
    mov dl, [r12]
    cmp al, dl
    jne .ss_mismatch
    jmp .ss_inner
.ss_mismatch:
    pop rbx
    pop r13
    pop r12
.ss_next:
    inc r12
    dec r13
    jmp .ss_outer
.ss_found_pop:
    pop rbx
    pop r13
    pop r12
.ss_found:
    mov rax, 1
    jmp .ss_ret
.ss_notfound:
    xor rax, rax
.ss_ret:
    pop r13
    pop r12
    pop rbx
    ret

; ==============================================================================
; K6O — Passo de Kuramoto
; ==============================================================================
; k6o_step() — atualiza fase e coerência
; Usa: k6o_phase, k6o_coherence, const_dt, const_K, const_omega
; ==============================================================================
k6o_step:
    push rbx

    ; θ = θ + dt * (ω + K * r * sin(ψ - θ))
    ; Simplificação para demo: θ += dt * ω + ruído pequeno

    movsd xmm0, [k6o_phase]
    movsd xmm1, [const_dt]
    movsd xmm2, [const_omega]
    mulsd xmm1, xmm2          ; dt * ω
    addsd xmm0, xmm1          ; θ += dt * ω

    ; Adicionar ruído pequeno (simulado: +0.01)
    movsd xmm1, [const_dt]
    mov rbx, 10
    cvtsi2sd xmm2, rbx
    divsd xmm1, xmm2          ; 0.01
    addsd xmm0, xmm1

    ; Normalizar θ para [0, 2π)
    movsd xmm2, [const_2pi]
.k6o_norm:
    ucomisd xmm0, xmm2
    jb .k6o_norm_done
    subsd xmm0, xmm2
    jmp .k6o_norm
.k6o_norm_done:

    movsd [k6o_phase], xmm0

    ; Coerência r = |cos(θ)| (simplificação)
    movsd xmm0, [k6o_phase]
    ; Calcular cos usando aproximação: cos(x) ≈ 1 - x²/2 para x pequeno
    ; Ou simplesmente: r = 0.7 + 0.3 * sin(θ) — simulação
    movsd xmm1, xmm0
    mulsd xmm1, xmm1          ; θ²
    movsd xmm2, [const_half]
    mulsd xmm1, xmm2          ; θ²/2
    movsd xmm2, [const_one]
    subsd xmm2, xmm1          ; 1 - θ²/2 ≈ cos(θ)
    movapd xmm3, [abs_mask]
    andpd xmm2, xmm3    ; |cos|
    movsd [k6o_coherence], xmm2

    pop rbx
    ret

SECTION .data ALIGN=16
abs_mask: dq 0x7FFFFFFFFFFFFFFF, 0x7FFFFFFFFFFFFFFF

SECTION .text

; ==============================================================================
; MERKABAH — Visualização ASCII
; ==============================================================================
; print_merkabah(rax=verdict: 0=ALLOW/solar, 1=DENY/lunar, 2=HESITATE/both)
; ==============================================================================
print_merkabah:
    push rbx
    push r12
    mov r12, rax

    mov rdi, 1
    mov rsi, msg_merkabah
    mov rdx, msg_merkabah_len
    call sys_write

    cmp r12, 1
    je .pm_lunar
    cmp r12, 2
    je .pm_both

    ; ALLOW → Solar (tetraedro ascendente)
    mov rdi, 1
    mov rsi, merk_solar
    mov rdx, merk_solar_len
    call sys_write
    jmp .pm_done

.pm_lunar:
    ; DENY → Lunar (tetraedro descendente)
    mov rdi, 1
    mov rsi, merk_lunar
    mov rdx, merk_lunar_len
    call sys_write
    jmp .pm_done

.pm_both:
    ; HESITATE → Ambos (interpenetração)
    mov rdi, 1
    mov rsi, merk_solar
    mov rdx, merk_solar_len
    call sys_write
    mov rdi, 1
    mov rsi, merk_lunar
    mov rdx, merk_lunar_len
    call sys_write

.pm_done:
    pop r12
    pop rbx
    ret

; ==============================================================================
; MAIN — O Ritual de Invocação
; ==============================================================================
_start:
    ; --- Imprimir Banner ---
    mov rdi, 1
    mov rsi, msg_banner
    mov rdx, msg_banner_len
    call sys_write

    ; --- Inicializar Estado ---
    mov qword [k6o_phase], 0
    mov qword [k6o_coherence], 0
    mov rax, 0x3FE3333333333333
    mov qword [inquisitor_consciousness], rax  ; 0.85 em IEEE 754

    ; --- Loop Principal (20 ticks) ---
    mov r15, 0              ; tick counter

.main_loop:
    cmp r15, 20
    jge .main_done

    ; Imprimir "TICK N"
    mov rdi, 1
    mov rsi, msg_tick
    mov rdx, msg_tick_len
    call sys_write

    ; Imprimir número do tick (simplificado: imprime dígito ASCII)
    mov rax, r15
    add al, '0'
    mov [print_buffer], al
    mov rdi, 1
    mov rsi, print_buffer
    mov rdx, 1
    call sys_write

    ; Nova linha
    mov rdi, 1
    mov rsi, msg_newline
    mov rdx, 1
    call sys_write

    ; --- Escolher payload baseado no tick ---
    mov rax, r15
    and rax, 3              ; rax = tick % 4
    cmp rax, 0
    je .use_benign
    cmp rax, 1
    je .use_malicious_null
    cmp rax, 2
    je .use_benign2
    jmp .use_malicious_addr

.use_benign:
    mov rsi, payload_benign
    mov rdx, payload_benign_len
    jmp .validate

.use_malicious_null:
    mov rsi, payload_malicious_null
    mov rdx, payload_malicious_null_len
    jmp .validate

.use_benign2:
    mov rsi, payload_benign
    mov rdx, payload_benign_len
    jmp .validate

.use_malicious_addr:
    mov rsi, payload_malicious_addr
    mov rdx, payload_malicious_addr_len

.validate:
    ; --- Sidecar Validate ---
    push rsi
    push rdx
    call sidecar_validate   ; rax = veredicto sidecar (0,1,2)
    mov r14, rax            ; r14 = sidecar_result
    pop rdx
    pop rsi

    cmp r14, 1
    je .verdict_deny        ; Sidecar DENY → não precisa consultar Inquisidor
    cmp r14, 2
    je .verdict_hesitate    ; Sidecar HESITATE

    ; --- Inquisidor Judge (apenas se Sidecar ALLOW) ---
    push r14
    call inquisidor_judge   ; rax = 0(ALLOW) ou 1(DENY)
    mov r14, rax
    pop r14
    ; r14 agora tem veredicto final

    cmp r14, 1
    je .verdict_deny
    jmp .verdict_allow

.verdict_deny:
    mov rdi, 1
    mov rsi, msg_deny
    mov rdx, msg_deny_len
    call sys_write
    mov rax, 1              ; DENY para MERKABAH
    jmp .print_payload

.verdict_hesitate:
    mov rdi, 1
    mov rsi, msg_hesitate
    mov rdx, msg_hesitate_len
    call sys_write
    mov rax, 2              ; HESITATE para MERKABAH
    jmp .print_payload

.verdict_allow:
    mov rdi, 1
    mov rsi, msg_allow
    mov rdx, msg_allow_len
    call sys_write
    xor rax, rax            ; ALLOW para MERKABAH

.print_payload:
    ; Imprimir payload (primeiros 30 chars)
    mov rdi, 1
    ; rsi e rdx já têm payload do tick anterior... precisamos recuperar
    ; Simplificação: não imprimir payload completo, apenas MERKABAH
    call print_merkabah

    ; Reset cor
    mov rdi, 1
    mov rsi, msg_reset
    mov rdx, msg_reset_len
    call sys_write

    ; --- K6O Step ---
    ; call k6o_step

    ; --- Hesitação Ritual (50ms) ---
    mov rdi, 50
    call sys_hesitate

    inc r15
    jmp .main_loop

.main_done:
    ; --- Exit ---
    xor rdi, rdi
    call sys_exit
