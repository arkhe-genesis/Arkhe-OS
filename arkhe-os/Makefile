# ARKHE OS Main Makefile
all: kernel userspace

kernel:
	$(MAKE) -C kernel

userspace:
	$(MAKE) -C userspace

test:
	$(MAKE) -C tests test

clean:
	$(MAKE) -C kernel clean
	$(MAKE) -C userspace clean
	$(MAKE) -C tests clean
clean:
	$(MAKE) -C kernel clean
	$(MAKE) -C userspace clean
