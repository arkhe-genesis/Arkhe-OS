obj-m += agi_omni_kernel.o

all:
	# Compile kernel module
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules || true
	# Compile user-space core library
	gcc -shared -fPIC -o omni_core.so omni_core.c coherence_field.c lfir_core.c omni_net.c sovereign_interface.c temporal_anchor.c -lm

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean || true
	rm -f omni_core.so
