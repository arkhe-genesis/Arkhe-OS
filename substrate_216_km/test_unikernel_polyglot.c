/*
 * test_unikernel_polyglot.c — User‑space test suite for Uni‑Kernel Polyglot
 * Compile: gcc -o test_unikernel_polyglot test_unikernel_polyglot.c
 * Run: sudo ./test_unikernel_polyglot
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <errno.h>
#include "arkhe_unikernel_polyglot.h"

#define DEVICE_PATH "/dev/arkhe_uni"

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

int test_parse_python(void) {
    struct arkhe_uni_request req;
    memset(&req, 0, sizeof(req));

    const char *source =
        "def secure_function(x):\n"
        "    if x > 0:\n"
        "        return x * 2\n"
        "    return 0\n"
        "\n"
        "# This is a safe function\n";

    req.caller_pid = getpid();
    req.caller_ring = ARKHE_RING0_KERNEL;
    req.language = ARKHE_LANG_PYTHON;
    req.source_len = strlen(source);
    strncpy(req.source_fragment, source, ARKHE_MAX_SOURCE_FRAGMENT - 1);

    printf("\n🧪 Test 1: Python Parse\n");
    if (ioctl(fd, ARKHE_IOCTL_PARSE_LANG, &req) < 0) {
        perror("ioctl PARSE_LANG failed");
        return -1;
    }

    printf("   Detected language: %u\n", req.detected_language);
    printf("   Program name: %s\n", req.program_name);
    printf("   Constructs found: %u\n", req.construct_count);
    printf("   Φ_C Score: %.4f\n", req.phi_c_score);
    printf("   Execution time: %llu ns\n", (unsigned long long)req.parse_time_ns);
    printf("   ✅ PASS\n");
    return 0;
}

int test_security_cobol(void) {
    struct arkhe_uni_request req;
    memset(&req, 0, sizeof(req));
    __u32 i;

    const char *source =
        "IDENTIFICATION DIVISION.\n"
        "PROGRAM-ID. INSECURE.\n"
        "PROCEDURE DIVISION.\n"
        "    ALTER MAIN-LOGIC TO PROCEED TO EXIT.\n"
        "    EXEC CICS READ FILE('ACCT') END-EXEC.\n"
        "END PROGRAM INSECURE.";

    req.caller_pid = getpid();
    req.caller_ring = ARKHE_RING0_KERNEL;
    req.language = ARKHE_LANG_COBOL;
    req.source_len = strlen(source);
    strncpy(req.source_fragment, source, ARKHE_MAX_SOURCE_FRAGMENT - 1);

    printf("\n🧪 Test 2: COBOL Security Scan\n");
    if (ioctl(fd, ARKHE_IOCTL_SECURITY_SCAN_LANG, &req) < 0) {
        perror("ioctl SECURITY_SCAN_LANG failed");
        return -1;
    }

    printf("   Violations: %u\n", req.violation_count);
    printf("   Φ_C Score: %.4f\n", req.phi_c_score);
    for (i = 0; i < req.violation_count; i++) {
        printf("   [%u] Type: 0x%04x, Severity: %u, Impact: %.2f\n",
               i, req.violations[i].violation_type,
               req.violations[i].severity,
               req.violations[i].phi_c_impact);
        printf("        → %s\n", req.violations[i].description);
    }
    printf("   ✅ PASS\n");
    return 0;
}

int test_register_language(void) {
    struct arkhe_lang_registration reg;
    memset(&reg, 0, sizeof(reg));

    strncpy(reg.language_name, "Rust", 31);
    reg.language = ARKHE_LANG_RUST;
    reg.engine_type = ARKHE_ENGINE_TREE_SITTER;
    strncpy(reg.grammar_path, "/lib/grammars/tree-sitter-rust.wasm", 255);
    reg.enabled = 1;

    printf("\n🧪 Test 3: Register Rust Language\n");
    if (ioctl(fd, ARKHE_IOCTL_REGISTER_LANGUAGE, &reg) < 0) {
        perror("ioctl REGISTER_LANGUAGE failed");
        return -1;
    }
    printf("   ✅ Language registered\n");
    return 0;
}

int test_kernel_stats(void) {
    struct arkhe_uni_kernel_stats stats;
    memset(&stats, 0, sizeof(stats));

    printf("\n🧪 Test 4: Kernel Stats\n");
    if (ioctl(fd, ARKHE_IOCTL_UNI_KERNEL_STATS, &stats) < 0) {
        perror("ioctl UNI_KERNEL_STATS failed");
        return -1;
    }

    printf("   Substrate: %s\n", stats.substrate_id);
    printf("   Kernel Φ_C: %.4f\n", stats.kernel_phi_c);
    printf("   Total parses: %u\n", stats.total_parses);
    printf("   Languages registered: %u\n", stats.languages_registered);
    printf("   Constructs extracted: %u\n", stats.constructs_extracted);
    printf("   Tokens generated: %u\n", stats.tokens_generated);
    printf("   ✅ PASS\n");
    return 0;
}

int main(void) {
    int passed = 0;
    int total = 4;

    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║  ARKHE OS — Uni‑Kernel Polyglot Test Suite                ║\n");
    printf("║  Substrate: 216-KM                                         ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");

    if (open_device() < 0) {
        printf("\n❌ Cannot open device. Is the module loaded?\n");
        printf("   Run: sudo insmod arkhe_unikernel_polyglot.ko\n");
        return 1;
    }

    if (test_parse_python() == 0) passed++;
    if (test_security_cobol() == 0) passed++;
    if (test_register_language() == 0) passed++;
    if (test_kernel_stats() == 0) passed++;

    close_device();

    printf("\n╔══════════════════════════════════════════════════════════════╗\n");
    printf("║  RESULT: %d/%d tests passed (%.0f%%)                              ║\n",
           passed, total, (float)passed / total * 100);
    printf("╚══════════════════════════════════════════════════════════════╝\n");

    return passed == total ? 0 : 1;
}
