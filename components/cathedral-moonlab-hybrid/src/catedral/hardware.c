#include "hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// Mock implementation for demo purposes
static qrng_mode_t current_mode = QRNG_MODE_STANDARD;

int hardware_qrng_init(qrng_mode_t mode) {
    printf("[HARDWARE] Initializing Physical QRNG in mode %d...\n", mode);
    current_mode = mode;
    srand(time(NULL));
    return 0;
}

int hardware_qrng_get_bytes(uint8_t* buffer, size_t length) {
    for (size_t i = 0; i < length; i++) {
        buffer[i] = rand() % 256;
    }
    return 0;
}

void hardware_qrng_cleanup(void) {
    printf("[HARDWARE] Physical QRNG cleanup.\n");
}

int hardware_cryo_init(void) {
    printf("[HARDWARE] Initializing Cryostat control system...\n");
    return 0;
}

int hardware_cryo_get_status(cryo_status_t* status) {
    if (!status) return -1;
    status->temperature_k = 4.2f + ((float)rand() / (float)RAND_MAX) * 0.1f;
    status->pressure_mbar = 1013.25f;
    status->helium_level_pct = 85.0f;
    status->stability_locked = 1;
    return 0;
}

int hardware_cryo_set_target_temp(float temp_k) {
    printf("[HARDWARE] Setting Cryostat target temperature to %.3f K\n", temp_k);
    return 0;
}

void hardware_cryo_cleanup(void) {
    printf("[HARDWARE] Cryostat system shutdown.\n");
}
