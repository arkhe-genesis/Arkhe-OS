.. _agi_overview:

======================
AGI Subsystem Overview
======================

The AGI (Artificial General Intelligence) subsystem provides kernel-space
primitives for building sovereign, coherence-aware intelligent systems.

Core Concepts
=============

Coherence (Φ_C)
    A metric representing the alignment, consistency, and integrity of an
    intelligent system. Ranges from 0.0 (incoherent) to 1.0 (perfectly coherent).

Retrocausal Inference
    A form of inference that uses weak measurements and post-selection to
    extract information about future states, enabling proactive optimization.

Sovereign Identity
    A quantum-based identity system that provides cryptographic proof of
    an agent's intentions and alignment with stated values.

Architecture
============

The AGI subsystem is organized into several kernel components:

* **AGI Core** (`kernel/agi_core.c`): Provides syscalls for inference,
  coherence management, and identity operations.

* **Coherence Scheduler** (`kernel/sched_coherence.c`): Extends the Linux
  scheduler to prioritize tasks based on their impact on system coherence.

* **Sovereign LSM** (`security/sovereign_lsm.c`): A Linux Security Module
  that enforces access control based on quantum-verified identity.

* **Coherence Cgroup** (`kernel/cgroup/coherence_cgroup.c`): A cgroup
  controller for resource management based on coherence thresholds.

* **Quantum Hardware Driver** (`drivers/quantum/rcp_hardware.c`): Drivers
  for time-crystal optomechanical systems enabling retrocausal channels.

Usage Examples
==============

Query Process Coherence
-----------------------

.. code-block:: c

    #include <linux/agi.h>

    struct agi_coherence_args args = {
        .pid = 0,  /* current process */
        .operation = AGI_COH_GET,
    };

    long ret = syscall(__NR_agi_coherence, &args);
    if (ret == 0) {
        printf("Coherence: %u.%06u\n",
               args.coherence_value >> 16,
               (args.coherence_value & 0xFFFF) * 1000000 / 0x10000);
    }

Execute Retrocausal Inference
-----------------------------

.. code-block:: c

    #include <linux/agi.h>

    struct agi_infer_args args = {
        .lfir_graph_id = my_graph_id,
        .target_coherence = 0x00010000,  /* 1.0 in Q16.16 */
        .observables = (u64)my_observables,
        .num_observables = 3,
        .flags = AGI_INFER_RETROCAUSAL,
        .result = (u64)my_results,
    };

    long ret = syscall(__NR_agi_infer, &args);
    if (ret > 0) {
        printf("Inference complete: %ld results\n", ret);
    }

Configuration
=============

The AGI subsystem can be configured via:

* **Kernel config**: Enable/disable components via `make menuconfig`
* **Cgroup files**: `/sys/fs/cgroup/agi/*/min_coherence`
* **Syscalls**: Runtime configuration via `sys_agi_coherence()`

For more details, see :ref:`agi_configuration`.
