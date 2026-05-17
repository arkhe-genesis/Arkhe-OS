/*
 * ARKHE OS Substrato ∞: ZFS Integrity Monitor
 * Canon: ∞.Ω.∇+++.∞.zfs.monitor
 * Função: Monitorar integridade de datasets e reportar anomalias
 * Linguagem: C (userspace, links against libzfs)
 */

#define _WITH_GETLINE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <libzfs.h>
#include <sys/time.h>
#include <sha3/sha3.h>

#define MONITOR_INTERVAL_SEC 60
#define HASH_CHUNK_SIZE (1024 * 1024)  /* 1MB chunks for hashing */

struct zfs_integrity_record {
    char dataset_name[256];
    char snapshot_name[256];
    uint8_t content_hash[32];  /* SHA3-256 */
    uint64_t used_bytes;
    uint64_t referenced_bytes;
    time_t last_verified;
    int corruption_detected;
};

static libzfs_handle_t *zfs_handle = NULL;
static FILE *integrity_log = NULL;

static void
log_integrity(const char *fmt, ...)
{
    va_list ap;
    time_t now = time(NULL);
    char timestamp[64];

    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", localtime(&now));
    fprintf(integrity_log, "[%s] ", timestamp);

    va_start(ap, fmt);
    vfprintf(integrity_log, fmt, ap);
    va_end(ap);
    fprintf(integrity_log, "\n");
    fflush(integrity_log);
}

static int
compute_dataset_hash(const char *dataset_path, uint8_t *out_hash)
{
    SHA3_256_CTX ctx;
    sha3_256_init(&ctx);

    FILE *f = fopen(dataset_path, "rb");
    if (!f) {
        log_integrity("ERROR: Cannot open %s for hashing", dataset_path);
        return -1;
    }

    unsigned char buffer[HASH_CHUNK_SIZE];
    size_t bytes_read;

    while ((bytes_read = fread(buffer, 1, HASH_CHUNK_SIZE, f)) > 0) {
        sha3_256_update(&ctx, buffer, bytes_read);
    }

    fclose(f);
    sha3_256_final(&ctx, out_hash);

    return 0;
}

static int
verify_dataset_integrity(zfs_handle_t *zhp, struct zfs_integrity_record *record)
{
    char mountpoint[ZFS_MAXPROPLEN];

    /* Get mountpoint */
    if (zfs_prop_get(zhp, ZFS_PROP_MOUNTPOINT, mountpoint,
                     sizeof(mountpoint), NULL, NULL, 0, B_FALSE) != 0) {
        log_integrity("ERROR: Cannot get mountpoint for %s",
                     zfs_get_name(zhp));
        return -1;
    }

    /* Skip if not mounted */
    if (strcmp(mountpoint, "-") == 0 || access(mountpoint, R_OK) != 0) {
        return 0;  /* Not an error, just skip */
    }

    /* Compute hash of dataset content */
    uint8_t current_hash[32];
    if (compute_dataset_hash(mountpoint, current_hash) != 0) {
        return -1;
    }

    /* Compare with stored hash if available */
    if (record->last_verified > 0) {
        if (memcmp(current_hash, record->content_hash, 32) != 0) {
            log_integrity("CORRUPTION DETECTED in %s: hash mismatch",
                         zfs_get_name(zhp));
            record->corruption_detected = 1;
            return 1;  /* Corruption detected */
        }
    }

    /* Update record */
    memcpy(record->content_hash, current_hash, 32);
    record->last_verified = time(NULL);

    /* Get ZFS properties */
    record->used_bytes = zfs_prop_get_int(zhp, ZFS_PROP_USED);
    record->referenced_bytes = zfs_prop_get_int(zhp, ZFS_PROP_REFERENCED);

    log_integrity("Verified integrity: %s (used: %lu MB, hash: %.8s...)",
                 zfs_get_name(zhp),
                 (unsigned long)(record->used_bytes / (1024*1024)),
                 record->content_hash);

    return 0;
}

static int
snapshot_callback(zfs_handle_t *zhp, void *data)
{
    if (zfs_get_type(zhp) == ZFS_TYPE_SNAPSHOT) {
        struct zfs_integrity_record *record = (struct zfs_integrity_record *)data;

        strlcpy(record->snapshot_name, zfs_get_name(zhp),
                sizeof(record->snapshot_name));

        /* Verify snapshot integrity */
        verify_dataset_integrity(zhp, record);
    }
    return ZFS_ITER_CONTINUE;
}

int
main(int argc, char *argv[])
{
    const char *base_dataset = "zroot/arkhe";

    /* Initialize libzfs */
    zfs_handle = libzfs_init();
    if (!zfs_handle) {
        fprintf(stderr, "ERROR: Failed to initialize libzfs\n");
        return 1;
    }

    /* Open integrity log */
    integrity_log = fopen("/var/log/arkhe_zfs_integrity.log", "a");
    if (!integrity_log) {
        fprintf(stderr, "WARNING: Cannot open integrity log, using stderr\n");
        integrity_log = stderr;
    }

    log_integrity("ZFS Integrity Monitor started");

    /* Main monitoring loop */
    while (1) {
        zfs_handle_t *base_zhp = zfs_open(zfs_handle, base_dataset,
                                          ZFS_TYPE_FILESYSTEM);
        if (!base_zhp) {
            log_integrity("ERROR: Cannot open dataset %s", base_dataset);
            sleep(MONITOR_INTERVAL_SEC);
            continue;
        }

        struct zfs_integrity_record record = {0};
        strlcpy(record.dataset_name, base_dataset, sizeof(record.dataset_name));

        /* Verify base dataset */
        int result = verify_dataset_integrity(base_zhp, &record);
        if (result > 0) {
            /* Corruption detected - trigger alert */
            log_integrity("ALERT: Initiating recovery procedure for %s",
                         base_dataset);
            /* In production: trigger ZFS rollback or notify operator */
        }

        /* Iterate over child datasets */
        zfs_iter_filesystems(base_zhp, snapshot_callback, &record);

        zfs_close(base_zhp);

        /* Sleep until next interval */
        sleep(MONITOR_INTERVAL_SEC);
    }

    libzfs_fini(zfs_handle);
    if (integrity_log != stderr) {
        fclose(integrity_log);
    }

    return 0;
}
