; ═══════════════════════════════════════════════════════════════════════════════
; INVOKE ALPHA NEXUS v2.0 — Substrato 651
; Submete um problema formal (Lean) ao agente AlphaProof Nexus e valida a prova.
; Correções: verificação de misformalização, fallback para agente B, logging
;            de custo no rollup 641.
;
; Input:  rdi = serv_id ("alpha-nexus")
;         rsi = ponteiro para o arquivo Lean
;         rdx = tamanho do arquivo
;         rcx = buffer para a prova retornada
;         r8  = agent_config (1=A, 2=B, 3=C, 4=D, 0=auto)
; Output: rax = 0 se resolvido, -1 se falhou, -2 se misformalização detectada
;         xmm0 = Φ_proof (0.0 a 1.0)
; ═══════════════════════════════════════════════════════════════════════════════
invoke_alpha_nexus:
    push rbp
    mov rbp, rsp
    sub rsp, 64

    ; Salvar argumentos
    mov [rbp-8], rdi
    mov [rbp-16], rsi
    mov [rbp-24], rdx
    mov [rbp-32], rcx
    mov [rbp-40], r8

    ; 1. Verificar se o problema foi revisado por matemático (flag no header)
    mov rdi, [rbp-16]
    call check_formalization_review
    test eax, eax
    jz .misformalization_detected

    ; 2. Selecionar agente (auto = D para problemas de pesquisa, B para rotina)
    mov r8, [rbp-40]
    test r8, r8
    jnz .agent_selected
    mov r8, 4                    ; Default: Agent D (full)
.agent_selected:

    ; 3. Escrever o arquivo Lean no sysfs input do Serv
    lea rdi, [alpha_nexus_input_path]
    mov rsi, [rbp-16]
    mov rdx, [rbp-24]
    call write_sysfs_file

    ; 4. Escrever configuração do agente
    lea rdi, [alpha_nexus_config_path]
    mov rsi, r8
    call write_sysfs_int

    ; 5. Invocar o Serv
    lea rdi, [alpha_nexus_invoke_path]
    mov esi, ignite_cmd
    mov edx, 1
    call write_sysfs_file

    ; 6. Aguardar resultado com timeout (3000 episódios ≈ 48h max)
    xor r12, r12                 ; contador de polls
.poll:
    lea rdi, [alpha_nexus_status_path]
    call read_sysfs_int
    cmp eax, 2                   ; verified
    je .verified
    cmp eax, 3                   ; failed
    je .failed
    cmp eax, 4                   ; misformalization
    je .misformalization_detected

    ; Timeout check
    inc r12
    cmp r12, 172800000           ; 48h em ms (poll a cada 1ms)
    jge .failed

    ; Yield
    call sched_yield
    jmp .poll

.verified:
    ; 7. Ler a prova (resultado)
    lea rdi, [alpha_nexus_result_path]
    mov rsi, [rbp-32]            ; buffer de saída
    mov edx, 65536
    call read_sysfs_file

    ; 8. Verificar a prova com Quantum Verifier (637)
    mov rdi, [rbp-16]            ; problema original
    mov rsi, [rbp-32]            ; prova
    call invoke_quantum_verifier_637
    test eax, eax
    jz .failed

    ; 9. Registrar custo no rollup (641)
    call read_sysfs_cost
    mov rdi, rax
    call log_cost_to_rollup_641

    ; 10. Anchor na Akashic (649)
    mov rdi, [rbp-16]            ; problem hash
    mov rsi, [rbp-32]            ; proof hash
    call anchor_to_akashic_649

    ; 11. Retornar sucesso com Φ_proof = 1.0
    movsd xmm0, [phi_proof_one]
    xor eax, eax
    jmp .done

.misformalization_detected:
    mov eax, -2
    movsd xmm0, [phi_proof_zero]
    jmp .done

.failed:
    mov eax, -1
    movsd xmm0, [phi_proof_zero]

.done:
    leave
    ret

section .rodata
alpha_nexus_input_path:  db "/sys/arkhe/serv/alpha-nexus/input", 0
alpha_nexus_config_path: db "/sys/arkhe/serv/alpha-nexus/config", 0
alpha_nexus_invoke_path: db "/sys/arkhe/serv/alpha-nexus/invoke", 0
alpha_nexus_status_path: db "/sys/arkhe/serv/alpha-nexus/status", 0
alpha_nexus_result_path: db "/sys/arkhe/serv/alpha-nexus/result", 0
phi_proof_one:         dq 1.0
phi_proof_zero:        dq 0.0
ignite_cmd:            db "IGNITE", 0
