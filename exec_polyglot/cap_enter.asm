; exec_polyglot/cap_enter.asm
; NASM syntax for x86_64 FreeBSD
; Invokes cap_enter() syscall and prints success message.

section .data
    msg db '🔩 Assembly: cap_enter() invoked successfully', 0xa
    len equ $ - msg

section .text
    global _start

_start:
    ; syscall cap_enter (number 516 on FreeBSD)
    mov rax, 516
    syscall

    ; write message to stdout
    mov rax, 1          ; sys_write (Linux) / on FreeBSD write is 4, Linux is 1
    mov rdi, 1          ; stdout
    mov rsi, msg
    mov rdx, len
    syscall

    ; exit(0)
    mov rax, 60          ; sys_exit (Linux 60)
    xor rdi, rdi
    syscall