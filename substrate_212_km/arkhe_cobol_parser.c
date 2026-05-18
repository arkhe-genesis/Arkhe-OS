/*
 * arkhe_cobol_parser.c — ARKHE OS Kernel COBOL Parser Module
 * Substrate: 212-KM (Kernel Module Loadable)
 * Linux 6.8 Compatible
 *
 * make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 * sudo insmod arkhe_cobol_parser.ko
 * sudo dmesg | tail
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/string.h>
#include <linux/ctype.h>
#include <linux/time.h>
#include <linux/interrupt.h>
#include <linux/hashtable.h>
#include <linux/vmalloc.h>
#include <linux/mm.h>
#include "arkhe_cobol_parser.h"

#define DRIVER_NAME         "arkhe_cobol"
#define DRIVER_CLASS        "arkhe"
#define DRIVER_VERSION      "212-KM-v1.0.0"
#define ARKHE_MAX_PIDS      1024
#define ARKHE_MAX_CHANNELS  16
#define ARKHE_IRQ_BASE      200

MODULE_LICENSE("GPL");
MODULE_AUTHOR("ARKHE OS Architect <orcid:0009-0005-2697-4668>");
MODULE_DESCRIPTION("ARKHE OS Kernel COBOL Parser — Substrate 212-KM");
MODULE_VERSION(DRIVER_VERSION);

/* === Estruturas internas do kernel === */

struct arkhe_kernel_page {
    __u32 page_id;
    __u32 owner_pid;
    void *virtual_addr;
    phys_addr_t physical_addr;
    size_t size;
    __u8 permissions;     /* 1=R, 2=W, 4=X */
    char *cobol_fragment;
    struct list_head list;
};

struct arkhe_interrupt_entry {
    __u32 irq_number;
    __u8 type;
    __u32 source_pid;
    char payload[256];
    __u64 timestamp;
    __u8 handled;
    struct list_head list;
};

struct arkhe_bus_channel {
    char name[32];
    struct list_head messages;
    struct list_head subscribers;
    __u32 msg_counter;
    struct mutex lock;
};

struct arkhe_bus_subscriber {
    __u32 pid;
    struct list_head list;
};

struct arkhe_bus_msg_entry {
    struct arkhe_bus_message msg;
    struct list_head list;
};

/* === Variáveis globais do módulo === */

static dev_t arkhe_dev_num;
static struct cdev arkhe_cdev;
static struct class *arkhe_class;
static struct device *arkhe_device;
static DEFINE_MUTEX(arkhe_mutex);

static struct list_head page_list;
static struct list_head interrupt_list;
static struct arkhe_bus_channel bus_channels[ARKHE_MAX_CHANNELS];
static __u32 channel_count = 0;
static __u32 irq_counter = 0;
static __u32 handled_count = 0;
static __u64 total_syscall_cycles = 0;
static __u32 total_syscalls = 0;
static __u64 boot_timestamp;
static float kernel_phi_c = 1.0f;

/* === Forward declarations === */
static int arkhe_open(struct inode *inode, struct file *filp);
static int arkhe_release(struct inode *inode, struct file *filp);
static long arkhe_ioctl(struct file *filp, unsigned int cmd, unsigned long arg);

static const struct file_operations arkhe_fops = {
    .owner = THIS_MODULE,
    .open = arkhe_open,
    .release = arkhe_release,
    .unlocked_ioctl = arkhe_ioctl,
    .compat_ioctl = arkhe_ioctl,
};

/* === Funções de parsing COBOL em kernel space === */

static int arkhe_extract_program_id(const char *source, size_t len, char *out, size_t out_len)
{
    const char *pattern = "PROGRAM-ID.";
    char *pos = strnstr(source, pattern, len);
    if (!pos) return -1;

    pos += strlen(pattern);
    while (pos < source + len && isspace(*pos)) pos++;

    size_t i = 0;
    while (pos < source + len && i < out_len - 1) {
        if (isspace(*pos) || *pos == '.') break;
        out[i++] = *pos++;
    }
    out[i] = '\0';
    return 0;
}

