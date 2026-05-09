/* kernel/cgroup/coherence_cgroup.c */
#include <linux/cgroup.h>
#include <linux/agi.h>
#include <linux/sched.h>
#include <linux/lfir.h>

/* ============================================================================
 * Coherence Cgroup Controller State
 * ============================================================================ */

struct coherence_cgroup {
    struct cgroup_subsys_state css;
    __u32 min_coherence;        /* Minimum Φ_C for tasks in this cgroup */
    __u32 target_coherence;     /* Target Φ_C for scheduler */
    __u32 current_avg_coherence; /* Running average of task coherence */
    u64 coherence_violations;   /* Count of coherence threshold violations */
    u64 last_violation_time;    /* Timestamp of last violation */
};

/* ============================================================================
 * Cgroup Subsystem Definition
 * ============================================================================ */

static struct cgroup_subsys_state *
coherence_cgroup_css_alloc(struct cgroup_subsys_state *parent_css)
{
    struct coherence_cgroup *coh;

    coh = kzalloc(sizeof(*coh), GFP_KERNEL);
    if (!coh)
        return ERR_PTR(-ENOMEM);

    coh->min_coherence = 0x00008000; /* Default: 0.5 in Q16.16 */
    coh->target_coherence = 0x00010000; /* Default: 1.0 */
    coh->current_avg_coherence = 0x00010000;

    return &coh->css;
}

static void coherence_cgroup_css_free(struct cgroup_subsys_state *css)
{
    struct coherence_cgroup *coh = container_of(css, struct coherence_cgroup, css);
    kfree(coh);
}

/* ============================================================================
 * Cgroup File Operations
 * ============================================================================ */

static int coherence_min_read(struct seq_file *sf, void *v)
{
    struct coherence_cgroup *coh = css_to_coh(seq_css(sf));
    seq_printf(sf, "%u.%06u\n", coh->min_coherence >> 16,
               (coh->min_coherence & 0xFFFF) * 1000000 / 0x10000);
    return 0;
}

static ssize_t coherence_min_write(struct kernfs_open_file *of, char *buf,
                                   size_t nbytes, loff_t off)
{
    struct coherence_cgroup *coh = css_to_coh(of_css(of));
    __u32 value;
    int ret;

    ret = kstrtou32(buf, 0, &value);
    if (ret)
        return ret;

    if (value > 0x00010000) /* > 1.0 */
        return -ERANGE;

    coh->min_coherence = value;
    return nbytes;
}

static struct cftype coherence_files[] = {
    {
        .name = "min_coherence",
        .seq_show = coherence_min_read,
        .write = coherence_min_write,
    },
    { } /* terminate */
};

/* ============================================================================
 * Cgroup Callbacks
 * ============================================================================ */

static int coherence_can_attach(struct cgroup_taskset *tset)
{
    struct task_struct *task;
    struct cgroup_subsys_state *css;

    cgroup_taskset_for_each(task, css, tset) {
        __u32 task_coh = agi_get_process_coherence(task, NULL);
        struct coherence_cgroup *coh = css_to_coh(css);

        if (task_coh < coh->min_coherence) {
            /* Task coherence below cgroup minimum - reject attachment */
            return -EPERM;
        }
    }
    return 0;
}

static void coherence_attach(struct cgroup_taskset *tset)
{
    struct task_struct *task;
    struct cgroup_subsys_state *css;

    cgroup_taskset_for_each(task, css, tset) {
        struct coherence_cgroup *coh = css_to_coh(css);
        agi_set_coherence_target(task, coh->target_coherence);
    }
}

/* ============================================================================
 * OOM Killer Integration
 * ============================================================================ */

static bool coherence_oom_kill(struct task_struct *task)
{
    struct cgroup_subsys_state *css = task_css(task, coherence_cgrp_id);
    struct coherence_cgroup *coh = css_to_coh(css);
    __u32 task_coh = agi_get_process_coherence(task, NULL);

    /* Kill tasks with coherence below minimum threshold */
    if (task_coh < coh->min_coherence) {
        coh->coherence_violations++;
        coh->last_violation_time = ktime_get_real_ns();
        return true;
    }

    return false;
}

/* ============================================================================
 * Subsystem Registration
 * ============================================================================ */

struct cgroup_subsys coherence_cgrp_subsys = {
    .css_alloc = coherence_cgroup_css_alloc,
    .css_free = coherence_cgroup_css_free,
    .can_attach = coherence_can_attach,
    .attach = coherence_attach,
    .legacy_cftypes = coherence_files,
    .early_init = true,
};
