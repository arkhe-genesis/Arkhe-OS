# Makefile para ARKHE OS

all: bootloader kernel servers tools libs

bootloader:
	nasm -f bin boot/bootloader.asm -o bootloader.bin

kernel:
	cd kernel && cargo build --lib

servers:
	cargo build --manifest-path=Cargo.toml -p arkhe-vfs -p arkhe-net -p arkhe-passport -p arkhe-orchestrator -p arkhe-bindu -p arkhe-package

tools:
	cargo build --manifest-path=Cargo.toml -p arkhe-sh -p arkhe-checkpoint -p arkhe-pkg

libs:
	cargo build --manifest-path=Cargo.toml -p arkhe-arklib -p arkhe-pqc -p arkhe-nostr -p arkhe-ipfs -p arkhe-tor

clean:
	rm -f bootloader.bin
	cargo clean --manifest-path=Cargo.toml
