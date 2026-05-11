section .text
global arkhe_crc32c

arkhe_crc32c:
    xor eax, eax
    test rsi, rsi
    jz .done
.loop:
    crc32 eax, byte [rdi]
    inc rdi
    dec rsi
    jnz .loop
.done:
    ret
