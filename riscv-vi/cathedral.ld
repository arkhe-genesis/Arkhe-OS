/* cathedral.ld — Linker script para Catedral RISC-VI */

MEMORY
{
    CODEX_CRYSTAL (rx)  : ORIGIN = 0x00000000, LENGTH = 1024M
    COHERENCE_RAM (rwx) : ORIGIN = 0x40000000, LENGTH = 256M
    QUANTUM_STACK (rw)  : ORIGIN = 0x50000000, LENGTH = 64M
    KNOT_MEMORY (rw)    : ORIGIN = 0x60000000, LENGTH = 1G
    SEAL_STORAGE (rw)   : ORIGIN = 0x70000000, LENGTH = 256M
}

SECTIONS
{
    .text : {
        *(.text._boot_atomic)
        *(.text._ivt)
        *(.text.kernel)
        *(.text*)
    } > CODEX_CRYSTAL

    .rodata : {
        *(.rodata*)
        *(.seal_data*)
    } > CODEX_CRYSTAL

    .data : {
        *(.data*)
        *(.invariance_metrics)
    } > COHERENCE_RAM

    .bss : {
        *(.bss*)
        *(.quantum_states)
    } > QUANTUM_STACK

    .knots : {
        *(.knot_topology*)
    } > KNOT_MEMORY

    .seals : {
        *(.seal_storage*)
    } > SEAL_STORAGE
}
