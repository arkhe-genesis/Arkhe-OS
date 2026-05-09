/* tools/testing/agi/test_agi_core.c */
#include <linux/agi.h>
#include <linux/lfir.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/syscall.h>

/* Test: Basic coherence query */
static int test_coherence_query(void)
{
    struct agi_coherence_args args = {
        .pid = 0,
        .operation = AGI_COH_GET,
    };

    long ret = syscall(__NR_agi_coherence, &args);
    if (ret != 0) {
        fprintf(stderr, "FAIL: coherence query failed: %ld\n", ret);
        return -1;
    }

    printf("PASS: Coherence = %u.%06u\n",
           args.coherence_value >> 16,
           (args.coherence_value & 0xFFFF) * 1000000 / 0x10000);
    return 0;
}

/* Test: Retrocausal inference (classical fallback) */
static int test_retrocausal_inference(void)
{
    const char *observables[] = {"coherence_score", "alignment_consistency"};
    struct agi_weak_value results[2];
    struct agi_infer_args args = {
        .lfir_graph_id = 1,  /* Test graph */
        .target_coherence = 0x0000F000,  /* 0.9375 */
        .observables = (u64)observables,
        .num_observables = 2,
        .flags = AGI_INFER_CLASSICAL,  /* Use classical fallback */
        .result = (u64)results,
    };

    long ret = syscall(__NR_agi_infer, &args);
    if (ret != 2) {
        fprintf(stderr, "FAIL: inference returned %ld, expected 2\n", ret);
        return -1;
    }

    printf("PASS: Inference results:\n");
    for (int i = 0; i < 2; i++) {
        printf("  %s: %lld.%06lld ± %u.%06u\n",
               results[i].observable,
               results[i].real_part >> 32,
               (results[i].real_part & 0xFFFFFFFF) * 1000000ULL >> 32,
               results[i].uncertainty >> 16,
               (results[i].uncertainty & 0xFFFF) * 1000000 / 0x10000);
    }
    return 0;
}

int main(int argc, char **argv)
{
    printf("AGI Kernel Subsystem Tests\n");
    printf("==========================\n\n");

    int failures = 0;

    printf("Test 1: Coherence query... ");
    if (test_coherence_query() != 0) failures++;

    printf("Test 2: Retrocausal inference... ");
    if (test_retrocausal_inference() != 0) failures++;

    printf("\nResults: %d/%d tests passed\n", 2 - failures, 2);
    return failures ? 1 : 0;
}