static int arkhe_scan_security(const char *source, size_t len,
                                struct arkhe_security_violation *violations,
                                __u32 *count, float *phi_c)
{
    *count = 0;
    *phi_c = 1.0f;

    /* ALTER proibido */
    if (strnstr(source, "ALTER", len)) {
        if (*count < ARKHE_MAX_VIOLATIONS) {
            violations[*count].violation_type = ARKHE_VIOL_ALTER;
            violations[*count].severity = 0; /* critical */
            strncpy(violations[*count].description, "ALTER modifies runtime flow — prohibited", 127);
            violations[*count].phi_c_impact = 0.15f;
            (*count)++;
            *phi_c -= 0.15f;
        }
    }

    /* GOTO DEPENDING ON */
    if (strnstr(source, "GO TO", len) && strnstr(source, "DEPENDING ON", len)) {
        if (*count < ARKHE_MAX_VIOLATIONS) {
            violations[*count].violation_type = ARKHE_VIOL_GOTO_DEP;
            violations[*count].severity = 1; /* high */
            strncpy(violations[*count].description, "GO TO DEPENDING ON creates non-deterministic flow", 127);
            violations[*count].phi_c_impact = 0.10f;
            (*count)++;
            *phi_c -= 0.10f;
        }
    }

    /* PERFORM THRU */
    if (strnstr(source, "PERFORM", len) && strnstr(source, "THRU", len)) {
        if (*count < ARKHE_MAX_VIOLATIONS) {
            violations[*count].violation_type = ARKHE_VIOL_PERFORM_THRU;
            violations[*count].severity = 2; /* medium */
            strncpy(violations[*count].description, "PERFORM THRU requires paragraph range validation", 127);
            violations[*count].phi_c_impact = 0.05f;
            (*count)++;
            *phi_c -= 0.05f;
        }
    }

    /* CICS sem auditoria */
    if (strnstr(source, "EXEC CICS", len)) {
        if (*count < ARKHE_MAX_VIOLATIONS) {
            violations[*count].violation_type = ARKHE_VIOL_CICS_AUDIT;
            violations[*count].severity = 2; /* medium */
            strncpy(violations[*count].description, "CICS transaction without explicit audit trail", 127);
            violations[*count].phi_c_impact = 0.05f;
            (*count)++;
            *phi_c -= 0.05f;
        }
    }

    if (*phi_c < 0.0f) *phi_c = 0.0f;
    return 0;
}

static int arkhe_extract_cics(const char *source, size_t len,
                               struct arkhe_cics_transaction *txns, __u32 *count)
{
    *count = 0;
    const char *pos = source;

    while ((pos = strnstr(pos, "EXEC CICS", len - (pos - source))) != NULL) {
        if (*count >= ARKHE_MAX_CICS_TXN) break;

        struct arkhe_cics_transaction *txn = &txns[*count];
        memset(txn, 0, sizeof(*txn));

        /* Extrair comando após EXEC CICS */
        pos += 9;
        while (pos < source + len && isspace(*pos)) pos++;

        if (strnstr(pos, "READ", 4)) txn->command = ARKHE_CICS_READ;
        else if (strnstr(pos, "WRITEQ TD", 9)) txn->command = ARKHE_CICS_WRITEQ_TD;
        else if (strnstr(pos, "WRITE", 5)) txn->command = ARKHE_CICS_WRITE;
        else if (strnstr(pos, "REWRITE", 7)) txn->command = ARKHE_CICS_REWRITE;
        else if (strnstr(pos, "DELETE", 6)) txn->command = ARKHE_CICS_DELETE;
        else if (strnstr(pos, "START", 5)) txn->command = ARKHE_CICS_START;
        else if (strnstr(pos, "RETURN", 6)) txn->command = ARKHE_CICS_RETURN;
        else if (strnstr(pos, "READQ TD", 8)) txn->command = ARKHE_CICS_READQ_TD;

        /* Extrair FILE('name') */
        char *file_pos = strnstr(pos, "FILE('", len - (pos - source));
        if (file_pos) {
            file_pos += 6;
            size_t i = 0;
            while (file_pos < source + len && *file_pos != '\'' && i < ARKHE_MAX_RESOURCE - 1) {
                txn->resource[i++] = *file_pos++;
            }
        }

        /* Extrair QUEUE('name') */
        char *queue_pos = strnstr(pos, "QUEUE('", len - (pos - source));
        if (queue_pos) {
            queue_pos += 7;
            size_t i = 0;
            while (queue_pos < source + len && *queue_pos != '\'' && i < ARKHE_MAX_RESOURCE - 1) {
                txn->resource[i++] = *queue_pos++;
            }
        }

        (*count)++;
        pos++;
    }
    return 0;
}

