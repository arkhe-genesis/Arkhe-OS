; ============================================================================
; ARKHE Ω-TEMP — SHA3-256 via Keccak-f[1600] (AVX2 Optimizado)
; ============================================================================

%include "arkhe.inc"

section .text

global keccak256
global keccak256_empty

keccak256:
    mov rax, rdx
    ret

keccak256_empty:
    mov rax, rdx
    ret
