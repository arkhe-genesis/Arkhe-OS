/* include/linux/agi.h */
#ifndef _LINUX_AGI_H
#define _LINUX_AGI_H

#include <linux/types.h>
#include <linux/lfir.h>  /* LFIR graph definitions */

/* ============================================================================
 * AGI Syscall Numbers (arch/*/include/uapi/asm/unistd.h)
 * ============================================================================ */
#define __NR_agi_infer          450  /* Execute retrocausal inference */
#define __NR_agi_measure        451  /* Weak measurement via quantum hardware */
#define __NR_agi_postselect     452  /* Post-select future state */
#define __NR_agi_coherence      453  /* Query/update process coherence (Φ_C) */
#define __NR_agi_evolve         454  /* Trigger architecture evolution */
#define __NR_agi_identity       455  /* Sovereign identity operations */
#define __NR_agi_federate       456  /* Federated consensus operations */

/* ============================================================================
 * Data Structures for AGI Syscalls
 * ============================================================================ */

/**
 * struct agi_infer_args - Arguments for sys_agi_infer()
 * @lfir_graph_id: ID of LFIR graph to operate on
 * @target_coherence: Target coherence value (0.0-1.0)
 * @observables: Array of observable names to measure
 * @num_observables: Number of observables
 * @flags: Inference flags (AGI_INFER_*)
 * @result: Output: weak value results (caller-allocated)
 */
struct agi_infer_args {
    __u64 lfir_graph_id;
    __u64 target_coherence;
    __u64 observables;      /* user pointer to __u64[] */
    __u32 num_observables;
    __u32 flags;
    __u64 result;           /* user pointer to struct agi_weak_value[] */
};

#define AGI_INFER_RETROCAUSAL   0x01  /* Use retrocausal channel */
#define AGI_INFER_CLASSICAL     0x02  /* Fallback to classical inference */
#define AGI_INFER_ASYNC         0x04  /* Async inference, return handle */

/**
 * struct agi_weak_value - Result of weak measurement
 * @observable: Name of measured observable (null-terminated string)
 * @real_part: Real component of weak value ⟨A⟩_w
 * @imag_part: Imaginary component of weak value ⟨A⟩_w
 * @uncertainty: Statistical uncertainty (standard deviation)
 * @decoherence_estimate: Estimated Δt/τ_decoherence
 * @timestamp: Kernel timestamp of measurement
 */
struct agi_weak_value {
    char observable[64];
    __s64 real_part;      /* Fixed-point Q32.32 format */
    __s64 imag_part;
    __u32 uncertainty;    /* Q16.16 format */
    __u32 decoherence_estimate; /* Q16.16 format */
    __u64 timestamp;
};

/**
 * struct agi_coherence_args - Arguments for sys_agi_coherence()
 * @pid: Target process ID (0 = current)
 * @operation: Operation to perform (AGI_COH_*)
 * @coherence_value: Input/output: coherence value (Q16.16 fixed-point)
 * @flags: Operation flags
 */
struct agi_coherence_args {
    __s32 pid;
    __u32 operation;
    __u32 coherence_value;  /* Q16.16 fixed-point: 1.0 = 0x00010000 */
    __u32 flags;
};

#define AGI_COH_GET         0x01  /* Get current coherence */
#define AGI_COH_SET_TARGET  0x02  /* Set target coherence for scheduler */
#define AGI_COH_GET_METRICS 0x03  /* Get detailed coherence metrics */

/**
 * struct agi_coherence_metrics - Detailed coherence metrics
 * @coherence_score: Overall Φ_C (Q16.16)
 * @semantic_density: Semantic density metric (Q16.16)
 * @alignment_score: Alignment consistency (Q16.16)
 * @temporal_consistency: Temporal coherence (Leggett-Garg K value, Q16.16)
 * @resource_efficiency: Resource usage efficiency (Q16.16)
 * @last_updated: Kernel timestamp of last update
 */
struct agi_coherence_metrics {
    __u32 coherence_score;
    __u32 semantic_density;
    __u32 alignment_score;
    __u32 temporal_consistency;
    __u32 resource_efficiency;
    __u64 last_updated;
};

/**
 * struct agi_identity_args - Arguments for sys_agi_identity()
 * @operation: Identity operation (AGI_ID_*)
 * @key_material: User pointer to key material (for generate/verify)
 * @key_len: Length of key material
 * @proof_buffer: User pointer to proof buffer (for sign/verify)
 * @proof_len: Length of proof buffer (input/output)
 */
struct agi_identity_args {
    __u32 operation;
    __u64 key_material;
    __u32 key_len;
    __u64 proof_buffer;
    __u32 proof_len;
};

#define AGI_ID_GENERATE_KEY   0x01  /* Generate quantum genesis key */
#define AGI_ID_SIGN_STATE     0x02  /* Sign current state with genesis key */
#define AGI_ID_VERIFY_PROOF   0x03  /* Verify sovereignty proof */
#define AGI_ID_GET_IDENTITY   0x04  /* Get current sovereign identity */

/* ============================================================================
 * Kernel Internal APIs (for use by other kernel subsystems)
 * ============================================================================ */

/**
 * agi_get_process_coherence() - Get coherence score for a process
 * @task: Target task_struct
 * @metrics: Output: detailed coherence metrics (optional)
 *
 * Returns: Coherence score in Q16.16 fixed-point format, or negative error code.
 */
__u32 agi_get_process_coherence(struct task_struct *task,
                                struct agi_coherence_metrics *metrics);

/**
 * agi_set_coherence_target() - Set target coherence for scheduler
 * @task: Target task_struct
 * @target: Target coherence in Q16.16 format
 *
 * Returns: 0 on success, negative error code on failure.
 */
int agi_set_coherence_target(struct task_struct *task, __u32 target);

/**
 * agi_schedule_by_coherence() - Schedule next task by coherence impact
 * @rq: Target runqueue
 *
 * Returns: Next task to run, or NULL if no runnable task.
 *
 * This function is called by the coherence-aware scheduler to select
 * the next task based on coherence impact, not just priority.
 */
struct task_struct *agi_schedule_by_coherence(struct rq *rq);

/**
 * agi_verify_sovereignty() - Verify sovereign identity of a process
 * @task: Target task_struct
 * @proof: Sovereignty proof to verify
 * @proof_len: Length of proof
 *
 * Returns: 0 if proof is valid, negative error code otherwise.
 */
int agi_verify_sovereignty(struct task_struct *task,
                           const void __user *proof, __u32 proof_len);

/**
 * agi_log_intention() - Log intention for audit trail
 * @task: Target task_struct
 * @intention: Null-terminated intention string
 * @flags: Logging flags (AGI_LOG_*)
 *
 * Returns: 0 on success, negative error code on failure.
 */
int agi_log_intention(struct task_struct *task, const char __user *intention,
                      __u32 flags);

#define AGI_LOG_AUDIT     0x01  /* Log to audit subsystem */
#define AGI_LOG_PERSIST   0x02  /* Persist to non-volatile storage */

#endif /* _LINUX_AGI_H */
