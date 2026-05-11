#ifndef ARKHE_HARDWARE_H
#define ARKHE_HARDWARE_H

#include <stdint.h>
#include <stddef.h>

// QRNG Interface
typedef enum {
    QRNG_MODE_STANDARD,
    QRNG_MODE_BELL_VERIFIED,
    QRNG_MODE_PHYSICAL_CRYSTAL
} qrng_mode_t;

int hardware_qrng_init(qrng_mode_t mode);
int hardware_qrng_get_bytes(uint8_t* buffer, size_t length);
void hardware_qrng_cleanup(void);

// Cryostat Interface
typedef struct {
    float temperature_k;
    float pressure_mbar;
    float helium_level_pct;
    int stability_locked;
} cryo_status_t;

int hardware_cryo_init(void);
int hardware_cryo_get_status(cryo_status_t* status);
int hardware_cryo_set_target_temp(float temp_k);
void hardware_cryo_cleanup(void);

#endif // ARKHE_HARDWARE_H
