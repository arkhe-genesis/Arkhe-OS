#!/bin/bash
KERNEL_IMG="../platforms/linux/arch/x86/boot/bzImage"
INITRD_IMG="../platforms/linux/initrd.img"

echo "Iniciando Cathedral OS no QEMU com isolamento de hardware..."

# Inicia um processo em background que simula o hardware enviando dados IMU
python3 virtio_sensor_sim.py --port 12345 &
SENSOR_PID=$!

qemu-system-x86_64 \
    -m 2G \
    -kernel $KERNEL_IMG \
    -initrd $INITRD_IMG \
    -append "console=ttyS0 selinux=1 enforcing=1 cathedral.fast=true" \
    -nographic \
    -cpu host \
    -smp 2 \
    # Cria um device virtio-serial conectado ao nosso script Python \
    -device virtio-serial-pci,id=vser0 \
    -chardev socket,id=chr0,host=127.0.0.1,port=12345,server=on,wait=off \
    -device virtserialport,chardev=chr0,bus=vser0.0,nr=1 \
    # Aceleração de GPU (para inferência LiteRT/OpenGL) \
    -accel kvm \
    -display none

kill $SENSOR_PID