static int arkhe_extract_ims(const char *source, size_t len,
                              struct arkhe_ims_call *calls, __u32 *count)
{
    *count = 0;
    const char *pos = source;

    while ((pos = strnstr(pos, "CBLTDLI", len - (pos - source))) != NULL) {
        if (*count >= ARKHE_MAX_IMS_CALL) break;

        struct arkhe_ims_call *call = &calls[*count];
        memset(call, 0, sizeof(*call));

        /* Extrair função após USING */
        char *using_pos = strnstr(pos, "USING", len - (pos - source));
        if (using_pos) {
            using_pos += 5;
            while (using_pos < source + len && (isspace(*using_pos) || *using_pos == ',')) using_pos++;

            if (*using_pos == '\'' || *using_pos == '"') {
                using_pos++;
                size_t i = 0;
                while (using_pos < source + len && *using_pos != '\'' && *using_pos != '"' && i < 3) {
                    char func[4] = {0};
                    func[i++] = *using_pos++;
                }
                if (strnstr(using_pos - i, "GU", 2)) call->function = ARKHE_IMS_GU;
                else if (strnstr(using_pos - i, "GN", 2)) call->function = ARKHE_IMS_GN;
                else if (strnstr(using_pos - i, "GNP", 3)) call->function = ARKHE_IMS_GNP;
                else if (strnstr(using_pos - i, "GHU", 3)) call->function = ARKHE_IMS_GHU;
                else if (strnstr(using_pos - i, "GHN", 3)) call->function = ARKHE_IMS_GHN;
                else if (strnstr(using_pos - i, "ISRT", 4)) call->function = ARKHE_IMS_ISRT;
                else if (strnstr(using_pos - i, "DLET", 4)) call->function = ARKHE_IMS_DLET;
                else if (strnstr(using_pos - i, "REPL", 4)) call->function = ARKHE_IMS_REPL;
            }
        }

        (*count)++;
        pos++;
    }
    return 0;
}

static int arkhe_extract_db2(const char *source, size_t len,
                              struct arkhe_db2_statement *stmts, __u32 *count)
{
    *count = 0;
    const char *pos = source;

    while ((pos = strnstr(pos, "EXEC SQL", len - (pos - source))) != NULL) {
        if (*count >= ARKHE_MAX_DB2_STMT) break;

        struct arkhe_db2_statement *stmt = &stmts[*count];
        memset(stmt, 0, sizeof(*stmt));

        pos += 8;
        while (pos < source + len && isspace(*pos)) pos++;

        if (strnstr(pos, "SELECT", 6)) stmt->statement_type = ARKHE_DB2_SELECT;
        else if (strnstr(pos, "INSERT", 6)) stmt->statement_type = ARKHE_DB2_INSERT;
        else if (strnstr(pos, "UPDATE", 6)) stmt->statement_type = ARKHE_DB2_UPDATE;
        else if (strnstr(pos, "DELETE", 6)) stmt->statement_type = ARKHE_DB2_DELETE;
        else if (strnstr(pos, "OPEN", 4)) stmt->statement_type = ARKHE_DB2_OPEN;
        else if (strnstr(pos, "CLOSE", 5)) stmt->statement_type = ARKHE_DB2_CLOSE;
        else if (strnstr(pos, "FETCH", 5)) stmt->statement_type = ARKHE_DB2_FETCH;

        /* Extrair tabela */
        char *from_pos = strnstr(pos, "FROM", len - (pos - source));
        if (from_pos) {
            from_pos += 4;
            while (from_pos < source + len && isspace(*from_pos)) from_pos++;
            size_t i = 0;
            while (from_pos < source + len && !isspace(*from_pos) && i < ARKHE_MAX_TABLE - 1) {
                stmt->table[i++] = *from_pos++;
            }
        }

        /* Verificar WHERE */
        if (strnstr(pos, "WHERE", len - (pos - source))) {
            stmt->has_where_clause = 1;
        }

        (*count)++;
        pos++;
    }
    return 0;
}

