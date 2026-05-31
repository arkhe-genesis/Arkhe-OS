# Makefile para ARKHE OS

all: bootloader kernel

bootloader:
	nasm -f bin boot/bootloader.asm -o bootloader.bin

kernel:
	cargo build --manifest-path=Cargo.toml

clean:
	rm -f bootloader.bin
	cargo clean --manifest-path=Cargo.toml
