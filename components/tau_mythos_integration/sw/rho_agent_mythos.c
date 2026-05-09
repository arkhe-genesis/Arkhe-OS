#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <time.h>
#include "mythos_driver.h"

// --- Estruturas e Definições ---

typedef struct {
    uint32_t flags;
    float x, y, z;
} roi_packet_t;

#define FLAG_RED_DOMINANT 0x01
#define FLAG_HIGH_INTENSITY 0x02

#define ANOMALY_BUFFER_SIZE 32
#define NORM_CURIOSITY_THRESHOLD 70.0f
#define NORM_DIVERGENCE_THRESHOLD 80.0f

// Limiar de momento linear (em unidades Q8.8 ou float simulado)
#define KINETIC_MOMENTUM_THRESHOLD 2.0f

typedef struct {
    int16_t embedding[MYTHOS_D_MODEL];
    float latent_norm;
    roi_packet_t roi_data;
} anomaly_sample_t;

typedef struct {
    float last_x, last_y, last_z;
    double last_timestamp;
} cluster_history_t;

static anomaly_sample_t anomaly_buffer[ANOMALY_BUFFER_SIZE];
static int anomaly_idx = 0;
static float global_latent_norm = 0.0f;

// --- Helpers ---

long long get_timestamp_ms() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}

int get_sector(const roi_packet_t *pkt) {
    // Divisão simples em 8 setores baseada em coordenadas
    int sector = 0;
    if (pkt->x > 0) sector |= 1;
    if (pkt->y > 0) sector |= 2;
    if (pkt->z > 0) sector |= 4;
    return sector;
}

float get_current_latent_norm() {
    return global_latent_norm;
}

float calculate_cluster_momentum(const roi_packet_t *pkt, const cluster_history_t *history) {
    if (history->last_timestamp == 0) return 0.0f;

    float dx = pkt->x - history->last_x;
    float dy = pkt->y - history->last_y;
    float dz = pkt->z - history->last_z;
    float dist = sqrtf(dx*dx + dy*dy + dz*dz);

    double dt = (get_timestamp_ms() - history->last_timestamp) / 1000.0;
    if (dt <= 0) return 0.0f;

    // Velocidade = dist / dt.
    // Momentum = m * v. Assumindo massa unitária para ROI simplificado.
    return dist / (float)dt;
}

// --- Comunicação (Simulada) ---

void firebase_publish(const char *path, const char *json_str) {
    // Placeholder para publicação real no Firebase
    printf("[RHO->EOLUS] Publicando em %s: %s\n", path, json_str);
}

void publish_phantom_to_eolus(const roi_packet_t *pkt, const cluster_history_t *history) {
    char path[128];
    long long ts = get_timestamp_ms();
    snprintf(path, sizeof(path), "/environment/phantoms/%lld", ts);

    char json[512];
    snprintf(json, sizeof(json),
             "{\"sector\":%d, \"norm\":%.2f, \"x\":%.2f, \"y\":%.2f, \"z\":%.2f, \"timestamp\":%.3f}",
             get_sector(pkt), get_current_latent_norm(), pkt->x, pkt->y, pkt->z, ts / 1000.0);

    firebase_publish(path, json);
}

void firebase_publish_anomaly_batch(anomaly_sample_t *buffer, int size) {
    printf("[RHO] Lote de %d anomalias enviado para a Forja (simulado).\n", size);
}

// --- Lógica Principal ---

void check_and_store_anomaly(const int16_t *embedding, float norm, const roi_packet_t *pkt) {
    if (norm > NORM_CURIOSITY_THRESHOLD && norm < NORM_DIVERGENCE_THRESHOLD) {
        anomaly_buffer[anomaly_idx].latent_norm = norm;
        memcpy(anomaly_buffer[anomaly_idx].embedding, embedding, MYTHOS_D_MODEL * sizeof(int16_t));
        memcpy(&anomaly_buffer[anomaly_idx].roi_data, pkt, sizeof(roi_packet_t));

        anomaly_idx = (anomaly_idx + 1) % ANOMALY_BUFFER_SIZE;

        if (anomaly_idx == 0) {
            firebase_publish_anomaly_batch(anomaly_buffer, ANOMALY_BUFFER_SIZE);
        }
    }
}

bool should_invoke_mythos(const roi_packet_t *pkt, const cluster_history_t *history) {
    int danger_score = 0;
    if (pkt->flags & FLAG_RED_DOMINANT) danger_score += 3;
    if (pkt->flags & FLAG_HIGH_INTENSITY) danger_score += 2;
    if (pkt->z < 5.0f) danger_score += 5;

    float momentum = calculate_cluster_momentum(pkt, history);

    if (momentum > KINETIC_MOMENTUM_THRESHOLD) {
        // Alvo com intenção de deslocamento -> Canal Principal (Mythos Tático)
        return (danger_score >= 8);
    } else {
        // "Hálito" ambiental -> Encaminhar para Éolo (Firebase)
        publish_phantom_to_eolus(pkt, history);
        return false; // Não aciona o Mythos para isto
    }
}

int main() {
    mythos_t mythos;
    // Tenta inicializar o hardware (simulado ou real)
    if (mythos_init(&mythos, "/dev/uio2") < 0) {
        fprintf(stderr, "[RHO] Aviso: Falha ao iniciar Mythos Core hardware. Usando modo simulação.\n");
    }

    printf("[RHO] Agente Mythos (com Poda Seletiva) Iniciado.\n");

    cluster_history_t history = {0};

    while (1) {
        // Simula a chegada de um ROI
        roi_packet_t pkt = { .flags = FLAG_RED_DOMINANT, .x = 10.0, .y = 0.0, .z = 4.0 };

        // Simula movimento para teste de momentum (velocidade crescente)
        static float velocity = 0.0f;
        static float pos_x = 10.0f;
        pos_x += velocity;
        pkt.x = pos_x;
        velocity += 0.1f;
        // Limita velocidade para o loop de teste
        if (velocity > 10.0f) {
            velocity = 0.0f;
            pos_x = 10.0f;
        }

        int16_t simulated_embedding[MYTHOS_D_MODEL] = {0};

        if (should_invoke_mythos(&pkt, &history)) {
            printf("[RHO] ROI Crítico detectado (Momentum: %.2f). Invocando Mythos...\n",
                   calculate_cluster_momentum(&pkt, &history));

            mythos_start(&mythos, 8);
            if (mythos_wait_done(&mythos, 100) == 0) {
                global_latent_norm = mythos_read_norm(&mythos);
                printf("[RHO] Mythos concluiu. Norma latente: %.2f\n", global_latent_norm);

                check_and_store_anomaly(simulated_embedding, global_latent_norm, &pkt);

                if (global_latent_norm > 50.0f) {
                    printf("[RHO] ALERTA: Colisão iminente detectada!\n");
                }
            } else {
                printf("[RHO] Timeout ou Erro no Mythos Core.\n");
            }
        } else {
            // Se não invocou Mythos, pode ter sido podado para o Éolo
        }

        // Atualiza histórico para o próximo ciclo
        history.last_x = pkt.x;
        history.last_y = pkt.y;
        history.last_z = pkt.z;
        history.last_timestamp = (double)get_timestamp_ms();

        sleep(1);
    }

    mythos_close(&mythos);
    return 0;
}
