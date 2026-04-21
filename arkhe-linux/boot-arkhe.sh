#!/bin/bash
# Boot ARKHE LINUX via QEMU
qemu-system-x86_64 \
    -kernel vmlinuz-arkhe \
    -initrd arkhe-initramfs.cpio.gz \
    -append "console=ttyS0 quiet init=/init" \
    -nographic \
    -m 256M \
    -cpu host \
    -enable-kvm 2>/dev/null || \
qemu-system-x86_64 \
    -kernel vmlinuz-arkhe \
    -initrd arkhe-initramfs.cpio.gz \
    -append "console=ttyS0 quiet init=/init" \
    -nographic \
    -m 256M
