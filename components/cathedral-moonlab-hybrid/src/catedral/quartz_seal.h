#ifndef QUARTZ_SEAL_H
#define QUARTZ_SEAL_H

#include <stdint.h>
#include <stddef.h>

#define SEAL_SIZE 32

int generate_quartz_seal(const char* operation_name,
                         const uint8_t* operation_data, size_t data_len,
                         uint8_t* output_seal);

int verify_quartz_seal(const uint8_t* expected_seal,
                       const char* operation_name,
                       const uint8_t* operation_data, size_t data_len);

#endif // QUARTZ_SEAL_H
