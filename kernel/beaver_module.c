/*
 * ARKHE OS Substrato ∞: BEAVer Kernel Module
 * Canon: ∞.Ω.∇+++.∞.kernel.beaver
 * Função: Verificação determinística de execuções no kernel FreeBSD
 * Linguagem: C (kernel space)
 */

#include <sys/param.h>
#include <sys/systm.h>
#include <sys/kernel.h>
#include <sys/module.h>
#include <sys/sysctl.h>
#include <sys/lock.h>
#include <sys/mutex.h>
#include <sys/proc.h>
#include <sys/uio.h>
#include <sys/malloc.h>
#include <sha3/sha3.h>      /* LibSHA3 para SHA3-256 */
#include <crypto/dilithium/dilithium.h>  /* PQC signatures */

#define BEAVER_VERSION "1.0.0"
#define BEAVER_MAX_EXECUTIONS 10000

MALLOC_DEFINE(M_BEAVer, "beaver", "ARKHE BEAVer verification data");

/* Estrutura para registro de execução verificada */
struct beaver_execution {
    uint64_t exec_id;
    uint8_t prompt_hash[32];          /* SHA3-256 do prompt */
    uint8_t result_hash[32];          /* SHA3-256 do resultado */
    uint8_t phi_c_score;              /* Coerência quantizada [0-255] */
    uint8_t pqc_signature[2592];      /* Dilithium3 signature */
    uint64_t timestamp;
    pid_t pid;
    char jail_name[64];
    TAILQ_ENTRY(beaver_execution) entries;
};

static TAILQ_HEAD(, beaver_execution) beaver_executions =
    TAILQ_HEAD_INITIALIZER(beaver_executions);

static struct mtx beaver_lock;
static uint64_t beaver_counter = 0;
static uint64_t beaver_list_length = 0;
static SYSCTL_NODE(_kern, OID_AUTO, beaver, CTLFLAG_RD, 0, "ARKHE BEAVer");

/* Sysctl para leitura de estatísticas */
static int
sysctl_beaver_stats(SYSCTL_HANDLER_ARGS)
{
    struct beaver_stats {
        uint64_t total_executions;
        uint64_t verified_count;
        uint8_t avg_phi_c;
    } stats;

    mtx_lock(&beaver_lock);
    stats.total_executions = beaver_counter;
    stats.verified_count = 0;

    struct beaver_execution *exec;
    TAILQ_FOREACH(exec, &beaver_executions, entries) {
        if (exec->phi_c_score >= 217)  /* Φ_C ≥ 0.85 */
            stats.verified_count++;
    }
    stats.avg_phi_c = (beaver_counter > 0) ?
        255 * stats.verified_count / beaver_counter : 0;
    mtx_unlock(&beaver_lock);

    return SYSCTL_OUT(req, &stats, sizeof(stats));
}

SYSCTL_PROC(_kern_beaver, OID_AUTO, stats, CTLTYPE_OPAQUE|CTLFLAG_RD,
    NULL, 0, sysctl_beaver_stats, "S,beaver_stats",
    "BEAVer execution statistics");

/* Função principal: registrar execução verificada */
int
beaver_register_execution(const uint8_t *prompt, size_t prompt_len,
                         const uint8_t *result, size_t result_len,
                         uint8_t phi_c, const uint8_t *pqc_sig,
                         struct thread *td)
{
    struct beaver_execution *exec;
    uint8_t prompt_hash[32], result_hash[32];
    int error = 0;

    /* Validar parâmetros */
    if (!prompt || !result || !pqc_sig || phi_c > 255)
        return EINVAL;

    /* Calcular hashes SHA3-256 */
    sha3_256(prompt_hash, prompt, prompt_len);
    sha3_256(result_hash, result, result_len);

    /* Alocar estrutura */
    exec = malloc(sizeof(*exec), M_BEAVer, M_WAITOK | M_ZERO);
    if (!exec)
        return ENOMEM;

    /* Preencher estrutura */
    mtx_lock(&beaver_lock);
    exec->exec_id = ++beaver_counter;
    memcpy(exec->prompt_hash, prompt_hash, 32);
    memcpy(exec->result_hash, result_hash, 32);
    exec->phi_c_score = phi_c;
    memcpy(exec->pqc_signature, pqc_sig, 2592);  /* Dilithium3 size */
    exec->timestamp = time_second;
    exec->pid = td->td_proc->p_pid;
    if (td->td_proc->p_prison)
        strlcpy(exec->jail_name, td->td_proc->p_prison->pr_name,
                sizeof(exec->jail_name));

    TAILQ_INSERT_TAIL(&beaver_executions, exec, entries);
    beaver_list_length++;

    /* Limitar tamanho da lista */
    while (beaver_list_length > BEAVER_MAX_EXECUTIONS) {
        struct beaver_execution *oldest = TAILQ_FIRST(&beaver_executions);
        if (oldest) {
            TAILQ_REMOVE(&beaver_executions, oldest, entries);
            free(oldest, M_BEAVer);
            beaver_list_length--;
        }
    }
    mtx_unlock(&beaver_lock);

    /* Ancorar na TemporalChain via character device (implementado separadamente) */
    /* beaver_anchor_to_temporalchain(exec); */

    printf("[BEAVer] Execution %llu registered: Φ_C=%d.%02d, jail=%s\n",
           (unsigned long long)exec->exec_id, exec->phi_c_score / 255 * 100,
           (exec->phi_c_score % 255) * 100 / 255, exec->jail_name);

    return 0;
}

/* Module load/unload */
static int
beaver_load(module_t mod, int what, void *arg)
{
    struct beaver_execution *exec, *tmp;

    switch (what) {
    case MOD_LOAD:
        mtx_init(&beaver_lock, "beaver_lock", NULL, MTX_DEF);
        printf("[BEAVer] Module loaded v%s\n", BEAVER_VERSION);
        break;
    case MOD_UNLOAD:
        mtx_lock(&beaver_lock);
        TAILQ_FOREACH_SAFE(exec, &beaver_executions, entries, tmp) {
            TAILQ_REMOVE(&beaver_executions, exec, entries);
            free(exec, M_BEAVer);
        }
        mtx_unlock(&beaver_lock);
        mtx_destroy(&beaver_lock);
        printf("[BEAVer] Module unloaded\n");
        break;
    default:
        return EOPNOTSUPP;
    }
    return 0;
}

static moduledata_t beaver_mod = {
    "beaver",
    beaver_load,
    NULL
};

DECLARE_MODULE(beaver, beaver_mod, SI_SUB_DRIVERS, SI_ORDER_MIDDLE);
MODULE_VERSION(beaver, 1);
