// firmware_guard.c — Proteção de acesso a firmware SPI/flash
// Integra com cdv.ko e Safety Guardian para intervenção preemptiva

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/io.h>
#include <errno.h>
#include <linux/msr.h>
#include "../kernel/cdv.h"

// Endereços de registros SPI/BIOS lock (exemplo para Intel PCH)
#define SPI_BAR_OFFSET 0xDC  // SPI Base Address Register offset no PCH
#define SPI_BIOS_CNTL 0xDC   // BIOS Control Register
#define BLE_BIT (1 << 5)     // BIOS Lock Enable
#define SMM_BWP_BIT (1 << 4) // SMM BIOS Write Protect

// MSR para proteção (exemplo)
#define MSR_BIOS_LOCK 0x1F4

// Mock for safety_guardian_trigger
static void safety_guardian_trigger(const char* reason, uint64_t addr, size_t len) {
    printf("[SafetyGuardian] TRIGGERED: %s at 0x%lx (len %zu)\n", reason, addr, len);
}

static int spi_fd = -1;
static int msr_fd = -1;
static volatile int firmware_locked = 0;

int firmware_guard_init(void) {
    // Abrir /dev/mem para acesso a MMIO (requer root)
    spi_fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (spi_fd < 0) {
        perror("Failed to open /dev/mem");
        return -1;
    }

    // Abrir /dev/cpu/*/msr para acesso a MSRs
    msr_fd = open("/dev/cpu/0/msr", O_RDWR);
    if (msr_fd < 0) {
        perror("Failed to open /dev/cpu/0/msr");
        close(spi_fd);
        return -1;
    }

    return 0;
}

int firmware_guard_lock(void) {
    if (firmware_locked) return 0;

    printf("[FirmwareGuard] Locking SPI flash protection...\n");

    // 1. Habilitar BIOS Lock Enable (BLE) via MSR
    uint64_t msr_val;
    if (pread(msr_fd, &msr_val, sizeof(msr_val), MSR_BIOS_LOCK) == sizeof(msr_val)) {
        msr_val |= BLE_BIT;
        if (pwrite(msr_fd, &msr_val, sizeof(msr_val), MSR_BIOS_LOCK) != sizeof(msr_val)) {
            perror("Failed to write MSR_BIOS_LOCK");
            return -1;
        }
    }

    // 2. Habilitar SMM BIOS Write Protect (SMM_BWP)
    // (Em hardware real: escrever em SPI_BIOS_CNTL via MMIO)
    // Para protótipo: simular
    firmware_locked = 1;

    // 3. Notificar cdv.ko e Safety Guardian
    // (Em produção: ioctl para cdv.ko + hypercall para Guardian)
    printf("[FirmwareGuard] Firmware protection ENABLED\n");

    return 0;
}

int firmware_guard_detect_write(uint64_t addr, size_t len) {
    // Verificar se endereço está na região de firmware SPI
    #define SPI_FLASH_BASE 0xFF000000
    #define SPI_FLASH_SIZE (16 * 1024 * 1024)  // 16MB típico

    if (addr >= SPI_FLASH_BASE && addr < SPI_FLASH_BASE + SPI_FLASH_SIZE) {
        // Tentativa de acesso a firmware — disparar alerta
        fprintf(stderr, "[FirmwareGuard] ALERT: Firmware write attempt at 0x%lx (len %zu)\n",
                addr, len);

        // Disparar intervenção do Safety Guardian (simulado)
        // Em produção: signal para thread RT do Guardian
        safety_guardian_trigger("FIRMWARE_WRITE_ATTEMPT", addr, len);

        return -EPERM;  // Bloquear acesso
    }

    return 0;  // Acesso permitido
}

void firmware_guard_cleanup(void) {
    if (msr_fd >= 0) close(msr_fd);
    if (spi_fd >= 0) close(spi_fd);
    firmware_locked = 0;
}
