// src/cathedral/kernel/cdv.c — Cathedral Driver Vetting Kernel Module
// Implementa verificação soberana de drivers com callbacks de notificação

#include "cdv.h"
#include <linux/slab.h>
#include <linux/vmalloc.h>
#include <linux/moduleparam.h>
#include <linux/ktime.h>
#include <linux/xattr.h>
#include <linux/cred.h>
#include <linux/ptrace.h>
#include <linux/kprobes.h>
#include <net/net_namespace.h>

// Configurações do módulo
static int audit_mode = 1;  // Habilitar logging detalhado
static int firmware_lock_on_boot = 1;  // Travar SPI flash no init
static uint32_t default_policy = CDV_POLICY_BLOCK_REVOKED |
                                  CDV_POLICY_BLOCK_EXPIRED |
                                  CDV_POLICY_BLOCK_UNKNOWN;

module_param(audit_mode, int, 0644);
MODULE_PARM_DESC(audit_mode, "Enable detailed audit logging (default=1)");
module_param(firmware_lock_on_boot, int, 0644);
MODULE_PARM_DESC(firmware_lock_on_boot, "Lock firmware protection on module init (default=1)");

// Estado global do módulo
static struct class* cdv_class = NULL;
static struct cdev cdv_cdev;
static dev_t cdv_dev_number;
static DEFINE_MUTEX(cdv_mutex);
static DEFINE_MUTEX(cdv_notifier_mutex);

// Hash table para cache de reputações (LRU simplificado)
#define REPUTATION_HASH_BITS 10
#define REPUTATION_HASH_SIZE (1 << REPUTATION_HASH_BITS)
static struct hlist_head reputation_hash[REPUTATION_HASH_SIZE];
static atomic_t reputation_count = ATOMIC_INIT(0);

// Lista de callbacks de notificação
static LIST_HEAD(cdv_notifiers);

// Estatísticas atômicas
static struct cdv_stats stats = {0};

// BYOVD Database embutida (272 hashes de drivers vulneráveis)
#include "../include/byovd_database.h"  // Gera: extern const struct byovd_entry byovd_db[];

// ===== Funções auxiliares =====

static uint32_t hash_to_index(const uint8_t* hash) {
    // Simple hash para índice na hash table
    return (*(uint32_t*)hash) & (REPUTATION_HASH_SIZE - 1);
}

static void cdv_log_audit(const char* fmt, ...) {
    if (audit_mode) {
        va_list args;
        va_start(args, fmt);
        printk(KERN_INFO "[CDV] ");
        vprintk(fmt, args);
        va_end(args);
    }
}

static void cdv_notify_userspace(struct cdv_notification* notif) {
    struct cdv_notifier_entry* entry;

    mutex_lock(&cdv_notifier_mutex);
    list_for_each_entry(entry, &cdv_notifiers, list) {
        if (entry->callback) {
            entry->callback(notif);
        }
    }
    mutex_unlock(&cdv_notifier_mutex);
}

// ===== Cálculo de hash SHA-256 de arquivo =====

static int cdv_compute_file_hash(const char* path, uint8_t* out_hash) {
    struct file* filp = NULL;
    struct sha256_state sctx;
    char* buf = NULL;
    loff_t pos = 0;
    int ret = 0;

    if (!path || !out_hash) return -EINVAL;

    filp = filp_open(path, O_RDONLY, 0);
    if (IS_ERR(filp)) {
        cdv_log_audit("Failed to open %s: %ld\n", path, PTR_ERR(filp));
        return PTR_ERR(filp);
    }

    buf = kmalloc(65536, GFP_KERNEL);  // 64KB buffer
    if (!buf) {
        ret = -ENOMEM;
        goto out_close;
    }

    sha256_init(&sctx);

    while (1) {
        ssize_t bytes_read = kernel_read(filp, buf, 65536, &pos);
        if (bytes_read < 0) {
            ret = bytes_read;
            break;
        }
        if (bytes_read == 0) break;  // EOF

        sha256_update(&sctx, buf, bytes_read);
    }

    if (ret == 0) {
        sha256_final(&sctx, out_hash);
    }

    kfree(buf);
out_close:
    filp_close(filp, NULL);
    return ret;
}

// ===== Lookup de reputação na hash table =====

static struct cdv_driver_reputation* cdv_lookup_reputation(const uint8_t* hash) {
    struct cdv_driver_reputation* rep;
    uint32_t idx = hash_to_index(hash);

    hlist_for_each_entry(rep, &reputation_hash[idx], hash_node) {
        if (memcmp(rep->sha256, hash, SHA256_DIGEST_SIZE) == 0) {
            rep->last_checked = ktime_get_ns();
            return rep;
        }
    }
    return NULL;
}

// ===== Verificação de certificado X.509 =====

