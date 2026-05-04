// arkhe_sensor.bpf.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("tracepoint/syscalls/sys_enter_write")
int bpf_prog(void *ctx) {
    char msg[] = "Arkhe coherence event\n";
    bpf_trace_printk(msg, sizeof(msg));
    return 0;
}

char _license[] SEC("license") = "GPL";
