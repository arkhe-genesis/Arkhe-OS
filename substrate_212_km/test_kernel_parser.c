/*
 * test_kernel_parser.c — User-space test for ARKHE Kernel COBOL Parser
 * Substrate: 212-KM
 * Compile: gcc -o test_kernel_parser test_kernel_parser.c
 * Run: sudo ./test_kernel_parser
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <errno.h>
#include "arkhe_cobol_parser.h"

#define DEVICE_PATH "/dev/arkhe_cobol"

static int fd = -1;

int open_device(void) {
    fd = open(DEVICE_PATH, O_RDWR);
    if (fd < 0) {
        perror("Failed to open device");
        return -1;
    }
    printf("✅ Device opened: %s\n", DEVICE_PATH);
    return 0;
}

void close_device(void) {
    if (fd >= 0) {
        close(fd);
        printf("✅ Device closed\n");
    }
}

int test_parse_basic(void) {
    struct arkhe_cobol_request req;
    memset(&req, 0, sizeof(req));

    const char *source =
        "IDENTIFICATION DIVISION.\n"
        "PROGRAM-ID. TESTPROG.\n"
        "PROCEDURE DIVISION.\n"
        "    DISPLAY 'HELLO KERNEL'.\n"
        "    STOP RUN.\n"
        "END PROGRAM TESTPROG.";

    req.caller_pid = getpid();
    req.caller_ring = ARKHE_RING0_KERNEL;
    req.source_len = strlen(source);
    strncpy(req.source_fragment, source, ARKHE_MAX_FRAGMENT - 1);

    printf("\n🧪 Test 1: Basic Parse\n");
    if (ioctl(fd, ARKHE_IOCTL_PARSE, &req) < 0) {
        perror("ioctl PARSE failed");
        return -1;
    }

    printf("   Status: %s\n", req.status == 0 ? "OK" : "ERROR");
    printf("   Program ID: %s\n", req.program_id);
    printf("   Φ_C Score: %.4f\n", req.phi_c_score);
    printf("   CICS: %u, IMS: %u, DB2: %u\n", req.cics_count, req.ims_count, req.db2_count);
    printf("   Violations: %u, Tokens: %u\n", req.violation_count, req.token_count);
    printf("   Execution cycles: %llu ns\n", (unsigned long long)req.execution_cycles);
    printf("   ✅ PASS\n");
    return 0;
}

int test_parse_cics(void) {
    struct arkhe_cobol_request req;
    memset(&req, 0, sizeof(req));

    const char *source =
        "IDENTIFICATION DIVISION.\n"
        "PROGRAM-ID. CICSPROG.\n"
        "PROCEDURE DIVISION.\n"
        "    EXEC CICS READ FILE('ACCTFILE') RIDFLD('001') INTO(WS-AREA) END-EXEC.\n"
        "    EXEC CICS WRITEQ TD QUEUE('LOGQ') FROM(WS-AREA) END-EXEC.\n"
        "    EXEC CICS RETURN END-EXEC.\n"
        "END PROGRAM CICSPROG.";

    req.caller_pid = getpid();
    req.caller_ring = ARKHE_RING0_KERNEL;
    req.source_len = strlen(source);
    strncpy(req.source_fragment, source, ARKHE_MAX_FRAGMENT - 1);

    printf("\n🧪 Test 2: CICS Transactions\n");
    if (ioctl(fd, ARKHE_IOCTL_PARSE, &req) < 0) {
        perror("ioctl PARSE failed");
        return -1;
    }

    printf("   CICS transactions: %u\n", req.cics_count);
    for (unsigned int i = 0; i < req.cics_count; i++) {
        printf("   [%u] Command: %u, Resource: %s, Line: %u\n",
               i, req.cics_txns[i].command, req.cics_txns[i].resource,
               req.cics_txns[i].line_number);
    }
    printf("   ✅ PASS\n");
    return 0;
}

int test_security_scan(void) {
    struct arkhe_cobol_request req;
    memset(&req, 0, sizeof(req));

    const char *source =
        "IDENTIFICATION DIVISION.\n"
        "PROGRAM-ID. BADPROG.\n"
        "PROCEDURE DIVISION.\n"
        "    ALTER MAIN-LOGIC TO PROCEED TO EXIT.\n"
        "    GO TO DEPENDING ON WS-FLAG A, B, C.\n"
        "    EXEC CICS READ FILE('X') INTO(Y) END-EXEC.\n"
        "END PROGRAM BADPROG.";

    req.caller_pid = getpid();
    req.caller_ring = ARKHE_RING0_KERNEL;
    req.source_len = strlen(source);
    strncpy(req.source_fragment, source, ARKHE_MAX_FRAGMENT - 1);

    printf("\n🧪 Test 3: Security Scan\n");
    if (ioctl(fd, ARKHE_IOCTL_SECURITY_SCAN, &req) < 0) {
        perror("ioctl SECURITY_SCAN failed");
        return -1;
    }

    printf("   Violations: %u\n", req.violation_count);
    printf("   Φ_C Score: %.4f\n", req.phi_c_score);
    for (unsigned int i = 0; i < req.violation_count; i++) {
        printf("   [%u] Type: 0x%02x, Severity: %u, Impact: %.2f\n",
               i, req.violations[i].violation_type,
               req.violations[i].severity,
               req.violations[i].phi_c_impact);
    }
    printf("   ✅ PASS\n");
    return 0;
}

int test_permission_denied(void) {
    struct arkhe_cobol_request req;
    memset(&req, 0, sizeof(req));

    const char *source =
        "IDENTIFICATION DIVISION.\n"
        "PROGRAM-ID. USERPROG.\n"
        "PROCEDURE DIVISION.\n"
        "    STOP RUN.\n"
        "END PROGRAM USERPROG.";

    req.caller_pid = getpid();
    req.caller_ring = ARKHE_RING3_USER;  /* User space! */
    req.source_len = strlen(source);
    strncpy(req.source_fragment, source, ARKHE_MAX_FRAGMENT - 1);

    printf("\n🧪 Test 4: Permission Denied (RING3)\n");
    if (ioctl(fd, ARKHE_IOCTL_PARSE, &req) < 0) {
        perror("ioctl PARSE failed");
        return -1;
    }

    printf("   Status: %d (expected -2 = PERMISSION_DENIED)\n", req.status);
    printf("   %s\n", req.status == -2 ? "✅ PASS" : "❌ FAIL");
    return req.status == -2 ? 0 : -1;
}

