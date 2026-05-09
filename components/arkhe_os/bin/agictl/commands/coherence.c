/* bin/agictl/commands/coherence.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <linux/agi.h>
#include "../../utils/syscall_wrapper.h"
#include "../../utils/output_formatter.h"
#include "../../utils/fixed_point.h"

static struct option coherence_options[] = {
    {"pid", required_argument, 0, 'p'},
    {"target", required_argument, 0, 't'},
    {"metrics", no_argument, 0, 'm'},
    {0, 0, 0, 0}
};

int cmd_coherence(int argc, char **argv, int verbose, const char *format, const char *output_file)
{
    int opt, option_index = 0;
    pid_t pid = 0;  /* 0 = current process */
    __u32 target_coh = 0;
    int get_metrics = 0;
    int operation = AGI_COH_GET;

    while ((opt = getopt_long(argc, argv, "p:t:m", coherence_options, &option_index)) != -1) {
        switch (opt) {
        case 'p':
            pid = atoi(optarg);
            break;
        case 't':
            target_coh = q16_16_parse(optarg);
            operation = AGI_COH_SET_TARGET;
            break;
        case 'm':
            get_metrics = 1;
            operation = AGI_COH_GET_METRICS;
            break;
        case '?':
            return 1;
        }
    }

    struct agi_coherence_args args = {
        .pid = pid,
        .operation = operation,
        .coherence_value = target_coh,
        .flags = 0,
    };

    int ret = agi_syscall_coherence(&args);
    if (ret < 0) {
        fprintf(stderr, "Error: coherence syscall failed: %s\n", strerror(-ret));
        return 1;
    }

    /* Format and output results */
    if (operation == AGI_COH_GET_METRICS) {
        struct agi_coherence_metrics *metrics = (void *)&args;
        return format_coherence_metrics(metrics, format, output_file, verbose);
    } else {
        return format_coherence_value(args.coherence_value, format, output_file, verbose);
    }
}
