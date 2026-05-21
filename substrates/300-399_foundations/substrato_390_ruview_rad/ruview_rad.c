/*
 * ruview_rad.c — Detetor de Partículas baseado em ath10k Spectral Scan
 * Compilação: gcc -O2 -o ruview_rad ruview_rad.c -lm -lreadline
 * Execução: sudo ./ruview_rad --iface wlan0 --threshold 10.0
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <math.h>
#include <time.h>

#define SPECTRAL_FFT_BINS 256
#define DEFAULT_RELAY_PATH "/sys/kernel/debug/ieee80211/phy0/ath10k/spectral_scan0"
#define DEFAULT_THRESHOLD 10.0
#define CORRELATION_WINDOW_NS 500000000L  // 500 ms

struct ath10k_fft_sample {
    uint64_t timestamp;    // ns
    uint16_t center_freq;  // MHz
    uint16_t channel_width;
    uint8_t  bins[SPECTRAL_FFT_BINS]; // magnitude bins
};

static volatile sig_atomic_t running = 1;

void sig_handler(int sig) {
    running = 0;
}

// Detetor de pico linear (rápido, para streaming)
int detect_peak(struct ath10k_fft_sample *s, double threshold) {
    double sum = 0.0, max_val = 0.0;
    for (int i = 0; i < SPECTRAL_FFT_BINS; i++) {
        sum += s->bins[i];
        if (s->bins[i] > max_val) max_val = s->bins[i];
    }
    double avg = sum / SPECTRAL_FFT_BINS;
    return (max_val > avg * threshold);
}

// Classificador simples: baseado na largura do pico
const char *classify_peak(struct ath10k_fft_sample *s) {
    int above_half = 0;
    double max_val = 0.0;
    for (int i = 0; i < SPECTRAL_FFT_BINS; i++) if (s->bins[i] > max_val) max_val = s->bins[i];
    double half_max = max_val * 0.5;
    for (int i = 0; i < SPECTRAL_FFT_BINS; i++) if (s->bins[i] > half_max) above_half++;
    if (above_half < 5) return "MUON";
    else if (above_half < 20) return "ELECTRON";
    else return "PHOTON";
}

int main(int argc, char *argv[]) {
    const char *relay_path = DEFAULT_RELAY_PATH;
    double threshold = DEFAULT_THRESHOLD;
    struct timespec ts;

    // Processar argumentos
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--iface") == 0 && i+1 < argc) {
            char tmp[256];
            snprintf(tmp, sizeof(tmp), "/sys/kernel/debug/ieee80211/%s/ath10k/spectral_scan0", argv[i+1]);
            relay_path = strdup(tmp);
            i++;
        } else if (strcmp(argv[i], "--threshold") == 0 && i+1 < argc) {
            threshold = atof(argv[i+1]);
            i++;
        }
    }

    int fd = open(relay_path, O_RDONLY | O_NONBLOCK);
    if (fd < 0) {
        perror("open relayfs");
        return 1;
    }

    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    printf("=== RuView‑RAD Particle Detector ===\n");
    printf("Listening on: %s\nThreshold: %.2f\n", relay_path, threshold);
    printf("Timestamp (ns), Peak Ratio, Max Bin, Classification\n");

    struct ath10k_fft_sample sample;
    struct ath10k_fft_sample last_event = {0};
    uint64_t last_event_ns = 0;
    int event_count = 0;

    while (running) {
        ssize_t n = read(fd, &sample, sizeof(sample));
        if (n == sizeof(sample)) {
            if (detect_peak(&sample, threshold)) {
                // Correlação temporal: ignorar eventos muito próximos (pós‑disparo)
                if (sample.timestamp - last_event_ns < CORRELATION_WINDOW_NS)
                    continue;

                last_event_ns = sample.timestamp;
                memcpy(&last_event, &sample, sizeof(sample));
                event_count++;

                double sum = 0.0, max_val = 0.0;
                for (int i = 0; i < SPECTRAL_FFT_BINS; i++) {
                    sum += sample.bins[i];
                    if (sample.bins[i] > max_val) max_val = sample.bins[i];
                }
                double avg = sum / SPECTRAL_FFT_BINS;
                double ratio = max_val / avg;
                const char *classification = classify_peak(&sample);

                printf("%llu, %.2f, %.0f, %s\n",
                       (unsigned long long)sample.timestamp,
                       ratio, max_val, classification);
                fflush(stdout);
            }
        } else if (errno != EAGAIN) {
            break;
        } else {
            usleep(100);
        }
    }

    close(fd);
    printf("\nTotal events detected: %d\n", event_count);
    return 0;
}