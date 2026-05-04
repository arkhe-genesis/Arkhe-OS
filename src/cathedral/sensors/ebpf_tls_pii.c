// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

char LICENSE[] SEC("license") = "Dual BSD/GPL";

// Ring Buffer para saída segura para user-space
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 16);
} egress_buf SEC(".maps");

// Mapa de rastreamento de conexões (fd -> ssl pointer)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);
    __type(value, __u64);
} ssl_map SEC(".maps");

// Evento enviado ao user-space
struct tls_event {
    __u64 ts;
    __u32 pid;
    __u32 fd;
    __u16 data_len;
    char data[128]; // Buffer pequeno para inspeção rápida no kernel
    char pii_flags; // Bitmap: 0x01=email, 0x02=cpf, 0x04=credit_card, 0x00=clean
};

// Verificador simplificado de PII no kernel (evita regex pesada no eBPF)
static __always_inline char check_pii_simple(const char *buf, __u16 len) {
    char flags = 0;
    // Heurística rápida: '@' para email, padrões de CPF/CC por comprimento/dígitos
    for (__u16 i = 0; i < len && i < 64; i++) {
        char c = buf[i];
        if (c == '@') flags |= 0x01;
        if (c >= '0' && c <= '9') {
            // Contagem simplificada de dígitos para detecção de padrões
            // Em produção: usar eBPF Bloom Filter ou passar para user-space
        }
    }
    return flags;
}

SEC("uprobe/SSL_write")
int BPF_KPROBE(on_ssl_write, void *ssl, const void *buf, int num) {
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    struct tls_event *e;

    e = bpf_ringbuf_reserve(&egress_buf, sizeof(*e), 0);
    if (!e) return 0;

    e->ts = bpf_ktime_get_ns();
    e->pid = pid;
    e->data_len = (num > 128) ? 128 : num;
    bpf_probe_read_user(e->data, e->data_len, buf); // Φ+: Seguro em user-space
    e->pii_flags = check_pii_simple(e->data, e->data_len); // Ψ+: Detecção rápida

    bpf_ringbuf_submit(e, 0);
    return 0;
}

// URETPOBE para rastrear SSL_free e limpar mapa
SEC("uprobe/SSL_free")
int BPF_KPROBE(on_ssl_free, void *ssl) {
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    bpf_map_delete_elem(&ssl_map, &pid);
    return 0;
}