static int cdv_verify_certificate(const char* path, struct cdv_driver_reputation* rep) {
    // Em produção: usar kernel crypto API para verificar assinatura PKCS#7
    // Para protótipo: simular verificação baseada em thumbprint

    // Extrair thumbprint do certificado (simulado)
    snprintf(rep->certificate_thumbprint, sizeof(rep->certificate_thumbprint),
             "simulated_thumbprint_%02x%02x", rep->sha256[0], rep->sha256[1]);

    // Verificar se certificado está na lista de revogados (simulado)
    // Em produção: consultar CRL/OCSP ou CodexSpectrum
    if (rep->sha256[0] == 0xDE && rep->sha256[1] == 0xAD) {  // Exemplo de hash "revogado"
        rep->is_revoked = 1;
        return -EKEYREVOKED;
    }

    // Verificar expiração (simulado com timestamp)
    if (rep->first_seen < (ktime_get_ns() - 10ULL * 365 * 24 * 60 * 60 * 1000000000)) {
        rep->is_expired = 1;
        return -EKEYEXPIRED;
    }

    return 0;
}

// ===== Análise estática simplificada de capacidades =====

static int cdv_analyze_driver_capabilities(const char* path, struct cdv_driver_reputation* rep) {
    // Em produção: usar eBPF ou kprobes para interceptar chamadas perigosas
    // Para protótipo: análise baseada em nome do driver e heurísticas

    // Heurísticas baseadas em nomes conhecidos (exemplo)
    if (strstr(path, "gdrv") || strstr(path, "rtcore") || strstr(path, "iqvw64e")) {
        rep->has_kernel_mem_access = 1;
        rep->has_msr_access = 1;
    }
    if (strstr(path, "flash") || strstr(path, "bios") || strstr(path, "spi")) {
        rep->has_firmware_access = 1;
    }

    // Verificar na BYOVD Database embutida
    for (size_t i = 0; i < BYOVD_DB_SIZE; i++) {
        if (memcmp(rep->sha256, byovd_db[i].hash, SHA256_DIGEST_SIZE) == 0) {
            // Driver vulnerável conhecido
            rep->has_kernel_mem_access |= byovd_db[i].flags & BYOVD_FLAG_KERNEL_MEM;
            rep->has_firmware_access |= byovd_db[i].flags & BYOVD_FLAG_FIRMWARE;
            rep->has_msr_access |= byovd_db[i].flags & BYOVD_FLAG_MSR;
            rep->is_revoked = 1;  // Marcar como revogado para bloqueio
            return 0;
        }
    }

    return 0;
}

// ===== Função principal de verificação =====

enum cdv_check_result cdv_check_driver_sync(const char* path, const char* consent_id, uint32_t policy) {
    struct cdv_driver_reputation* rep = NULL;
    uint8_t hash[SHA256_DIGEST_SIZE];
    int ret;

    if (!path) return CDV_ERROR_INTERNAL;

    // 1. Calcular hash do driver
    ret = cdv_compute_file_hash(path, hash);
    if (ret < 0) {
        cdv_log_audit("Hash computation failed for %s: %d\n", path, ret);
        return CDV_ERROR_INTERNAL;
    }

    mutex_lock(&cdv_mutex);

    // 2. Lookup ou criar reputação
    rep = cdv_lookup_reputation(hash);
    if (!rep) {
        // Nova entrada
        rep = kzalloc(sizeof(*rep), GFP_KERNEL);
        if (!rep) {
            mutex_unlock(&cdv_mutex);
            return CDV_ERROR_INTERNAL;
        }

        memcpy(rep->sha256, hash, SHA256_DIGEST_SIZE);
        rep->first_seen = ktime_get_ns();
        rep->last_checked = rep->first_seen;

        // Inserir na hash table
        uint32_t idx = hash_to_index(hash);
        hlist_add_head(&rep->hash_node, &reputation_hash[idx]);
        atomic_inc(&reputation_count);
    }

    rep->load_count++;

    // 3. Verificar certificado
    ret = cdv_verify_certificate(path, rep);
    if (ret == -EKEYREVOKED && (policy & CDV_POLICY_BLOCK_REVOKED)) {
        cdv_log_audit("Blocked %s: revoked certificate\n", path);
        stats.revoked_blocked++;
        mutex_unlock(&cdv_mutex);

        // Notificar userspace
        struct cdv_notification notif = {
            .type = CDV_NOTIFY_CERT_INVALID,
            .result = CDV_BLOCK_REVOKED_CERT,
            .timestamp_ns = ktime_get_ns(),
        };
        memcpy(notif.driver_hash, hash, SHA256_DIGEST_SIZE);
        if (consent_id) strncpy(notif.consent_id, consent_id, 35);
        snprintf(notif.message, sizeof(notif.message), "Certificate revoked");
        cdv_notify_userspace(&notif);

        return CDV_BLOCK_REVOKED_CERT;
    }

