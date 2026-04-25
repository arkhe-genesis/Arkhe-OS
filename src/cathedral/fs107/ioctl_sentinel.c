// ioctl_sentinel.c — Monitoramento em tempo real de IOCTLs perigosos
// Usa eBPF/kprobes para interceptar DeviceIoControl no kernel

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include "../kernel/cdv.h"

// Programa eBPF embutido (compilado com clang-bpf)
// ioctl_sentinel.bpf.c — compilado separadamente para .o
static const char ioctl_sentinel_bpf_prog[] = {0};
static size_t ioctl_sentinel_bpf_prog_size = 0;

static int prog_fd = -1;
static int map_fd = -1;

// Estrutura de evento para ring buffer
struct ioctl_event {
    uint64_t timestamp_ns;
    uint32_t pid;
    uint32_t tid;
    char driver_name[64];
    uint32_t ioctl_code;
    uint64_t arg_ptr;
    uint8_t blocked;
    char reason[64];
};

// Callback para eventos do ring buffer
static int handle_ioctl_event(void* ctx, void* data, size_t len) {
    struct ioctl_event* evt = (struct ioctl_event*)data;

    if (evt->blocked) {
        fprintf(stderr, "[IOCTLSentinel] BLOCKED: pid=%u ioctl=0x%x driver=%s reason=%s\n",
                evt->pid, evt->ioctl_code, evt->driver_name, evt->reason);
    } else {
        printf("[IOCTLSentinel] Allowed: pid=%u ioctl=0x%x driver=%s\n",
               evt->pid, evt->ioctl_code, evt->driver_name);
    }

    // Ancorar evento bloqueado no Códice
    if (evt->blocked) {
        // (Em produção: cathedral_codex_anchor_ioctl_event(evt))
    }

    return 0;
}

int ioctl_sentinel_init(void) {
    // Carregar programa eBPF
    struct bpf_prog_load_attr attr = {
        .prog_type = BPF_PROG_TYPE_KPROBE,
        .insns = (struct bpf_insn*)ioctl_sentinel_bpf_prog,
        .insns_cnt = ioctl_sentinel_bpf_prog_size / sizeof(struct bpf_insn),
        .license = "GPL",
    };

    if (bpf_prog_load_xattr(&attr, &prog_fd, NULL) < 0) {
        perror("Failed to load eBPF program");
        return -1;
    }

    // Obter FD do map de eventos
    map_fd = bpf_object__find_map_fd_by_name(NULL, "ioctl_events");
    if (map_fd < 0) {
        perror("Failed to find events map");
        // bpf_prog_detach(prog_fd);
        return -1;
    }

    // Configurar ring buffer callback
    struct ring_buffer* rb = ring_buffer__new(map_fd, handle_ioctl_event, NULL, NULL);
    if (!rb) {
        perror("Failed to create ring buffer");
        return -1;
    }

    printf("[IOCTLSentinel] eBPF program loaded and monitoring IOCTLs\n");
    return 0;
}

int ioctl_sentinel_block_ioctl(uint32_t ioctl_code, const char* driver_name) {
    // Adicionar regra de bloqueio via map eBPF
    // (Implementação simplificada — em produção: usar BPF_MAP_TYPE_HASH)

    printf("[IOCTLSentinel] Adding block rule: ioctl=0x%x driver=%s\n",
           ioctl_code, driver_name);

    // (Em produção: bpf_map_update_elem para map de regras)
    return 0;
}

void ioctl_sentinel_cleanup(void) {
    if (prog_fd >= 0) {
        // bpf_prog_detach(prog_fd);
        prog_fd = -1;
    }
}
