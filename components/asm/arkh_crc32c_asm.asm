section .text
global arkhe_crc32c

; uint32_t arkhe_crc32c(const uint8_t *data, size_t len);
; Usa a instrução SSE4.2 CRC32 se disponível.
arkhe_crc32c:
    xor eax, eax                 ; acc = 0
    test rsi, rsi                ; len == 0?
    jz .done
.loop:
    crc32 eax, byte [rdi]        ; acc = _mm_crc32_u8(acc, *data)
    inc rdi
    dec rsi
    jnz .loop
.done:
    ret
