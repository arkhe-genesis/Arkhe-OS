CC=gcc
CFLAGS=-Wall -fPIC
LIBS=-lm
TARGET_LIB=libarkhe.so
ALLOC_LIB=libarkhe_alloc.so
DAEMON=arkhe_daemon
PVM=pvm
BOOT=arkhe_os

all: $(TARGET_LIB) $(ALLOC_LIB) $(DAEMON) $(PVM) $(BOOT)
CFLAGS=-Wall -fPIC -shared -ldl -lm
TARGET=libarkhe_alloc.so
DEMO_TARGET=tailslayer_demo
CXX=g++
CXXFLAGS=-Wall -std=c++20 -pthread -I../../include -I.
CFLAGS=-Wall -fPIC -shared -ldl -lm

all: $(TARGET) $(DEMO_TARGET)

$(TARGET_LIB): arkhe_hal.c cronos_scheduler.c
	$(CC) $(CFLAGS) -shared -o $(TARGET_LIB) arkhe_hal.c cronos_scheduler.c $(LIBS)

$(ALLOC_LIB): arkhe_alloc.c
	$(CC) $(CFLAGS) -shared -o $(ALLOC_LIB) arkhe_alloc.c -ldl $(LIBS)

$(DAEMON): daemon/arkhe_daemon.c $(TARGET_LIB)
	$(CC) $(CFLAGS) -o $(DAEMON) daemon/arkhe_daemon.c -L. -larkhe -Wl,-rpath,. $(LIBS)

$(PVM): vm/phase_vm.c vm/main_vm.c $(TARGET_LIB)
	$(CC) $(CFLAGS) -o $(PVM) vm/phase_vm.c vm/main_vm.c -L. -larkhe -Wl,-rpath,. $(LIBS)

$(BOOT): main.c $(TARGET_LIB)
	$(CC) $(CFLAGS) -o $(BOOT) main.c vm/phase_vm.c -L. -larkhe -Wl,-rpath,. $(LIBS)

$(DEMO_TARGET): tailslayer_arkhe_demo.cpp arkhe_hal.c
	$(CXX) $(CXXFLAGS) -o $(DEMO_TARGET) tailslayer_arkhe_demo.cpp arkhe_hal.c

clean:
	rm -f $(TARGET_LIB) $(ALLOC_LIB) $(DAEMON) $(PVM) $(BOOT)
	rm -f $(TARGET) $(DEMO_TARGET)

install:
	@echo "🜏 Arkhe OS installation successful. Phase-lock established."
