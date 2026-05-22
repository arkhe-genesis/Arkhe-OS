CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c11
LDFLAGS = -lm -lpthread
TARGET = megakernel

SRCS = megakernel.c \
       josephson/josephson_driver.c \
       josephson/squid_readout.c \
       josephson/pulse_controller.c \
       sophon/sophon_orchestrator.c \
       sophon/kk_cavity_bridge.c \
       sophon/panprotopsiquic_field.c \
       invariants/ghost_checker.c \
       invariants/loopseal_checker.c \
       invariants/gap_checker.c \
       invariants/phi_checker.c \
       security/dilithium3_hsm.c \
       temporal/temporal_chain.c \
       telemetry/telemetry_daemon.c

OBJS = $(SRCS:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET)

run: $(TARGET)
	sudo ./$(TARGET)