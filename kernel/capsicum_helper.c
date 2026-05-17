/*
 * ARKHE OS Substrato ∞: Capsicum Helper
 * Canon: ∞.Ω.∇+++.∞.kernel.capsicum_helper
 * Função: Facilitar entrada em capability mode para processos de IA
 * Linguagem: C (kernel space + userspace interface)
 */

#include <sys/param.h>
#include <sys/systm.h>
#include <sys/kernel.h>
#include <sys/module.h>
#include <sys/sysctl.h>
#include <sys/proc.h>
#include <sys/capsicum.h>
#include <sys/file.h>
#include <sys/fcntl.h>
#include <sys/uio.h>
#include <sys/malloc.h>
#include <security/mac/mac_framework.h>

#define CAPSICUM_HELPER_VERSION "1.0.0"

MALLOC_DEFINE(M_CAPSICUM_HELPER, "capsicum_helper", "Capsicum helper data");

/* Sysctl para configurar políticas de capability */
static int capsicum_policy_enforce = 1;
SYSCTL_INT(_kern, OID_AUTO, capsicum_policy_enforce, CTLFLAG_RW,
    &capsicum_policy_enforce, 0, "Enforce ARKHE Capsicum policies");

/* MAC policy para validar capabilities */
static int
capsicum_helper_check_cap_enter(struct thread *td)
{
    if (!capsicum_policy_enforce)
        return 0;

    /* Verificar se processo pertence a jail ARKHE */
    if (td->td_proc->p_prison &&
        strncmp(td->td_proc->p_prison->pr_name, "arkhe_", 6) == 0) {
        /* Permitir cap_enter() apenas para processos autorizados */
        if (td->td_proc->p_comm[0] == 'a' &&
            strncmp(td->td_proc->p_comm, "arkhe_agent", 11) == 0) {
            printf("[Capsicum] Allowing cap_enter for %s in jail %s\n",
                   td->td_proc->p_comm, td->td_proc->p_prison->pr_name);
            return 0;
        }
    }

    /* Negar por padrão para processos não autorizados */
    printf("[Capsicum] Denied cap_enter for %s (pid %d)\n",
           td->td_proc->p_comm, td->td_proc->p_pid);
    return EPERM;
}

/* Registrar política MAC */
static struct mac_policy_ops capsicum_helper_ops = {
    .mpo_check_cap_enter = capsicum_helper_check_cap_enter,
};

static struct mac_policy_conf capsicum_helper_conf = {
    .mpc_name = "capsicum_helper",
    .mpc_fullname = "ARKHE Capsicum Helper Policy",
    .mpc_ops = &capsicum_helper_ops,
    .mpc_loadtime_flags = MPC_LOADTIME_FLAG_NOTLATE,
    .mpc_field_off = NULL,
    .mpc_runtime_flags = 0
};

/* Module load/unload */
static int
capsicum_helper_load(module_t mod, int what, void *arg)
{
    switch (what) {
    case MOD_LOAD:
        mac_policy_register(&capsicum_helper_conf);
        printf("[Capsicum Helper] Policy loaded v%s\n", CAPSICUM_HELPER_VERSION);
        break;
    case MOD_UNLOAD:
        mac_policy_unregister(&capsicum_helper_conf);
        printf("[Capsicum Helper] Policy unloaded\n");
        break;
    default:
        return EOPNOTSUPP;
    }
    return 0;
}

static moduledata_t capsicum_helper_mod = {
    "capsicum_helper",
    capsicum_helper_load,
    NULL
};

DECLARE_MODULE(capsicum_helper, capsicum_helper_mod,
               SI_SUB_MAC_POLICY, SI_ORDER_ANY);
MODULE_VERSION(capsicum_helper, 1);
