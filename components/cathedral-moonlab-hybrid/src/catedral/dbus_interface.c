#include <stdio.h>
#include <stdlib.h>
#include "dbus_interface.h"

int dbus_service_init(void) {
    printf("[DBUS] Inicializando barramento org.arkhe.Cathedral...\n");
    return 0;
}

void dbus_service_dispatch(void) {
    // Mock dispatch
}

void dbus_service_cleanup(void) {
    printf("[DBUS] Finalizando barramento.\n");
}
