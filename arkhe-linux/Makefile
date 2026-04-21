# Makefile para arkhe.ko
obj-m += arkhe.o

KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean

install:
	sudo insmod arkhe.ko
	sudo mknod /dev/arkhe c 250 0
	sudo chmod 666 /dev/arkhe

remove:
	sudo rmmod arkhe
	sudo rm -f /dev/arkhe
