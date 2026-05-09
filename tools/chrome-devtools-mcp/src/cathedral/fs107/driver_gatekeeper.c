// driver_gatekeeper.c — Daemon userspace que integra com cdv.ko
// Monitora carregamento de drivers e aplica políticas de soberania

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/inotify.h>
#include <errno.h>
#include <pthread.h>
#include <json-c/json.h>

#include "../kernel/cdv.h"
#include "../include/cathedral_consent.h"
#include "../include/cathedral_codex.h"

#define CDV_DEVICE "/dev/cdv0"
#define DRIVER_DIRS {"/lib/modules", "/usr/lib/dkms", "/etc/cathedral/drivers"}
#define POLL_INTERVAL_SEC 5

static int cdv_fd = -1;
static volatile int running = 1;
static pthread_mutex_t policy_mutex = PTHREAD_MUTEX_INITIALIZER;
static uint32_t active_policy = CDV_POLICY_BLOCK_REVOKED | CDV_POLICY_BLOCK_EXPIRED;

// Callback para notificações do kernel
// OBS: Em ambiente real, userspace não chama cdv_register_notifier diretamente.
// Isso exigiria uma interface via netlink, sinal, ou polling em /dev/cdv0.
// Para fins de protótipo FS-107, simulamos o processamento de notificações.
static int cdv_notification_handler_simulated(struct cdv_notification* notif) {
    printf("[Gatekeeper] Notification: %s\n", notif->message);

    // Ancorar receipt no Códice para auditoria
    if (notif->type == CDV_NOTIFY_DRIVER_BLOCKED) {
        json_object* receipt = json_object_new_object();
        json_object_object_add(receipt, "type", json_object_new_string("driver_blocked"));
        json_object_object_add(receipt, "driver_hash",
            json_object_new_string_len((char*)notif->driver_hash, SHA256_DIGEST_SIZE));
        json_object_object_add(receipt, "reason", json_object_new_string(notif->message));
        json_object_object_add(receipt, "timestamp",
            json_object_new_int64(notif->timestamp_ns));

        cathedral_codex_anchor("driver_gatekeeper", receipt);
        json_object_put(receipt);
    }

    return 0;
}

// Thread para monitorar diretórios de drivers via inotify
static void* monitor_driver_dirs(void* arg) {
    int fd = inotify_init1(IN_NONBLOCK);
    if (fd < 0) {
        perror("inotify_init1");
        return NULL;
    }

    // Adicionar watches para diretórios de drivers
    const char* dirs[] = DRIVER_DIRS;
    for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); i++) {
        int wd = inotify_add_watch(fd, dirs[i], IN_CREATE | IN_MODIFY | IN_DELETE);
        if (wd < 0) {
            fprintf(stderr, "Failed to watch %s: %s\n", dirs[i], strerror(errno));
        }
    }

    char buf[4096] __attribute__((aligned(__alignof__(struct inotify_event))));

    while (running) {
        ssize_t len = read(fd, buf, sizeof(buf));
        if (len < 0 && errno != EAGAIN) {
            perror("inotify read");
            break;
        }

        for (char* ptr = buf; ptr < buf + len; ) {
            struct inotify_event* event = (struct inotify_event*)ptr;

            if (event->mask & IN_CREATE) {
                // Novo arquivo criado — verificar se é driver (.ko, .sys)
                if (strstr(event->name, ".ko") || strstr(event->name, ".sys")) {
                    char path[512];
                    // Nota: simplificado para o exemplo
                    snprintf(path, sizeof(path), "%s/%s", "/lib/modules", event->name);

                    // Verificar driver com cdv.ko
                    struct cdv_driver_check_req req = {
                        .policy_flags = active_policy,
                    };
                    strncpy(req.driver_path, path, sizeof(req.driver_path) - 1);

                    // Obter consentimento do usuário (simulado)
                    cathedral_consent_request("driver_load", path, req.consent_id, sizeof(req.consent_id));

                    enum cdv_check_result result;
                    if (ioctl(cdv_fd, CDV_IOC_CHECK_DRIVER, &req) == 0) {
                        // result = *(enum cdv_check_result*)&req; // Unsafe cast in snippet
                        // Em uma implementação real, o resultado viria no corpo da req ou retorno do ioctl
                        printf("[Gatekeeper] Checked driver: %s\n", path);
                    }
                }
            }

            ptr += sizeof(struct inotify_event) + event->len;
        }

        usleep(100000);  // 100ms debounce
    }

    close(fd);
    return NULL;
}

// Thread para polling de estatísticas e health check
static void* health_monitor(void* arg) {
    while (running) {
        struct cdv_stats stats;
        if (ioctl(cdv_fd, CDV_IOC_GET_STATS, &stats) == 0) {
            printf("[Gatekeeper] Stats: %llu checks, %llu blocked, %u cached reps\n",
                   stats.total_checks, stats.blocked_loads, stats.reputation_cache_size);
        }
        sleep(POLL_INTERVAL_SEC);
    }
    return NULL;
}

int main(int argc, char** argv) {
    printf("[Gatekeeper] Cathedral Driver Gatekeeper starting...\n");

    // Abrir dispositivo cdv.ko
    cdv_fd = open(CDV_DEVICE, O_RDWR);
    if (cdv_fd < 0) {
        fprintf(stderr, "Failed to open %s: %s\n", CDV_DEVICE, strerror(errno));
        fprintf(stderr, "Ensure cdv.ko is loaded: sudo insmod cdv.ko\n");
        // return 1; // Permite rodar simulação sem o driver real no sandbox
    }

    // Iniciar threads de monitoramento
    pthread_t monitor_thread, health_thread;
    pthread_create(&monitor_thread, NULL, monitor_driver_dirs, NULL);
    pthread_create(&health_thread, NULL, health_monitor, NULL);

    // Loop principal (aguarda sinais)
    while (running) {
        sleep(1);
        // Em produção: handle SIGHUP para recarregar políticas
    }

    // Cleanup
    running = 0;
    pthread_join(monitor_thread, NULL);
    pthread_join(health_thread, NULL);
    if (cdv_fd >= 0) close(cdv_fd);

    printf("[Gatekeeper] Shutdown complete.\n");
    return 0;
}