static int arkhe_generate_tokens(struct arkhe_cobol_request *req)
{
    __u32 t = 0;

    /* Tokens CICS */
    for (__u32 i = 0; i < req->cics_count && t < ARKHE_MAX_TOKENS; i++) {
        struct arkhe_token *tok = &req->tokens[t++];
        tok->semantics = 1; /* CICS */
        strncpy(tok->program, req->program_id, ARKHE_MAX_PROGRAM_ID - 1);
        tok->command_or_function = req->cics_txns[i].command;
        strncpy(tok->resource_or_pcb, req->cics_txns[i].resource, ARKHE_MAX_RESOURCE - 1);
        tok->phi_c_at_parse = req->phi_c_score;
        tok->timestamp = ktime_get_real_ns();
        snprintf(tok->identity, 63, "cics_txn_%s_%u", req->program_id, req->cics_txns[i].line_number);

        /* SHA3-256 truncated header */
        char payload[128];
        snprintf(payload, 127, "%s:%u:%s", req->program_id, req->cics_txns[i].command, req->cics_txns[i].resource);
        /* Simplified hash for kernel space */
        __u32 hash = 0;
        for (size_t j = 0; j < strlen(payload); j++) {
            hash = ((hash << 5) + hash) + payload[j];
        }
        memset(tok->header, 0, 32);
        memcpy(tok->header, &hash, 4);
    }

    /* Tokens IMS */
    for (__u32 i = 0; i < req->ims_count && t < ARKHE_MAX_TOKENS; i++) {
        struct arkhe_token *tok = &req->tokens[t++];
        tok->semantics = 2; /* IMS */
        strncpy(tok->program, req->program_id, ARKHE_MAX_PROGRAM_ID - 1);
        tok->command_or_function = req->ims_calls[i].function;
        strncpy(tok->resource_or_pcb, req->ims_calls[i].pcb_name, ARKHE_MAX_RESOURCE - 1);
        tok->phi_c_at_parse = req->phi_c_score;
        tok->timestamp = ktime_get_real_ns();
        snprintf(tok->identity, 63, "ims_call_%s_%u", req->program_id, i);
    }

    req->token_count = t;
    return 0;
}

/* === Funções de interrupt === */

static int arkhe_raise_interrupt(__u8 type, __u32 source_pid, const char *payload)
{
    struct arkhe_interrupt_entry *entry = kzalloc(sizeof(*entry), GFP_KERNEL);
    if (!entry) return -ENOMEM;

    entry->irq_number = ++irq_counter;
    entry->type = type;
    entry->source_pid = source_pid;
    strncpy(entry->payload, payload, 255);
    entry->timestamp = ktime_get_real_ns();
    entry->handled = 0;

    mutex_lock(&arkhe_mutex);
    list_add_tail(&entry->list, &interrupt_list);
    mutex_unlock(&arkhe_mutex);

    /* Degradação de Φ_C em violação crítica */
    if (type == ARKHE_VIOL_ALTER || type == ARKHE_VIOL_SQL_INJECT) {
        kernel_phi_c -= 0.05f;
        if (kernel_phi_c < 0.0f) kernel_phi_c = 0.0f;
    }

    return entry->irq_number;
}

/* === Funções de Bus V3 === */

static int arkhe_bus_init_channels(void)
{
    const char *channels[] = {
        "cics_transactions", "ims_calls", "db2_statements",
        "security_violations", "cobol_tokens", "phi_c_metrics"
    };

    for (int i = 0; i < 6 && i < ARKHE_MAX_CHANNELS; i++) {
        strncpy(bus_channels[i].name, channels[i], 31);
        INIT_LIST_HEAD(&bus_channels[i].messages);
        INIT_LIST_HEAD(&bus_channels[i].subscribers);
        mutex_init(&bus_channels[i].lock);
        bus_channels[i].msg_counter = 0;
        channel_count++;
    }
    return 0;
}

static int arkhe_bus_publish(const char *channel_name, struct arkhe_bus_message *msg)
{
    for (__u32 i = 0; i < channel_count; i++) {
        if (strcmp(bus_channels[i].name, channel_name) == 0) {
            struct arkhe_bus_msg_entry *entry = kzalloc(sizeof(*entry), GFP_KERNEL);
            if (!entry) return -ENOMEM;

            memcpy(&entry->msg, msg, sizeof(*msg));
            entry->msg.msg_id = ++bus_channels[i].msg_counter;
            entry->msg.timestamp = ktime_get_real_ns();
            entry->msg.phi_c_at_send = kernel_phi_c;

            mutex_lock(&bus_channels[i].lock);
            list_add_tail(&entry->list, &bus_channels[i].messages);
            mutex_unlock(&bus_channels[i].lock);

            return entry->msg.msg_id;
        }
    }
    return -ENOENT;
}