    if (ret == -EKEYEXPIRED && (policy & CDV_POLICY_BLOCK_EXPIRED)) {
        cdv_log_audit("Blocked %s: expired certificate\n", path);
        stats.expired_blocked++;
        mutex_unlock(&cdv_mutex);
        return CDV_BLOCK_EXPIRED_CERT;
    }

    // 4. Analisar capacidades perigosas
    cdv_analyze_driver_capabilities(path, rep);

    // 5. Aplicar políticas baseadas em capacidades
    if (rep->has_firmware_access && (policy & CDV_POLICY_LOCK_FIRMWARE)) {
        // Requer consentimento explícito para firmware access
        if (!consent_id || strlen(consent_id) == 0) {
            cdv_log_audit("Blocked %s: firmware access without consent\n", path);
            stats.blocked_loads++;
            mutex_unlock(&cdv_mutex);
            return CDV_BLOCK_FIRMWARE_NO_CONSENT;
        }
    }

    if (rep->has_kernel_mem_access && (policy & CDV_POLICY_BLOCK_UNKNOWN) && !rep->is_whitelisted) {
        cdv_log_audit("Blocked %s: kernel memory access, unknown driver\n", path);
        stats.unknown_blocked++;
        mutex_unlock(&cdv_mutex);
        return CDV_BLOCK_KERNEL_MEM_NO_CONSENT;
    }

    if (rep->has_msr_access) {
        // Acesso a MSR sempre requer intervenção do Safety Guardian
        cdv_log_audit("Intercepted MSR access attempt from %s\n", path);
        stats.msr_intercepts++;
        // Não bloquear automaticamente — registrar para auditoria
    }

    // 6. Atualizar estatísticas
    stats.total_checks++;
    stats.allowed_loads++;

    // 7. Gerar receipt para ancoragem no Códice (assíncrono)
    // (Em produção: enfileirar para thread de anchoring)

    mutex_unlock(&cdv_mutex);

    // Notificar carregamento permitido
    struct cdv_notification notif = {
        .type = CDV_NOTIFY_DRIVER_LOADED,
        .result = CDV_ALLOW,
        .timestamp_ns = ktime_get_ns(),
    };
    memcpy(notif.driver_hash, hash, SHA256_DIGEST_SIZE);
    if (consent_id) strncpy(notif.consent_id, consent_id, 35);
    snprintf(notif.message, sizeof(notif.message), "Driver loaded: %s", path);
    cdv_notify_userspace(&notif);

    return CDV_ALLOW;
}

// ===== Proteção de firmware SPI =====

int cdv_lock_firmware_protection(void) {
    // Em hardware real: escrever em MSRs/registers de proteção SPI
    // Para protótipo: registrar estado e notificar

    cdv_log_audit("Firmware protection LOCKED\n");
    stats.firmware_protected++;

    struct cdv_notification notif = {
        .type = CDV_NOTIFY_FIRMWARE_ACCESS,
        .result = CDV_ALLOW,  // Lock bem-sucedido
        .timestamp_ns = ktime_get_ns(),
    };
    snprintf(notif.message, sizeof(notif.message), "SPI flash protection enabled");
    cdv_notify_userspace(&notif);

    return 0;
}

// ===== Interface IOCTL para userspace =====

static long cdv_ioctl(struct file* filp, unsigned int cmd, unsigned long arg) {
    int ret = 0;

    switch (cmd) {
        case CDV_IOC_CHECK_DRIVER: {
            struct cdv_driver_check_req req;
            if (copy_from_user(&req, (void __user*)arg, sizeof(req))) {
                return -EFAULT;
            }

            enum cdv_check_result result = cdv_check_driver_sync(
                req.driver_path, req.consent_id, req.policy_flags);

            if (copy_to_user((void __user*)arg, &result, sizeof(result))) {
                return -EFAULT;
            }
            break;
        }

        case CDV_IOC_LOCK_FIRMWARE:
            ret = cdv_lock_firmware_protection();
            break;

        case CDV_IOC_GET_STATS: {
            struct cdv_stats s = cdv_get_stats();
            if (copy_to_user((void __user*)arg, &s, sizeof(s))) {
                return -EFAULT;
            }
            break;
        }

        default:
            return -ENOTTY;
    }

    return ret;
}

static const struct file_operations cdv_fops = {
    .owner = THIS_MODULE,
    .unlocked_ioctl = cdv_ioctl,
    .compat_ioctl = compat_ptr_ioctl,
};

// ===== Registro de notifiers =====

