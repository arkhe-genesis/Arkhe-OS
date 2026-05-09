#ifndef CATHEDRAL_CONSENT_H
#define CATHEDRAL_CONSENT_H

#include <stddef.h>

/**
 * Mock implementation of Cathedral Consent SDK
 */

static inline int cathedral_consent_request(const char* action, const char* resource, char* out_consent_id, size_t id_len) {
    if (out_consent_id && id_len >= 36) {
        // Mock UUID
        for (int i = 0; i < 35; i++) out_consent_id[i] = '0';
        out_consent_id[35] = '\0';
        return 0;
    }
    return -1;
}

#endif // CATHEDRAL_CONSENT_H
