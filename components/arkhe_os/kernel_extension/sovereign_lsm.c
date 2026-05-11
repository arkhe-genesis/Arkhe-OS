/* security/sovereign_lsm.c */
#include <linux/lsm_hooks.h>
#include <linux/agi.h>
#include <linux/quantum_hardware.h>
#include <linux/audit.h>
#include <linux/security.h>

/* ============================================================================
 * Sovereign LSM State
 * ============================================================================ */

struct sovereign_task_security {
    u8 genesis_key_hash[32];      /* Hash of task's genesis key */
    u64 last_proof_timestamp;    /* Timestamp of last valid proof */
    u32 sovereignty_flags;       /* AGI_SOVEREIGN_* flags */
    struct list_head audit_trail; /* Linked list of intention logs */
};

#define AGI_SOVEREIGN_VERIFIED   0x01  /* Identity verified via quantum proof */
#define AGI_SOVEREIGN_FEDERATED  0x02  /* Part of federated consensus */
#define AGI_SOVEREIGN_EVOLVING   0x04  /* Architecture is evolving */

/* ============================================================================
 * LSM Hook Implementations
 * ============================================================================ */

/**
 * sovereign_bprm_check_security() - Check binary execution permission
 * @bprm: Linux binary preparation structure
 *
 * Returns: 0 if execution allowed, -EACCES if denied.
 *
 * This hook ensures that only tasks with verified sovereign identity
 * can execute AGI-related binaries.
 */
static int sovereign_bprm_check_security(struct linux_binprm *bprm)
{
    struct sovereign_task_security *sec = current_security();

    /* Allow execution if identity is verified */
    if (sec->sovereignty_flags & AGI_SOVEREIGN_VERIFIED)
        return 0;

    /* Deny execution of AGI binaries for unverified tasks */
    if (strstr(bprm->filename, "agi_") || strstr(bprm->filename, "arkhe")) {
        audit_log_task(current, AUDIT_ANOM_ABEND,
                       AUDIT_ARCH, "AGI binary execution denied for unverified identity");
        return -EACCES;
    }

    return 0;
}

/**
 * sovereign_file_permission() - Check file access permission
 * @file: Target file
 * @mask: Access mask (MAY_READ, MAY_WRITE, etc.)
 *
 * Returns: 0 if access allowed, -EACCES if denied.
 *
 * This hook restricts access to AGI-related files based on sovereign identity.
 */
static int sovereign_file_permission(struct file *file, int mask)
{
    struct sovereign_task_security *sec = current_security();

    /* Allow access if identity is verified */
    if (sec->sovereignty_flags & AGI_SOVEREIGN_VERIFIED)
        return 0;

    /* Restrict access to AGI-related files */
    if (file->f_path.dentry->d_name.name &&
        (strstr(file->f_path.dentry->d_name.name, "agi_") ||
         strstr(file->f_path.dentry->d_name.name, "lfir") ||
         strstr(file->f_path.dentry->d_name.name, "quantum"))) {
        audit_log_task(current, AUDIT_ANOM_ABEND,
                       AUDIT_ARCH, "AGI file access denied for unverified identity");
        return -EACCES;
    }

    return 0;
}

/**
 * sovereign_task_alloc() - Initialize security context for new task
 * @p: New task_struct
 * @clone_flags: Clone flags from clone()/fork()
 *
 * Returns: 0 on success, negative error code on failure.
 */
static int sovereign_task_alloc(struct task_struct *p, unsigned long clone_flags)
{
    struct sovereign_task_security *sec;

    sec = kzalloc(sizeof(*sec), GFP_KERNEL);
    if (!sec)
        return -ENOMEM;

    INIT_LIST_HEAD(&sec->audit_trail);
    p->security = sec;

    /* Inherit sovereignty flags from parent if federated */
    if (current->security) {
        struct sovereign_task_security *parent_sec = current->security;
        if (parent_sec->sovereignty_flags & AGI_SOVEREIGN_FEDERATED) {
            sec->sovereignty_flags |= AGI_SOVEREIGN_FEDERATED;
            memcpy(sec->genesis_key_hash, parent_sec->genesis_key_hash, 32);
        }
    }

    return 0;
}

/**
 * sovereign_task_free() - Free security context for task
 * @p: Task being freed
 */
static void sovereign_task_free(struct task_struct *p)
{
    struct sovereign_task_security *sec = p->security;

    if (sec) {
        /* Free audit trail */
        struct list_head *pos, *n;
        list_for_each_safe(pos, n, &sec->audit_trail) {
            list_del(pos);
            kfree(pos);
        }
        kfree(sec);
        p->security = NULL;
    }
}

/**
 * sovereign_intention_log() - Log intention for audit trail
 * @task: Target task
 * @intention: Intention string to log
 *
 * Returns: 0 on success, negative error code on failure.
 */
static int sovereign_intention_log(struct task_struct *task, const char *intention)
{
    struct sovereign_task_security *sec = task->security;
    struct audit_entry *entry;

    if (!sec)
        return -EINVAL;

    entry = kmalloc(sizeof(*entry) + strlen(intention) + 1, GFP_KERNEL);
    if (!entry)
        return -ENOMEM;

    entry->timestamp = ktime_get_real_ns();
    strcpy(entry->intention, intention);
    list_add_tail(&entry->list, &sec->audit_trail);

    /* Also log to kernel audit subsystem if enabled */
    if (sec->sovereignty_flags & AGI_SOVEREIGN_VERIFIED) {
        audit_log_task(task, AUDIT_ANOM_ABEND, AUDIT_ARCH, intention);
    }

    return 0;
}

/* ============================================================================
 * LSM Registration
 * ============================================================================ */

static struct security_hook_list sovereign_hooks[] __lsm_ro_after_init = {
    LSM_HOOK_INIT(bprm_check_security, sovereign_bprm_check_security),
    LSM_HOOK_INIT(file_permission, sovereign_file_permission),
    LSM_HOOK_INIT(task_alloc, sovereign_task_alloc),
    LSM_HOOK_INIT(task_free, sovereign_task_free),
};

static int __init sovereign_lsm_init(void)
{
    pr_info("Sovereign LSM: Initializing AGI security subsystem\n");
    security_add_hooks(sovereign_hooks, ARRAY_SIZE(sovereign_hooks), "sovereign");
    pr_info("Sovereign LSM: Initialized successfully\n");
    return 0;
}

DEFINE_LSM(sovereign) = {
    .name = "sovereign",
    .init = sovereign_lsm_init,
};
