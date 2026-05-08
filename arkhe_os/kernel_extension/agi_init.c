/* init/agi_init.c */
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/agi.h>
#include <linux/lfir.h>
#include <linux/quantum_hardware.h>

/* ============================================================================
 * AGI Subsystem Initialization Order
 * ============================================================================ */

static int __init agi_subsystem_init(void)
{
    int ret;

    pr_info("AGI Subsystem: Initializing AGI kernel extensions\n");

    /* 1. Initialize LFIR graph infrastructure */
    ret = lfir_init();
    if (ret) {
        pr_err("AGI Subsystem: Failed to initialize LFIR\n");
        return ret;
    }

    /* 2. Initialize quantum hardware interface */
    ret = quantum_hardware_init();
    if (ret) {
        pr_warn("AGI Subsystem: Quantum hardware initialization failed, using classical fallback\n");
        /* Continue with classical fallback */
    }

    /* 3. Initialize AGI core syscalls */
    ret = agi_core_init();
    if (ret) {
        pr_err("AGI Subsystem: Failed to initialize AGI core\n");
        goto err_lfir;
    }

    /* 4. Initialize coherence-aware scheduler */
    ret = coherence_sched_init_all();
    if (ret) {
        pr_err("AGI Subsystem: Failed to initialize coherence scheduler\n");
        goto err_core;
    }

    /* 5. Initialize sovereign LSM */
    ret = sovereign_lsm_init();
    if (ret) {
        pr_err("AGI Subsystem: Failed to initialize sovereign LSM\n");
        goto err_sched;
    }

    /* 6. Initialize coherence cgroup controller */
    ret = coherence_cgroup_init();
    if (ret) {
        pr_err("AGI Subsystem: Failed to initialize coherence cgroup\n");
        goto err_lsm;
    }

    pr_info("AGI Subsystem: All components initialized successfully\n");
    return 0;

err_lsm:
    /* LSM cleanup handled by kernel */
err_sched:
    coherence_sched_destroy_all();
err_core:
    agi_core_exit();
err_lfir:
    lfir_exit();
    return ret;
}

static void __exit agi_subsystem_exit(void)
{
    pr_info("AGI Subsystem: Shutting down AGI kernel extensions\n");

    coherence_cgroup_exit();
    /* LSM cleanup handled by kernel */
    coherence_sched_destroy_all();
    agi_core_exit();
    quantum_hardware_exit();
    lfir_exit();

    pr_info("AGI Subsystem: Shutdown complete\n");
}

/* ============================================================================
 * Module Registration
 * ============================================================================ */

late_initcall(agi_subsystem_init);
module_exit(agi_subsystem_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arkhe OS Collective");
MODULE_DESCRIPTION("AGI Kernel Subsystem Initialization");
MODULE_VERSION("1.0");