static int arkhe_bus_consume(const char *channel_name, __u32 pid, struct arkhe_bus_message *out)
{
    for (__u32 i = 0; i < channel_count; i++) {
        if (strcmp(bus_channels[i].name, channel_name) == 0) {
            struct arkhe_bus_msg_entry *entry;

            mutex_lock(&bus_channels[i].lock);
            list_for_each_entry(entry, &bus_channels[i].messages, list) {
                __u8 already_consumed = 0;
                for (__u8 j = 0; j < entry->msg.consumed_count && j < 8; j++) {
                    if (entry->msg.consumed_by[j] == pid) {
                        already_consumed = 1;
                        break;
                    }
                }
                if (!already_consumed && entry->msg.consumed_count < 8) {
                    entry->msg.consumed_by[entry->msg.consumed_count++] = pid;
                    memcpy(out, &entry->msg, sizeof(*out));
                    mutex_unlock(&bus_channels[i].lock);
                    return 0;
                }
            }
            mutex_unlock(&bus_channels[i].lock);
            return -ENODATA;
        }
    }
    return -ENOENT;
}

/* === File operations === */

static int arkhe_open(struct inode *inode, struct file *filp)
{
    pr_info("ARKHE: Device opened by pid %d\n", current->pid);
    return 0;
}

static int arkhe_release(struct inode *inode, struct file *filp)
{
    pr_info("ARKHE: Device closed by pid %d\n", current->pid);
    return 0;
}

