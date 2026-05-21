CC = gcc
CFLAGS = -Wall -Wextra -I.
PYTHON = python3

all: arkhe_hybrid_bus.o canonize test_bin

arkhe_hybrid_bus.o: arkhe_hybrid_bus.c arkhe_gds_map.h arkhe_unikernel_polyglot.h
	$(CC) $(CFLAGS) -c $< -o $@

test_bin: substrato_434_test.c arkhe_hybrid_bus.o
	$(CC) $(CFLAGS) $^ -o test

canonize: substrato_434_sfq_nv.py
	$(PYTHON) substrato_434_sfq_nv.py

clean:
	rm -f *.o test