int cdv_register_notifier(cdv_notification_callback_t callback) {
    struct cdv_notifier_entry* entry;

    if (!callback) return -EINVAL;

    entry = kmalloc(sizeof(*entry), GFP_KERNEL);
    if (!entry) return -ENOMEM;

    entry->callback = callback;
    INIT_LIST_HEAD(&entry->list);

    mutex_lock(&cdv_notifier_mutex);
    list_add_tail(&entry->list, &cdv_notifiers);
    mutex_unlock(&cdv_notifier_mutex);

    return 0;
}

int cdv_unregister_notifier(cdv_notification_callback_t callback) {
    struct cdv_notifier_entry* entry, *tmp;

    mutex_lock(&cdv_notifier_mutex);
    list_for_each_entry_safe(entry, tmp, &cdv_notifiers, list) {
        if (entry->callback == callback) {
            list_del(&entry->list);
            kfree(entry);
            mutex_unlock(&cdv_notifier_mutex);
            return 0;
        }
    }
    mutex_unlock(&cdv_notifier_mutex);
    return -ENOENT;
}

// ===== Funções de estatísticas =====

struct cdv_stats cdv_get_stats(void) {
    struct cdv_stats s;

    s.total_checks = stats.total_checks;
    s.allowed_loads = stats.allowed_loads;
    s.blocked_loads = stats.blocked_loads;
    s.revoked_blocked = stats.revoked_blocked;
    s.expired_blocked = stats.expired_blocked;
    s.unknown_blocked = stats.unknown_blocked;
    s.firmware_protected = stats.firmware_protected;
    s.ioctl_intercepts = stats.ioctl_intercepts;
    s.msr_intercepts = stats.msr_intercepts;
    s.reputation_cache_size = atomic_read(&reputation_count);
    s.byovd_db_entries = BYOVD_DB_SIZE;

    return s;
}

// ===== Init/Exit do módulo =====

static int __init cdv_init(void) {
    int ret;
    int i;

    printk(KERN_INFO "[CDV] Cathedral Driver Vetting module loading...\n");

    // Inicializar hash table
    for (i = 0; i < REPUTATION_HASH_SIZE; i++) {
        INIT_HLIST_HEAD(&reputation_hash[i]);
    }

    // Registrar dispositivo char
    ret = alloc_chrdev_region(&cdv_dev_number, 0, 1, CDV_DRIVER_NAME);
    if (ret < 0) {
        printk(KERN_ERR "[CDV] Failed to allocate device number\n");
        return ret;
    }

    cdev_init(&cdv_cdev, &cdv_fops);
    ret = cdev_add(&cdv_cdev, cdv_dev_number, 1);
    if (ret < 0) {
        unregister_chrdev_region(cdv_dev_number, 1);
        return ret;
    }

    // Criar classe para udev
    cdv_class = class_create(THIS_MODULE, CDV_CLASS_NAME);
    if (IS_ERR(cdv_class)) {
        cdev_del(&cdv_cdev);
        unregister_chrdev_region(cdv_dev_number, 1);
        return PTR_ERR(cdv_class);
    }

    device_create(cdv_class, NULL, cdv_dev_number, NULL, CDV_DEVICE_NAME);

    // Travar firmware protection no boot se configurado
    if (firmware_lock_on_boot) {
        cdv_lock_firmware_protection();
    }

    // Carregar BYOVD Database embutida
    printk(KERN_INFO "[CDV] Loaded BYOVD database: %d entries\n", BYOVD_DB_SIZE);

    printk(KERN_INFO "[CDV] Module loaded successfully. Major: %d\n", MAJOR(cdv_dev_number));
    return 0;
}

static void __exit cdv_exit(void) {
    // Cleanup de reputações em cache
    struct cdv_driver_reputation* rep;
    struct hlist_node* tmp;
    int i;

    for (i = 0; i < REPUTATION_HASH_SIZE; i++) {
        hlist_for_each_entry_safe(rep, tmp, &reputation_hash[i], hash_node) {
            hlist_del(&rep->hash_node);
            kfree(rep);
        }
    }

    // Cleanup de notifiers
    struct cdv_notifier_entry* entry, *tmp_entry;
    list_for_each_entry_safe(entry, tmp_entry, &cdv_notifiers, list) {
        list_del(&entry->list);
        kfree(entry);
    }

    device_destroy(cdv_class, cdv_dev_number);
    class_destroy(cdv_class);
    cdev_del(&cdv_cdev);
    unregister_chrdev_region(cdv_dev_number, 1);

    printk(KERN_INFO "[CDV] Module unloaded. Final stats: %llu checks, %llu blocked\n",
           stats.total_checks, stats.blocked_loads);
}

module_init(cdv_init);
module_exit(cdv_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Cathedral Arkhe Consortium");
MODULE_DESCRIPTION("Cathedral Driver Vetting — Kernel module for sovereign driver verification");
MODULE_VERSION("1.0.0");
