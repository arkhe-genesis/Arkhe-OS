# Makefile para Agente RHO (Cross-compilation para Versal)

# Compilador (Pode ser sobrescrito: make CC=gcc)
CROSS_COMPILE ?= aarch64-linux-gnu-
CC = $(CROSS_COMPILE)gcc
CFLAGS = -Wall -O2

# Alvos
TARGET = rho_agent
SRC = rho_agent.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $^

clean:
	rm -f $(TARGET)

.PHONY: all clean
