obj-m += modules/temporal_mod.o
obj-m += modules/consensus_mod.o
obj-m += modules/merkle_mod.o
obj-m += modules/netfilter_arkhe.o

KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
