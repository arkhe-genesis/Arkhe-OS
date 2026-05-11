# kernel/Makefile - AGI subsystem integration

# AGI Subsystem
obj-$(CONFIG_AGI_SUBSYSTEM) += agi/
agi/ := kernel/agi/

# Core AGI syscalls
obj-$(CONFIG_AGI_CORE) += agi/agi_core.o

# Coherence-aware scheduler
obj-$(CONFIG_AGI_SCHEDULER) += agi/sched_coherence.o

# Quantum hardware interface (shared)
obj-$(CONFIG_AGI_QUANTUM_HW) += agi/quantum_hardware.o

# Tracepoints
obj-$(CONFIG_AGI_TRACEPOINTS) += agi/trace_agi.o
