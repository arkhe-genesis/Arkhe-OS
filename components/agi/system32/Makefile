obj-m += agi_omni_kernel.o

all:
	# Compile kernel module
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules || true
	# Compile user-space core library
	gcc -shared -fPIC -o omni_core.so omni_core.c coherence_field.c lfir_core.c omni_net.c sovereign_interface.c temporal_anchor.c runtime/quantum/rcp_bridge.c -lm
	# Compile FFI bridge
	gcc -shared -fPIC -o agi_rcp_bridge.so runtime/quantum/rcp_bridge.c

package: all
	mkdir -p pkg/usr/local/lib/arkhe
	cp omni_core.so pkg/usr/local/lib/arkhe/
	cp agi_rcp_bridge.so pkg/usr/local/lib/arkhe/
	mkdir -p pkg/DEBIAN
	echo "Package: arkhe-system32" > pkg/DEBIAN/control
	echo "Version: 1.0" >> pkg/DEBIAN/control
	echo "Section: base" >> pkg/DEBIAN/control
	echo "Priority: optional" >> pkg/DEBIAN/control
	echo "Architecture: amd64" >> pkg/DEBIAN/control
	echo "Maintainer: Arkhe OS Architect" >> pkg/DEBIAN/control
	echo "Description: Arkhe OS Substrate 315/316 OmniCore and RCP FFI bridge" >> pkg/DEBIAN/control
	dpkg-deb --build pkg arkhe_system32.deb

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean || true
	rm -f omni_core.so agi_rcp_bridge.so arkhe_system32.deb
	rm -rf pkg
