.section .data
msg:
    .ascii "\033[1;35m[CATHEDRAL] Pulsing with 7.83Hz Schumann Resonance...\033[0m\n"
len = . - msg

.section .text
.global _start

_start:
    # write(1, msg, len)
    mov $1, %rax        # syscall: write
    mov $1, %rdi        # fd: stdout
    lea msg(%rip), %rsi # buf
    mov $len, %rdx      # count
    syscall

    # exit(0)
    mov $60, %rax       # syscall: exit
    xor %rdi, %rdi      # status: 0
    syscall
