#ifndef LFIR_CORE_H
#define LFIR_CORE_H

/* Mock implementation for LFIR core */
#define EXPORT __attribute__((visibility("default")))

double config_get_double(const char *config_path, const char *key, double default_val);

#endif
