#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include "catedral/dbus_interface.h"
#include "catedral/quantum_scheduler.h"
#include "catedral/hardware.h"

void* resource_monitor_thread(void* arg) {
    while(1) {
        // Simular variação de coerência
        double c = 0.95;
        adjust_priority_by_coherence(getpid(), c);
        sleep(60);
    }
    return NULL;
}

int main() {
    printf("╔════════════════════════════════════════════════════╗\n");
    printf("║     CATEDRAL ARKHE(N) — LINUX DAEMON v2.7         ║\n");
    printf("╚════════════════════════════════════════════════════╝\n");

    dbus_service_init();

    pthread_t monitor;
    pthread_create(&monitor, NULL, resource_monitor_thread, NULL);

    printf("[DAEMON] Ativo e escutando...\n");

    // Loop principal
    while(1) {
        dbus_service_dispatch();
        sleep(1);
    }

    dbus_service_cleanup();
    return 0;
}
