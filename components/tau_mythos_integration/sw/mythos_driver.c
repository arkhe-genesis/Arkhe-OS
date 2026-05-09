#include "mythos_driver.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <poll.h>
#include <errno.h>
#include <math.h>

int mythos_init(mythos_t *dev, const char *uio_dev) {
    dev->uio_fd = open(uio_dev, O_RDWR);
    if (dev->uio_fd < 0) return -1;

    dev->map_size = 0x1000;
    dev->regs = mmap(NULL, dev->map_size, PROT_READ | PROT_WRITE, MAP_SHARED, dev->uio_fd, 0);
    if (dev->regs == MAP_FAILED) return -1;

    dev->irq_fd = dev->uio_fd;
    return 0;
}

void mythos_close(mythos_t *dev) {
    munmap((void*)dev->regs, dev->map_size);
    close(dev->uio_fd);
}

void mythos_start(mythos_t *dev, uint32_t loop_count) {
    dev->regs[MYTHOS_REG_LOOP / 4] = loop_count;
    dev->regs[MYTHOS_REG_CTRL / 4] |= (MYTHOS_CTRL_START | MYTHOS_CTRL_IRQ_EN);
}

int mythos_wait_done(mythos_t *dev, int timeout_ms) {
    struct pollfd pfd = { .fd = dev->irq_fd, .events = POLLIN };
    int ret = poll(&pfd, 1, timeout_ms);
    if (ret > 0 && (pfd.revents & POLLIN)) {
        uint32_t count;
        read(dev->irq_fd, &count, sizeof(count));
        uint32_t enable = 1;
        write(dev->irq_fd, &enable, sizeof(enable));
        return 0;
    }
    return -1;
}

float mythos_read_norm(mythos_t *dev) {
    uint32_t raw = dev->regs[MYTHOS_REG_NORM / 4];
    return sqrtf((float)raw); // norm_reg stores sum of squares
}

void mythos_soft_reset(mythos_t *dev) {
    dev->regs[MYTHOS_REG_CTRL / 4] |= MYTHOS_CTRL_RESET;
    usleep(1000);
    dev->regs[MYTHOS_REG_CTRL / 4] &= ~MYTHOS_CTRL_RESET;
}
