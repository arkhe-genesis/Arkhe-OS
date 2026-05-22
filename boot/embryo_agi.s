// boot/embryo_agi.s
// Embrião AGI em assembly (100 KB) - Architecture: AArch64
.global _start
.section .text

_start:
    // Initialize stack pointer
    ldr x0, =stack_top
    mov sp, x0

    // Set up basic vector table
    bl setup_vectors

    // Jump to C ignition sequence (boot_v2_ignition)
    bl boot_v2_ignition

hang:
    wfe
    b hang

setup_vectors:
    // Stub vector table setup
    ret

.section .bss
.align 4
stack_bottom:
    .space 4096
stack_top:
