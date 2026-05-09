/* bin/agimon/main.c */
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <linux/agi.h>
#include "collectors/coherence_collector.h"
#include "exporters/prometheus_exporter.h"
#include "exporters/terminal_renderer.h"
#include "alerting/threshold_monitor.h"

#define DEFAULT_INTERVAL_MS 1000
#define DEFAULT_PROMETHEUS_PORT 9090

static volatile sig_atomic_t running = 1;

static void signal_handler(int sig)
{
    if (sig == SIGINT || sig == SIGTERM) {
        running = 0;
    }
}

static void print_usage(const char *prog)
{
    printf("Usage: %s [OPTIONS]\n", prog);
    printf("\nAGI CoherenceObserver — Real-time coherence monitoring\n\n");
    printf("Options:\n");
    printf("  -i, --interval MS    Collection interval in milliseconds (default: %d)\n", DEFAULT_INTERVAL_MS);
    printf("  -p, --prometheus PORT Enable Prometheus exporter on port (default: %d)\n", DEFAULT_PROMETHEUS_PORT);
    printf("  -t, --tui            Enable terminal UI mode\n");
    printf("  -c, --config FILE    Configuration file path\n");
    printf("  -v, --verbose        Enable verbose output\n");
    printf("  -h, --help           Show this help message\n");
}

int main(int argc, char **argv)
{
    int interval_ms = DEFAULT_INTERVAL_MS;
    int prometheus_port = 0;  /* 0 = disabled */
    int enable_tui = 0;
    char *config_file = NULL;
    int verbose = 0;

    /* Parse command line options */
    /* ... (getopt parsing) ... */

    /* Setup signal handlers */
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    /* Initialize collectors */
    struct coherence_collector *coh_collector = coherence_collector_init();
    if (!coh_collector) {
        fprintf(stderr, "Failed to initialize coherence collector\n");
        return 1;
    }

    /* Initialize exporters */
    struct prometheus_exporter *prom_exporter = NULL;
    if (prometheus_port > 0) {
        prom_exporter = prometheus_exporter_init(prometheus_port);
        if (!prom_exporter) {
            fprintf(stderr, "Failed to initialize Prometheus exporter\n");
            coherence_collector_destroy(coh_collector);
            return 1;
        }
    }

    struct terminal_renderer *tui = NULL;
    if (enable_tui) {
        tui = terminal_renderer_init();
        if (!tui) {
            fprintf(stderr, "Failed to initialize terminal renderer\n");
            if (prom_exporter) prometheus_exporter_destroy(prom_exporter);
            coherence_collector_destroy(coh_collector);
            return 1;
        }
    }

    /* Initialize alerting */
    struct threshold_monitor *alert_monitor = threshold_monitor_init(config_file);
    if (!alert_monitor) {
        fprintf(stderr, "Failed to initialize threshold monitor\n");
        /* Continue without alerting */
    }

    printf("AGI CoherenceObserver started (interval: %dms)\n", interval_ms);

    /* Main monitoring loop */
    while (running) {
        /* Collect coherence metrics */
        struct coherence_metrics_batch *batch = coherence_collector_collect(coh_collector);
        if (!batch) {
            usleep(interval_ms * 1000);
            continue;
        }

        /* Export to Prometheus if enabled */
        if (prom_exporter) {
            prometheus_exporter_export(prom_exporter, batch);
        }

        /* Render to TUI if enabled */
        if (tui) {
            terminal_renderer_update(tui, batch);
        }

        /* Check thresholds and trigger alerts */
        if (alert_monitor) {
            struct alert_list *alerts = threshold_monitor_check(alert_monitor, batch);
            if (alerts && alerts->count > 0) {
                /* Handle alerts (log, notify, etc.) */
                for (int i = 0; i < alerts->count; i++) {
                    fprintf(stderr, "ALERT: %s - %s\n",
                            alerts->alerts[i].name,
                            alerts->alerts[i].message);
                }
                alert_list_free(alerts);
            }
        }

        /* Verbose output to stdout */
        if (verbose) {
            printf("Collected %d coherence metrics\n", batch->count);
            for (int i = 0; i < batch->count; i++) {
                printf("  PID %d: Φ_C = %u.%06u\n",
                       batch->metrics[i].pid,
                       batch->metrics[i].coherence_score >> 16,
                       (batch->metrics[i].coherence_score & 0xFFFF) * 1000000 / 0x10000);
            }
        }

        coherence_metrics_batch_free(batch);
        usleep(interval_ms * 1000);
    }

    printf("Shutting down AGI CoherenceObserver...\n");

    /* Cleanup */
    if (tui) terminal_renderer_destroy(tui);
    if (prom_exporter) prometheus_exporter_destroy(prom_exporter);
    if (alert_monitor) threshold_monitor_destroy(alert_monitor);
    coherence_collector_destroy(coh_collector);

    printf("AGI CoherenceObserver stopped\n");
    return 0;
}
