obj-m += arkhe_bus_driver.o

# Detect if we have /lib/modules/$(uname -r)/build
# If not, fallback to /usr/src/linux-headers-6.8.0-117-generic
ifneq ("$(wildcard /lib/modules/$(shell uname -r)/build)","")
KDIR ?= /lib/modules/$(shell uname -r)/build
else
KDIR ?= /usr/src/linux-headers-6.8.0-117-generic
endif

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean
