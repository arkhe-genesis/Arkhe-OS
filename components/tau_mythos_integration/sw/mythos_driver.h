#ifndef MYTHOS_DRIVER_H
#define MYTHOS_DRIVER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// Register Map (Aligned with RTL)
#define MYTHOS_REG_CTRL     0x00
#define MYTHOS_REG_LOOP     0x04
#define MYTHOS_REG_STATUS   0x08
#define MYTHOS_REG_DEBUG    0x10
#define MYTHOS_REG_NORM     0x14

#define MYTHOS_CTRL_START   (1 << 0)
#define MYTHOS_CTRL_RESET   (1 << 1)
#define MYTHOS_CTRL_IRQ_EN  (1 << 2)

#define MYTHOS_D_MODEL 256

typedef struct {
    int uio_fd;
    int irq_fd;
    volatile uint32_t *regs;
    size_t map_size;
} mythos_t;

int  mythos_init(mythos_t *dev, const char *uio_dev);
void mythos_close(mythos_t *dev);
void mythos_start(mythos_t *dev, uint32_t loop_count);
int  mythos_wait_done(mythos_t *dev, int timeout_ms);
float mythos_read_norm(mythos_t *dev);
void mythos_soft_reset(mythos_t *dev);

#endif