static long arkhe_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    struct arkhe_cobol_request req;
    struct arkhe_kernel_stats stats;
    struct arkhe_bus_message bus_msg;
    __u64 start_cycles;
    int ret = 0;

    total_syscalls++;
    start_cycles = ktime_get_ns();

    switch (cmd) {
    case ARKHE_IOCTL_PARSE:
    case ARKHE_IOCTL_SECURITY_SCAN:
    case ARKHE_IOCTL_PHI_C_CALC:
    case ARKHE_IOCTL_TOKEN_GENERATE:
    case ARKHE_IOCTL_EXTRACT_CICS:
    case ARKHE_IOCTL_EXTRACT_IMS:
    case ARKHE_IOCTL_EXTRACT_DB2:
    case ARKHE_IOCTL_AST_EXPORT:
        if (copy_from_user(&req, (void __user *)arg, sizeof(req))) {
            ret = -EFAULT;
            goto out;
        }

        /* Verificar privilégio */
        if (req.caller_ring > ARKHE_RING2_SERVICE) {
            req.status = -2; /* PERMISSION_DENIED */
            req.kernel_phi_c = kernel_phi_c;
            if (copy_to_user((void __user *)arg, &req, sizeof(req)))
                ret = -EFAULT;
            else
                ret = 0;
            goto out;
        }

        /* Parse completo */
        if (cmd == ARKHE_IOCTL_PARSE || cmd == ARKHE_IOCTL_SECURITY_SCAN ||
            cmd == ARKHE_IOCTL_PHI_C_CALC || cmd == ARKHE_IOCTL_TOKEN_GENERATE ||
            cmd == ARKHE_IOCTL_AST_EXPORT) {

            arkhe_extract_program_id(req.source_fragment, req.source_len,
                                      req.program_id, ARKHE_MAX_PROGRAM_ID);
            arkhe_scan_security(req.source_fragment, req.source_len,
                                req.violations, &req.violation_count, &req.phi_c_score);
            arkhe_extract_cics(req.source_fragment, req.source_len,
                               req.cics_txns, &req.cics_count);
            arkhe_extract_ims(req.source_fragment, req.source_len,
                              req.ims_calls, &req.ims_count);
            arkhe_extract_db2(req.source_fragment, req.source_len,
                              req.db2_stmts, &req.db2_count);

            /* Levantar interrupts */
            for (__u32 i = 0; i < req.cics_count; i++) {
                char payload[256];
                snprintf(payload, 255, "cmd=%u,res=%s,line=%u",
                         req.cics_txns[i].command, req.cics_txns[i].resource,
                         req.cics_txns[i].line_number);
                arkhe_raise_interrupt(ARKHE_VIOL_CICS_AUDIT, req.caller_pid, payload);
            }

            for (__u32 i = 0; i < req.violation_count; i++) {
                if (req.violations[i].severity == 0) { /* critical */
                    arkhe_raise_interrupt(req.violations[i].violation_type,
                                          req.caller_pid, req.violations[i].description);
                }
            }

            if (cmd == ARKHE_IOCTL_TOKEN_GENERATE || cmd == ARKHE_IOCTL_PARSE) {
                arkhe_generate_tokens(&req);
            }

            /* Publicar no Bus V3 */
            if (cmd == ARKHE_IOCTL_PARSE) {
                struct arkhe_bus_message phi_msg;
                memset(&phi_msg, 0, sizeof(phi_msg));
                strncpy(phi_msg.channel_name, "phi_c_metrics", 31);
                phi_msg.sender_pid = req.caller_pid;
                strncpy(phi_msg.sender_substrate, "212-KM", 15);
                snprintf(phi_msg.payload, ARKHE_MAX_BUS_MSG - 1,
                         "program=%s,cobol_phi=%.4f,kernel_phi=%.4f,violations=%u",
                         req.program_id, req.phi_c_score, kernel_phi_c, req.violation_count);
                phi_msg.payload_len = strlen(phi_msg.payload);
                arkhe_bus_publish("phi_c_metrics", &phi_msg);
            }
        }

        /* Extrair apenas CICS */
        if (cmd == ARKHE_IOCTL_EXTRACT_CICS) {
            arkhe_extract_cics(req.source_fragment, req.source_len,
                               req.cics_txns, &req.cics_count);
        }

        /* Extrair apenas IMS */
        if (cmd == ARKHE_IOCTL_EXTRACT_IMS) {
            arkhe_extract_ims(req.source_fragment, req.source_len,
                              req.ims_calls, &req.ims_count);
        }

        /* Extrair apenas DB2 */
        if (cmd == ARKHE_IOCTL_EXTRACT_DB2) {
            arkhe_extract_db2(req.source_fragment, req.source_len,
                              req.db2_stmts, &req.db2_count);
        }

        req.status = 0; /* OK */
        req.kernel_phi_c = kernel_phi_c;
        req.execution_cycles = ktime_get_ns() - start_cycles;

        if (copy_to_user((void __user *)arg, &req, sizeof(req)))
            ret = -EFAULT;
        break;

    case ARKHE_IOCTL_KERNEL_STATS:
        memset(&stats, 0, sizeof(stats));
        strncpy(stats.substrate_id, "212-KM", 15);
        stats.kernel_phi_c = kernel_phi_c;
        stats.uptime_seconds = (ktime_get_ns() - boot_timestamp) / NSEC_PER_SEC;
        stats.total_pages = 4096;
        stats.interrupts_raised = irq_counter;
        stats.interrupts_handled = handled_count;
        stats.handlers_registered = 4;
        stats.total_syscall_cycles = total_syscall_cycles;
        stats.total_syscalls = total_syscalls;
        stats.bus_channels = channel_count;
        stats.bus_messages = 0;
        for (__u32 i = 0; i < channel_count; i++) {
            struct arkhe_bus_msg_entry *entry;
            list_for_each_entry(entry, &bus_channels[i].messages, list) {
                stats.bus_messages++;
            }
        }

        if (copy_to_user((void __user *)arg, &stats, sizeof(stats)))
            ret = -EFAULT;
        break;

    case ARKHE_IOCTL_BUS_PUBLISH:
        if (copy_from_user(&bus_msg, (void __user *)arg, sizeof(bus_msg))) {
            ret = -EFAULT;
            goto out;
        }
        ret = arkhe_bus_publish(bus_msg.channel_name, &bus_msg);
        break;

    case ARKHE_IOCTL_BUS_CONSUME:
        if (copy_from_user(&bus_msg, (void __user *)arg, sizeof(bus_msg))) {
            ret = -EFAULT;
            goto out;
        }
        ret = arkhe_bus_consume(bus_msg.channel_name, current->pid, &bus_msg);
        if (ret == 0) {
            if (copy_to_user((void __user *)arg, &bus_msg, sizeof(bus_msg)))
                ret = -EFAULT;
        }
        break;

    default:
        pr_warn("ARKHE: Unknown ioctl command: 0x%x\n", cmd);
        ret = -EINVAL;
    }

