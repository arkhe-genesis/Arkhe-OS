obj-m += arkhe_cobol_parser.o

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
	@echo "Loading ARKHE COBOL Parser Kernel Module..."
	@sudo insmod arkhe_cobol_parser.ko
	@echo "Module loaded. Check dmesg:"
	@sudo dmesg | tail -5

unload:
	@echo "Unloading ARKHE COBOL Parser Kernel Module..."
	@sudo rmmod arkhe_cobol_parser
	@echo "Module unloaded."

status:
	@echo "ARKHE Module Status:"
	@lsmod | grep arkhe_cobol || echo "Module not loaded"
	@echo ""
	@echo "Device nodes:"
	@ls -la /dev/arkhe_cobol 2>/dev/null || echo "Device not created"
	@echo ""
	@echo "Kernel log:"
	@sudo dmesg | grep "ARKHE:" | tail -10

.PHONY: all clean install load unload status