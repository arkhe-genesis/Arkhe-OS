#ifndef DBUS_INTERFACE_H
#define DBUS_INTERFACE_H

int dbus_service_init(void);
void dbus_service_dispatch(void);
void dbus_service_cleanup(void);

#endif
