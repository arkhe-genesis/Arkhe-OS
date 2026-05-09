#ifndef CDV_H
#define CDV_H

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include <linux/notifier.h>
#include <linux/security.h>
#include <linux/module_signature.h>
#include <crypto/sha2.h>

#define CDV_DRIVER_NAME "cdv"
#define CDV_CLASS_NAME "cathedral_driver_vetting"
#define CDV_DEVICE_NAME "cdv0"
#define CDV_MAJOR 0  // Dynamic allocation

// IOCTL commands para interação userspace-kernel
#define CDV_IOC_MAGIC 'C'
#define CDV_IOC_CHECK_DRIVER _IOWR(CDV_IOC_MAGIC, 1, struct cdv_driver_check_req)
#define CDV_IOC_QUERY_REPUTATION _IOWR(CDV_IOC_MAGIC, 2, struct cdv_reputation_query)
#define CDV_IOC_LOCK_FIRMWARE _IO(CDV_IOC_MAGIC, 3)
#define CDV_IOC_GET_STATS _IOR(CDV_IOC_MAGIC, 4, struct cdv_stats)

// Estrutura de requisição de verificação de driver
struct cdv_driver_check_req {
    char driver_path[256];      // Caminho do driver a verificar
    char consent_id[36];         // UUID do consentimento associado
    uint8_t expected_hash[SHA256_DIGEST_SIZE];  // Hash esperado (opcional)
    uint32_t policy_flags;       // Políticas a aplicar (bitmask)
};

// Políticas de verificação (bitmask)
#define CDV_POLICY_BLOCK_REVOKED    (1 << 0)
#define CDV_POLICY_BLOCK_EXPIRED    (1 << 1)
#define CDV_POLICY_BLOCK_UNKNOWN    (1 << 2)
#define CDV_POLICY_REQUIRE_HVCI     (1 << 3)
#define CDV_POLICY_AUDIT_IOCTL      (1 << 4)
#define CDV_POLICY_LOCK_FIRMWARE    (1 << 5)

// Resultado da verificação
enum cdv_check_result {
    CDV_ALLOW = 0,
    CDV_BLOCK_REVOKED_CERT,
    CDV_BLOCK_EXPIRED_CERT,
    CDV_BLOCK_UNKNOWN_DRIVER,
    CDV_BLOCK_FIRMWARE_NO_CONSENT,
    CDV_BLOCK_KERNEL_MEM_NO_CONSENT,
    CDV_BLOCK_MSR_ACCESS,
    CDV_ERROR_INTERNAL,
};

// Estrutura de reputação de driver (cache kernel)
struct cdv_driver_reputation {
    uint8_t sha256[SHA256_DIGEST_SIZE];  // Hash do driver
    char certificate_thumbprint[64];      // Thumbprint do certificado
    uint64_t first_seen;                   // Timestamp de primeira detecção
    uint64_t last_checked;                 // Última verificação
    uint32_t load_count;                   // Quantas vezes foi carregado
    uint32_t block_count;                  // Quantas vezes foi bloqueado

    // Flags de capacidade perigosa
    uint8_t has_firmware_access : 1;
    uint8_t has_kernel_mem_access : 1;
    uint8_t has_msr_access : 1;
    uint8_t has_cr_access : 1;
    uint8_t is_revoked : 1;
    uint8_t is_expired : 1;
    uint8_t is_whitelisted : 1;

    // Ancoragem no Códice
    char codex_anchor[64];

    // Link para lista hash table
    struct hlist_node hash_node;
};

// Estatísticas para dashboard/monitoramento
struct cdv_stats {
    uint64_t total_checks;
    uint64_t allowed_loads;
    uint64_t blocked_loads;
    uint64_t revoked_blocked;
    uint64_t expired_blocked;
    uint64_t unknown_blocked;
    uint64_t firmware_protected;
    uint64_t ioctl_intercepts;
    uint64_t msr_intercepts;
    uint32_t reputation_cache_size;
    uint32_t byovd_db_entries;
};

// Callbacks de notificação para integração com userspace
struct cdv_notification {
    enum {
        CDV_NOTIFY_DRIVER_LOADED,
        CDV_NOTIFY_DRIVER_BLOCKED,
        CDV_NOTIFY_FIRMWARE_ACCESS,
        CDV_NOTIFY_MSR_ACCESS,
        CDV_NOTIFY_CERT_INVALID,
    } type;

    uint8_t driver_hash[SHA256_DIGEST_SIZE];
    char consent_id[36];
    uint64_t timestamp_ns;
    enum cdv_check_result result;
    char message[128];
};

typedef int (*cdv_notification_callback_t)(struct cdv_notification*);

// Entry for notifier list
struct cdv_notifier_entry {
    cdv_notification_callback_t callback;
    struct list_head list;
};

// API principal do módulo
int cdv_register_notifier(cdv_notification_callback_t callback);
int cdv_unregister_notifier(cdv_notification_callback_t callback);
enum cdv_check_result cdv_check_driver_sync(const char* path, const char* consent_id, uint32_t policy);
int cdv_lock_firmware_protection(void);
struct cdv_stats cdv_get_stats(void);

#endif // CDV_H