int test_kernel_stats(void) {
    struct arkhe_kernel_stats stats;
    memset(&stats, 0, sizeof(stats));

    printf("\n🧪 Test 5: Kernel Stats\n");
    if (ioctl(fd, ARKHE_IOCTL_KERNEL_STATS, &stats) < 0) {
        perror("ioctl KERNEL_STATS failed");
        return -1;
    }

    printf("   Substrate: %s\n", stats.substrate_id);
    printf("   Kernel Φ_C: %.4f\n", stats.kernel_phi_c);
    printf("   Uptime: %llu seconds\n", (unsigned long long)stats.uptime_seconds);
    printf("   Memory: %u/%u pages allocated\n", stats.allocated_pages, stats.total_pages);
    printf("   Interrupts: %u raised, %u handled\n", stats.interrupts_raised, stats.interrupts_handled);
    printf("   Syscalls: %u total, %llu cycles\n", stats.total_syscalls, (unsigned long long)stats.total_syscall_cycles);
    printf("   Bus: %u channels, %llu messages\n", stats.bus_channels, (unsigned long long)stats.bus_messages);
    printf("   ✅ PASS\n");
    return 0;
}

int test_bus_v3(void) {
    struct arkhe_bus_message msg;

    printf("\n🧪 Test 6: Bus V3 Communication\n");

    /* Publish */
    memset(&msg, 0, sizeof(msg));
    strncpy(msg.channel_name, "cics_transactions", 31);
    msg.sender_pid = getpid();
    strncpy(msg.sender_substrate, "212-TEST", 15);
    strncpy(msg.payload, "command=READ,file=TEST,line=42", ARKHE_MAX_BUS_MSG - 1);
    msg.payload_len = strlen(msg.payload);

    if (ioctl(fd, ARKHE_IOCTL_BUS_PUBLISH, &msg) < 0) {
        perror("ioctl BUS_PUBLISH failed");
        return -1;
    }
    printf("   Published message ID: %u\n", msg.msg_id);

    /* Consume */
    memset(&msg, 0, sizeof(msg));
    strncpy(msg.channel_name, "cics_transactions", 31);

    if (ioctl(fd, ARKHE_IOCTL_BUS_CONSUME, &msg) < 0) {
        perror("ioctl BUS_CONSUME failed");
        return -1;
    }
    printf("   Consumed message ID: %u\n", msg.msg_id);
    printf("   Payload: %s\n", msg.payload);
    printf("   ✅ PASS\n");
    return 0;
}

int main(void) {
    int passed = 0;
    int total = 6;

    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║  ARKHE OS — Kernel COBOL Parser Test Suite                 ║\n");
    printf("║  Substrate: 212-KM                                         ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");

    if (open_device() < 0) {
        printf("\n❌ Cannot open device. Is the module loaded?\n");
        printf("   Run: sudo insmod arkhe_cobol_parser.ko\n");
        return 1;
    }

    if (test_parse_basic() == 0) passed++;
    if (test_parse_cics() == 0) passed++;
    if (test_security_scan() == 0) passed++;
    if (test_permission_denied() == 0) passed++;
    if (test_kernel_stats() == 0) passed++;
    if (test_bus_v3() == 0) passed++;

    close_device();

    printf("\n╔══════════════════════════════════════════════════════════════╗\n");
    printf("║  RESULT: %d/%d tests passed (%.0f%%)                              ║\n",
           passed, total, (float)passed / total * 100);
    printf("╚══════════════════════════════════════════════════════════════╝\n");

    return passed == total ? 0 : 1;
}