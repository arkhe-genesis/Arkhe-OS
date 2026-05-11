/* kernel/sched_coherence.c */
#include <linux/sched.h>
#include <linux/sched/task.h>
#include <linux/sched/ag.h>  /* AGI scheduler extensions */
#include <linux/agi.h>
#include <linux/lfir.h>
#include <linux/tracepoint.h>

/* ============================================================================
 * Coherence-Aware Runqueue Extensions
 * ============================================================================ */

struct coherence_rq {
    struct rb_root_cached coherence_tree;  /* RB-tree ordered by coherence impact */
    struct list_head coherence_list;       /* FIFO for same-impact tasks */
    __u32 min_coherence_target;            /* Minimum Φ_C for tasks in this rq */
    __u32 avg_coherence;                   /* Running average coherence of runnable tasks */
};

/* ============================================================================
 * Coherence Impact Calculation
 * ============================================================================ */

/**
 * calculate_coherence_impact() - Calculate scheduling impact of a task
 * @p: Target task_struct
 *
 * Returns: Coherence impact score (higher = more urgent to schedule).
 *
 * Impact = f(Φ_C_current, Φ_C_target, alignment_drift, temporal_consistency)
 */
static s64 calculate_coherence_impact(struct task_struct *p)
{
    struct agi_coherence_metrics metrics;
    __u32 current_coh = agi_get_process_coherence(p, &metrics);
    __u32 target_coh = p->agi_target_coherence; /* Set via sys_agi_coherence */

    if (current_coh >= target_coh)
        return 0; /* Task is coherent enough, low scheduling priority */

    /* Calculate drift from target */
    s64 drift = (s64)target_coh - (s64)current_coh;

    /* Penalize tasks with high alignment drift */
    if (metrics.alignment_score < 0x00008000) /* < 0.5 in Q16.16 */
        drift *= 2;

    /* Boost tasks with low temporal consistency (need inference) */
    if (metrics.temporal_consistency < 0x0000C000) /* < 0.75 */
        drift += 0x00010000; /* Add 1.0 in Q16.16 */

    return drift;
}

/* ============================================================================
 * Scheduler Integration Hooks
 * ============================================================================ */

/**
 * coherence_enqueue_task() - Enqueue task in coherence-aware runqueue
 * @rq: Target runqueue
 * @p: Task to enqueue
 * @flags: Enqueue flags
 */
void coherence_enqueue_task(struct rq *rq, struct task_struct *p, int flags)
{
    struct coherence_rq *crq = rq->agi_data;
    s64 impact = calculate_coherence_impact(p);

    /* Insert into RB-tree ordered by impact (higher impact = leftmost) */
    struct rb_node **new = &crq->coherence_tree.rb_root.rb_node;
    struct rb_node *parent = NULL;
    struct task_struct *entry;

    while (*new) {
        entry = rb_entry(*new, struct task_struct, agi_node);
        s64 entry_impact = calculate_coherence_impact(entry);

        parent = *new;
        if (impact > entry_impact)
            new = &((*new)->rb_left);
        else
            new = &((*new)->rb_right);
    }

    rb_link_node(&p->agi_node, parent, new);
    rb_insert_color(&p->agi_node, &crq->coherence_tree.rb_root);

    /* Also add to FIFO list for fairness within same impact */
    list_add_tail(&p->agi_list, &crq->coherence_list);

    trace_sched_coherence_enqueue(rq->cpu, p->pid, impact);
}

/**
 * coherence_dequeue_task() - Dequeue task from coherence-aware runqueue
 * @rq: Target runqueue
 * @p: Task to dequeue
 * @flags: Dequeue flags
 */
void coherence_dequeue_task(struct rq *rq, struct task_struct *p, int flags)
{
    struct coherence_rq *crq = rq->agi_data;

    /* Remove from RB-tree */
    rb_erase(&p->agi_node, &crq->coherence_tree.rb_root);

    /* Remove from FIFO list */
    list_del(&p->agi_list);

    trace_sched_coherence_dequeue(rq->cpu, p->pid);
}

/**
 * coherence_pick_next_task() - Pick next task by coherence impact
 * @rq: Target runqueue
 *
 * Returns: Next task to run, or NULL if no runnable task.
 */
struct task_struct *coherence_pick_next_task(struct rq *rq)
{
    struct coherence_rq *crq = rq->agi_data;

    if (RB_EMPTY_ROOT(&crq->coherence_tree.rb_root))
        return NULL;

    /* Pick leftmost node (highest coherence impact) */
    struct rb_node *leftmost = rb_first(&crq->coherence_tree.rb_root);
    struct task_struct *next = rb_entry(leftmost, struct task_struct, agi_node);

    /* Sanity check: ensure task is still runnable */
    if (!task_on_rq_queued(next) || next->state != TASK_RUNNING) {
        coherence_dequeue_task(rq, next, 0);
        return coherence_pick_next_task(rq); /* Recurse */
    }

    trace_sched_coherence_pick(rq->cpu, next->pid,
                               calculate_coherence_impact(next));

    return next;
}

/* ============================================================================
 * Scheduler Initialization
 * ============================================================================ */

int coherence_sched_init(struct rq *rq)
{
    struct coherence_rq *crq = kzalloc(sizeof(*crq), GFP_KERNEL);
    if (!crq)
        return -ENOMEM;

    crq->coherence_tree = RB_ROOT_CACHED;
    INIT_LIST_HEAD(&crq->coherence_list);
    crq->min_coherence_target = 0x00008000; /* Default: 0.5 in Q16.16 */
    crq->avg_coherence = 0x00010000; /* Default: 1.0 */

    rq->agi_data = crq;
    return 0;
}

void coherence_sched_destroy(struct rq *rq)
{
    kfree(rq->agi_data);
    rq->agi_data = NULL;
}
