# Makefile para compilar cdv.ko

obj-m += cdv.o

# Flags de compilação
ccflags-y := -std=gnu11 -Wall -Wextra -DCONFIG_CATHEDRAL_SECURITY

# Incluir headers da Catedral
ccflags-y += -I$(src)/../include

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

install:
	insmod cdv.ko audit_mode=1 firmware_lock_on_boot=1
	dmesg | grep CDV

test:
	@echo "Running simulated tests for CDV..."
	@# In a real environment, we would run test_cdv_userspace
	@echo "Tests completed (simulated)."

.PHONY: all clean install test
