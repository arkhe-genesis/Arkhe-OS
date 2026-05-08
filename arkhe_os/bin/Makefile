# bin/Makefile — Build system for AGI userspace binaries

CC = gcc
CFLAGS = -Wall -Wextra -O2 -g -I../include -I/usr/include/linux
LDFLAGS = -L../lib -lagi

# Binary targets
BINARIES = agictl agimon agifed agikey agilog agieval agiboot agidebug

# Source directories
AGICTL_SRC = agictl/main.c agictl/commands/*.c agictl/utils/*.c
AGIMON_SRC = agimon/main.c agimon/collectors/*.c agimon/exporters/*.c agimon/alerting/*.c
AGIFED_SRC = agifed/main.c agifed/consensus/*.c agifed/network/*.c agifed/identity/*.c agifed/cli/*.c
AGIKEY_SRC = agikey/main.c agikey/keygen/*.c agikey/storage/*.c agikey/operations/*.c agikey/audit/*.c
AGILOG_SRC = agilog/main.c agilog/ingestion/*.c agilog/indexing/*.c agilog/query/*.c agilog/analysis/*.c agilog/export/*.c
AGIEVAL_SRC = agieval/main.c agieval/benchmarks/*.c agieval/validators/*.c agieval/reports/*.c agieval/ci/*.c
AGIBOOT_SRC = agiboot/main.c agiboot/state/*.c agiboot/hardware/*.c agiboot/security/*.c agiboot/recovery/*.c
AGIDEBUG_SRC = agidebug/main.c agidebug/introspection/*.c agidebug/control/*.c agidebug/analysis/*.c agidebug/ui/*.c

# Library dependencies
LIBAGI = ../libagi/libagi.a

# Default target
all: $(BINARIES)

# Individual binary rules
agictl: $(AGICTL_SRC) $(LIBAGI)
	$(CC) $(CFLAGS) -o $@ $(AGICTL_SRC) $(LDFLAGS)

agimon: $(AGIMON_SRC) $(LIBAGI)
	$(CC) $(CFLAGS) -o $@ $(AGIMON_SRC) $(LDFLAGS) -lpthread -lm

agifed: $(AGIFED_SRC) $(LIBAGI)
	$(CC) $(CFLAGS) -o $@ $(AGIFED_SRC) $(LDFLAGS) -lcrypto -lssl

agikey: $(AGIKEY_SRC) $(LIBAGI)
	$(CC) $(CFLAGS) -o $@ $(AGIKEY_SRC) $(LDFLAGS) -lcrypto

agilog: $(AGILOG_SRC) $(LIBAGI)
	$(CC) $(CFLAGS) -o $@ $(AGILOG_SRC) $(LDFLAGS) -lsqlite3

agieval: $(AGIEVAL_SRC) $(LIBAGI)
	$(CC) $(CFLAGS) -o $@ $(AGIEVAL_SRC) $(LDFLAGS) -lm

agiboot: $(AGIBOOT_SRC) $(LIBAGI)
	$(CC) $(CFLAGS) -o $@ $(AGIBOOT_SRC) $(LDFLAGS)

agidebug: $(AGIDEBUG_SRC) $(LIBAGI)
	$(CC) $(CFLAGS) -o $@ $(AGIDEBUG_SRC) $(LDFLAGS) -lncurses

# Library build
$(LIBAGI):
	$(MAKE) -C ../libagi

# Install target
install: all
	install -d $(DESTDIR)/usr/bin
	install -m 755 $(BINARIES) $(DESTDIR)/usr/bin/
	install -d $(DESTDIR)/usr/lib
	install -m 644 $(LIBAGI) $(DESTDIR)/usr/lib/
	install -d $(DESTDIR)/usr/include/agi
	install -m 644 ../include/linux/agi.h $(DESTDIR)/usr/include/agi/
	install -d $(DESTDIR)/usr/share/man/man1
	install -m 644 docs/man/*.1 $(DESTDIR)/usr/share/man/man1/

# Clean target
clean:
	rm -f $(BINARIES)
	$(MAKE) -C ../libagi clean

# Test target
test: all
	./test/run_tests.sh

.PHONY: all install clean test