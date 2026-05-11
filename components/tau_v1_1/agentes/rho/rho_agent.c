// ============================================================================
// rho_agent.c
// Agente de Percepção TAU - Leitor de ROI via mmap e IRQ
// Executa no ARM Cortex-A72 do Versal (Linux)
// ============================================================================

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <signal.h>
#include <stdint.h>
#include <string.h>
#include <poll.h>

// ----------------------------------------------------------------------------
// Configurações de Hardware (devem casar com o design RTL)
// ----------------------------------------------------------------------------
#define DDR_ROI_BASE_ADDR   0x40000000  // Endereço físico mapeado pelo NoC
#define ROI_BUFFER_SIZE     (4 * 1024 * 1024) // 4 MB
#define ROI_PACKET_SIZE     8           // 64 bits = 8 bytes

// Estrutura de um pacote ROI (conforme VRP v1.1)
typedef struct __attribute__((packed)) {
    uint16_t x;
    uint16_t y;
    uint16_t z;
    uint8_t  flags;        // [7:4] reservado, [3] high_intensity, [2:0] r,g,b dominant
    uint8_t  intensity_hi; // byte alto da intensidade (8 bits)
} roi_packet_t;

// Flags
#define FLAG_RED_DOMINANT   0x01
#define FLAG_GREEN_DOMINANT 0x02
#define FLAG_BLUE_DOMINANT  0x04
#define FLAG_HIGH_INTENSITY 0x08

// ----------------------------------------------------------------------------
// UIO para interrupção (assumindo que o PL IRQ está mapeado em /dev/uio0)
// ----------------------------------------------------------------------------
#define UIO_DEVICE "/dev/uio0"

// ----------------------------------------------------------------------------
// Protótipos Firebase (simplificado - use libcurl ou similar em produção)
// ----------------------------------------------------------------------------
void firebase_publish_roi(const roi_packet_t *pkt);

// ----------------------------------------------------------------------------
// Variáveis Globais
// ----------------------------------------------------------------------------
static volatile int keep_running = 1;
static uint8_t *roi_buffer_virt = NULL;
static uint32_t read_ptr = 0;      // gerenciado por hardware ou software?
static uint32_t write_ptr = 0;     // tipicamente atualizado pelo VRP/NOC

// Tratamento de sinal para saída limpa
void int_handler(int dummy) {
    keep_running = 0;
}

// ----------------------------------------------------------------------------
// Mapear a DDR do NoC
// ----------------------------------------------------------------------------
int map_roi_buffer() {
    int mem_fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (mem_fd < 0) {
        perror("open /dev/mem");
        return -1;
    }

    roi_buffer_virt = (uint8_t*) mmap(NULL, ROI_BUFFER_SIZE, PROT_READ, MAP_SHARED,
                                       mem_fd, DDR_ROI_BASE_ADDR);
    close(mem_fd);

    if (roi_buffer_virt == MAP_FAILED) {
        perror("mmap");
        return -1;
    }
    printf("[RHO] Buffer ROI mapeado em 0x%lx\n", (unsigned long)roi_buffer_virt);
    return 0;
}

// ----------------------------------------------------------------------------
// Tratamento de Interrupção (via UIO)
// ----------------------------------------------------------------------------
void uio_irq_handler(int uio_fd) {
    uint32_t irq_count;
    // Ler o contador de interrupções do UIO (4 bytes no offset 0)
    if (read(uio_fd, &irq_count, sizeof(irq_count)) != sizeof(irq_count)) {
        perror("read uio");
        return;
    }
    printf("[RHO] IRQ recebida! Contador: %u\n", irq_count);

    // Aqui leríamos o write_ptr do hardware para saber quantos pacotes novos existem.
    // Exemplo: write_ptr = *(volatile uint32_t*)(roi_buffer_virt + OFFSET_WRITE_PTR);
    // Para este esqueleto, vamos apenas drenar todos os pacotes pendentes.

    // Nesta implementação, o hardware gerencia um ring buffer com ponteiros.
    // Assumimos que o VRP escreve sequencialmente e o read_ptr é mantido em software.
    // Na prática, você pode ter registradores AXI4-Lite para os ponteiros.

    // Por simplicidade, vamos ler até encontrar um pacote com flags=0 (sentinel).
    roi_packet_t pkt;
    while (1) {
        // Copia um pacote do buffer (cuidado com wrap-around)
        memcpy(&pkt, roi_buffer_virt + read_ptr, ROI_PACKET_SIZE);

        // Se o pacote é um sentinela (dados zerados), paramos
        if (pkt.x == 0 && pkt.y == 0 && pkt.z == 0 && pkt.flags == 0 && pkt.intensity_hi == 0) {
            break;
        }

        // Processa o pacote
        printf("[RHO] ROI: (%d,%d,%d) flags=0x%02x\n", pkt.x, pkt.y, pkt.z, pkt.flags);
        firebase_publish_roi(&pkt);

        // Avança o ponteiro de leitura (com wrap)
        read_ptr = (read_ptr + ROI_PACKET_SIZE) % ROI_BUFFER_SIZE;
    }

    // Opcional: escrever o novo read_ptr de volta para o hardware
    // *(volatile uint32_t*)(roi_buffer_virt + OFFSET_READ_PTR) = read_ptr;

    // Reabilita a interrupção escrevendo 1 no UIO
    uint32_t enable = 1;
    if (write(uio_fd, &enable, sizeof(enable)) != sizeof(enable)) {
        perror("write uio");
    }
}

// ----------------------------------------------------------------------------
// Publicação no Firebase (simulação via cURL)
// ----------------------------------------------------------------------------
void firebase_publish_roi(const roi_packet_t *pkt) {
    // Construir JSON
    char json[256];
    snprintf(json, sizeof(json),
             "{\"agent\":\"RHO\",\"type\":\"roi\",\"x\":%d,\"y\":%d,\"z\":%d,"
             "\"flags\":%d,\"intensity_hi\":%d}",
             pkt->x, pkt->y, pkt->z, pkt->flags, pkt->intensity_hi);

    // Em produção, use libcurl para enviar para Firebase RTDB
    // curl -X POST -d '...' https://<seu-projeto>.firebaseio.com/vacuum/roi.json
    // Por enquanto, apenas imprime
    printf("[RHO] Firebase: %s\n", json);
}

// ----------------------------------------------------------------------------
// Função Principal
// ----------------------------------------------------------------------------
int main(int argc, char *argv[]) {
    printf("[RHO] Agente de Percepção TAU iniciando...\n");

    signal(SIGINT, int_handler);
    signal(SIGTERM, int_handler);

    // 1. Mapear buffer ROI
    if (map_roi_buffer() < 0) {
        return 1;
    }

    // 2. Abrir dispositivo UIO para IRQ
    int uio_fd = open(UIO_DEVICE, O_RDWR);
    if (uio_fd < 0) {
        perror("open UIO");
        munmap(roi_buffer_virt, ROI_BUFFER_SIZE);
        return 1;
    }

    // 3. Loop principal: aguarda interrupções
    struct pollfd fds = { .fd = uio_fd, .events = POLLIN };
    while (keep_running) {
        int ret = poll(&fds, 1, 1000); // timeout 1s
        if (ret < 0) {
            if (keep_running) perror("poll");
            break;
        } else if (ret > 0 && (fds.revents & POLLIN)) {
            uio_irq_handler(uio_fd);
        }
    }

    printf("[RHO] Encerrando...\n");
    close(uio_fd);
    munmap(roi_buffer_virt, ROI_BUFFER_SIZE);
    return 0;
}
