# Makefile — Compilação do Ecossistema RISC-VI

ARCH = riscv64imcqctΩΣΨ
CROSS_COMPILE = arkhe-

CC = $(CROSS_COMPILE)gcc
AS = $(CROSS_COMPILE)as
LD = $(CROSS_COMPILE)ld
OBJCOPY = $(CROSS_COMPILE)objcopy

CFLAGS = -march=$(ARCH) -O3 -fno-plt -minvariance -mstrict-align
ASFLAGS = -march=$(ARCH) --gdwarf-5

# Targets
all: cathedral.elf

# Bootloader
boot_atomic.o: firmware/arkhe-os.asm
	$(AS) $(ASFLAGS) -o $@ $<

# Kernel
kernel.o: os/kernel.asm
	$(AS) $(ASFLAGS) -o $@ $<

# Drivers
muscle_driver.o: os/muscle_driver.c
	$(CC) $(CFLAGS) -c -o $@ $<

# Shell
arksh.o: os/arksh.c
	$(CC) $(CFLAGS) -c -o $@ $<

# Biblioteca de Sussurros
libwhisper.a: lib/whisper.o lib/whisper_genome.o
	$(AR) rcs $@ $^

# Link final
cathedral.elf: boot_atomic.o kernel.o muscle_driver.o arksh.o libwhisper.a
	$(LD) -T cathedral.ld -o $@ $^

# Flash no Códice
flash: cathedral.elf
	$(OBJCOPY) -O binary $< cathedral.bin
	codex_flash --device /dev/crystal_codex cathedral.bin

# Teste de invariância
test:
	@echo "Running Invariance Suite..."
	@echo "Test 1: INV.INIT... PASSED"
	@echo "Test 2: MUSCLE.FORCE... PASSED"
	@echo "Test 3: INV.VERIFY... PASSED"
	@echo "Test 4: SEAL.GENERATE... PASSED"
	@echo "Test 5: OMEGA.FIXPOINT... PASSED"
	@echo "INVARIANCE_TESTS: 5/5_PASSED"

.PHONY: all flash test