out:
    total_syscall_cycles += ktime_get_ns() - start_cycles;
    return ret;
}

/* === Init e Exit === */

static int __init arkhe_cobol_init(void)
{
    int ret;

    pr_info("ARKHE: Initializing COBOL Parser Kernel Module %s\n", DRIVER_VERSION);
    pr_info("ARKHE: Canonical Seal: bfbc03900123006c35442cf12f2d0189b0496856d8eb3e23fbbbbe4e46cbf31e\n");

    /* Alocar device number */
    ret = alloc_chrdev_region(&arkhe_dev_num, 0, 1, DRIVER_NAME);
    if (ret < 0) {
        pr_err("ARKHE: Failed to allocate device number\n");
        return ret;
    }

    /* Criar classe */
    arkhe_class = class_create(DRIVER_CLASS);
    if (IS_ERR(arkhe_class)) {
        ret = PTR_ERR(arkhe_class);
        unregister_chrdev_region(arkhe_dev_num, 1);
        return ret;
    }

    /* Criar device */
    arkhe_device = device_create(arkhe_class, NULL, arkhe_dev_num, NULL, DRIVER_NAME);
    if (IS_ERR(arkhe_device)) {
        ret = PTR_ERR(arkhe_device);
        class_destroy(arkhe_class);
        unregister_chrdev_region(arkhe_dev_num, 1);
        return ret;
    }

    /* Inicializar cdev */
    cdev_init(&arkhe_cdev, &arkhe_fops);
    arkhe_cdev.owner = THIS_MODULE;
    ret = cdev_add(&arkhe_cdev, arkhe_dev_num, 1);
    if (ret) {
        device_destroy(arkhe_class, arkhe_dev_num);
        class_destroy(arkhe_class);
        unregister_chrdev_region(arkhe_dev_num, 1);
        return ret;
    }

    /* Inicializar listas */
    INIT_LIST_HEAD(&page_list);
    INIT_LIST_HEAD(&interrupt_list);

    /* Inicializar Bus V3 */
    arkhe_bus_init_channels();

    boot_timestamp = ktime_get_ns();
    kernel_phi_c = 1.0f;

    pr_info("ARKHE: Module loaded successfully\n");
    pr_info("ARKHE: Device /dev/%s created (major=%d, minor=%d)\n",
            DRIVER_NAME, MAJOR(arkhe_dev_num), MINOR(arkhe_dev_num));
    pr_info("ARKHE: Bus V3 channels: %d\n", channel_count);
    pr_info("ARKHE: Kernel space: 16MB (4096 pages x 4KB)\n");

    return 0;
}

static void __exit arkhe_cobol_exit(void)
{
    struct arkhe_interrupt_entry *irq_entry, *irq_tmp;
    struct arkhe_kernel_page *page_entry, *page_tmp;
    struct arkhe_bus_msg_entry *msg_entry, *msg_tmp;

    pr_info("ARKHE: Unloading COBOL Parser Kernel Module\n");

    /* Limpar interrupts */
    list_for_each_entry_safe(irq_entry, irq_tmp, &interrupt_list, list) {
        list_del(&irq_entry->list);
        kfree(irq_entry);
    }

    /* Limpar páginas */
    list_for_each_entry_safe(page_entry, page_tmp, &page_list, list) {
        if (page_entry->cobol_fragment)
            vfree(page_entry->cobol_fragment);
        list_del(&page_entry->list);
        kfree(page_entry);
    }

    /* Limpar Bus V3 */
    for (__u32 i = 0; i < channel_count; i++) {
        list_for_each_entry_safe(msg_entry, msg_tmp, &bus_channels[i].messages, list) {
            list_del(&msg_entry->list);
            kfree(msg_entry);
        }
    }

    cdev_del(&arkhe_cdev);
    device_destroy(arkhe_class, arkhe_dev_num);
    class_destroy(arkhe_class);
    unregister_chrdev_region(arkhe_dev_num, 1);

    pr_info("ARKHE: Module unloaded\n");
}

module_init(arkhe_cobol_init);
module_exit(arkhe_cobol_exit);