obj-m += arkhe_unikernel_polyglot.o

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install
	depmod -a

load:
	@echo "Loading ARKHE Uni‑Kernel Polyglot Module..."
	@sudo insmod arkhe_unikernel_polyglot.ko
	@echo "Module loaded. Check dmesg:"
	@sudo dmesg | tail -5

unload:
	@echo "Unloading ARKHE Uni‑Kernel Polyglot Module..."
	@sudo rmmod arkhe_unikernel_polyglot
	@echo "Module unloaded."

status:
	@echo "ARKHE Uni‑Kernel Status:"
	@lsmod | grep arkhe_uni || echo "Module not loaded"
	@echo ""
	@echo "Device nodes:"
	@ls -la /dev/arkhe_uni 2>/dev/null || echo "Device not created"
	@echo ""
	@echo "Kernel log:"
	@sudo dmesg | grep "ARKHE_UNI:" | tail -10

.PHONY: all clean install load unload status
