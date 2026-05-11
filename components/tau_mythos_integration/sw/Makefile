# Makefile for Mythos RHO Agent (Native/ARM64)
CC = gcc
CFLAGS = -O3 -Wall -D_GNU_SOURCE
LDFLAGS = -lm -lpthread

TARGET = rho_mythos_exec
SOURCES = mythos_driver.c rho_agent_mythos.c

# Consolidated RTL path for reference (not used in C compile but kept for documentation)
RTL_PATH = ../../arkhe-hardware

all: $(TARGET)

$(TARGET): $(SOURCES)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(TARGET)
