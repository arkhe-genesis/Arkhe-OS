/* bin/agictl/main.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <linux/agi.h>
#include "utils/syscall_wrapper.h"
#include "utils/output_formatter.h"

#define VERSION "1.0.0"
#define PROG_NAME "agictl"

static struct option long_options[] = {
    {"help", no_argument, 0, 'h'},
    {"version", no_argument, 0, 'v'},
    {"verbose", no_argument, 0, 'V'},
    {"format", required_argument, 0, 'f'},
    {"output", required_argument, 0, 'o'},
    {0, 0, 0, 0}
};

static void print_usage(void)
{
    printf("Usage: %s [OPTIONS] <command> [command-options]\n", PROG_NAME);
    printf("\nAGI SovereignCLI — Interface for AGI kernel subsystem\n\n");
    printf("Commands:\n");
    printf("  infer      Execute retrocausal inference\n");
    printf("  coherence  Query or update process coherence (Φ_C)\n");
    printf("  identity   Sovereign identity operations\n");
    printf("  evolve     Trigger architecture evolution\n");
    printf("  federate   Federated consensus operations\n");
    printf("  config     Configuration management\n");
    printf("\nOptions:\n");
    printf("  -h, --help           Show this help message\n");
    printf("  -v, --version        Show version information\n");
    printf("  -V, --verbose        Enable verbose output\n");
    printf("  -f, --format FORMAT  Output format: text, json, table (default: text)\n");
    printf("  -o, --output FILE    Write output to file instead of stdout\n");
    printf("\nExamples:\n");
    printf("  %s coherence get --pid=1234\n", PROG_NAME);
    printf("  %s infer --graph=1 --target=0.95 --observable=alignment\n", PROG_NAME);
    printf("  %s identity sign --input=state.json --output=proof.sig\n", PROG_NAME);
}

int main(int argc, char **argv)
{
    int opt, option_index = 0;
    int verbose = 0;
    char *format = "text";
    char *output_file = NULL;

    while ((opt = getopt_long(argc, argv, "hvVf:o:", long_options, &option_index)) != -1) {
        switch (opt) {
        case 'h':
            print_usage();
            return 0;
        case 'v':
            printf("%s version %s\n", PROG_NAME, VERSION);
            return 0;
        case 'V':
            verbose = 1;
            break;
        case 'f':
            format = optarg;
            break;
        case 'o':
            output_file = optarg;
            break;
        case '?':
            print_usage();
            return 1;
        }
    }

    if (optind >= argc) {
        fprintf(stderr, "Error: No command specified\n\n");
        print_usage();
        return 1;
    }

    const char *command = argv[optind];

    /* Dispatch to command handler */
    int ret;
    if (strcmp(command, "infer") == 0) {
        ret = cmd_infer(argc - optind, argv + optind, verbose, format, output_file);
    } else if (strcmp(command, "coherence") == 0) {
        ret = cmd_coherence(argc - optind, argv + optind, verbose, format, output_file);
    } else if (strcmp(command, "identity") == 0) {
        ret = cmd_identity(argc - optind, argv + optind, verbose, format, output_file);
    } else if (strcmp(command, "evolve") == 0) {
        ret = cmd_evolve(argc - optind, argv + optind, verbose, format, output_file);
    } else if (strcmp(command, "federate") == 0) {
        ret = cmd_federate(argc - optind, argv + optind, verbose, format, output_file);
    } else if (strcmp(command, "config") == 0) {
        ret = cmd_config(argc - optind, argv + optind, verbose, format, output_file);
    } else {
        fprintf(stderr, "Error: Unknown command '%s'\n\n", command);
        print_usage();
        return 1;
    }

    return ret;
}
