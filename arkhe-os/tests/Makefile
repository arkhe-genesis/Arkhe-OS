CC=gcc
CFLAGS=-I../userspace/libarkhe/include -Wall

INTEGRATION_SRCS=$(wildcard integration/*.c)
INTEGRATION_BINS=$(patsubst %.c,%,$(INTEGRATION_SRCS))

FUZZING_SRCS=$(wildcard fuzzing/*.c)
FUZZING_BINS=$(patsubst %.c,%,$(FUZZING_SRCS))

all: $(INTEGRATION_BINS) $(FUZZING_BINS)
	@echo "All tests built successfully."

test: all
	@for t in $(INTEGRATION_BINS); do ./$$t; done
	@for t in $(FUZZING_BINS); do ./$$t; done

%: %.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f $(INTEGRATION_BINS) $(FUZZING_BINS)
