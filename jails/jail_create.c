/*
 * ARKHE OS Substrato ∞: Jail Creation Wrapper
 * Canon: ∞.Ω.∇+++.∞.jails.create
 * Função: Criar jails com configurações de segurança ARKHE
 * Linguagem: C (userspace, uses jail(2) syscall)
 */

#define _WITH_GETLINE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/jail.h>
#include <sys/param.h>
#include <sys/mount.h>
#include <sys/resource.h>
#include <sys/rctl.h>
#include <libutil.h>
#include <sha3/sha3.h>
#include <sys/stat.h>

#define ARKHE_JAIL_PREFIX "arkhe_"
#define MAX_JAIL_PARAMS 64
#define CAPSICUM_ENTRYPOINT "/usr/local/bin/arkhe_capsicum_entry"

struct arkhe_jail_config {
    char name[64];
    char path[256];
    char ip4_addr[64];
    char hostname[64];
    int memory_limit_mb;
    int cpu_limit_pct;
    int allow_raw_sockets;
    int enable_capsicum;
    char *mount_fstab;  /* Optional fstab for mounts */
};

static int
parse_jail_config(const char *config_file, struct arkhe_jail_config *cfg)
{
    FILE *f = fopen(config_file, "r");
    if (!f) {
        perror("fopen");
        return -1;
    }

    char *line = NULL;
    size_t linecap = 0;
    ssize_t linelen;

    while ((linelen = getline(&line, &linecap, f)) > 0) {
        /* Skip comments and empty lines */
        if (line[0] == '#' || line[0] == '\n') continue;

        /* Remove newline */
        line[strcspn(line, "\n")] = 0;

        /* Parse key=value */
        char *key = strtok(line, "=");
        char *value = strtok(NULL, "=");
        if (!key || !value) continue;

        if (strcmp(key, "name") == 0) {
            snprintf(cfg->name, sizeof(cfg->name), "%s%s",
                     ARKHE_JAIL_PREFIX, value);
        } else if (strcmp(key, "path") == 0) {
            strlcpy(cfg->path, value, sizeof(cfg->path));
        } else if (strcmp(key, "ip4_addr") == 0) {
            strlcpy(cfg->ip4_addr, value, sizeof(cfg->ip4_addr));
        } else if (strcmp(key, "hostname") == 0) {
            strlcpy(cfg->hostname, value, sizeof(cfg->hostname));
        } else if (strcmp(key, "memory_limit_mb") == 0) {
            cfg->memory_limit_mb = atoi(value);
        } else if (strcmp(key, "cpu_limit_pct") == 0) {
            cfg->cpu_limit_pct = atoi(value);
        } else if (strcmp(key, "allow_raw_sockets") == 0) {
            cfg->allow_raw_sockets = (strcmp(value, "1") == 0);
        } else if (strcmp(key, "enable_capsicum") == 0) {
            cfg->enable_capsicum = (strcmp(value, "1") == 0);
        } else if (strcmp(key, "mount_fstab") == 0) {
            cfg->mount_fstab = strdup(value);
        }
    }

    free(line);
    fclose(f);
    return 0;
}

static int
apply_resource_limits(const char *jail_name, const struct arkhe_jail_config *cfg)
{
    /* Apply memory limit via rctl */
    if (cfg->memory_limit_mb > 0) {
        char rule[256];
        snprintf(rule, sizeof(rule),
                 "jail:%s:memoryuse:deny=%dM",
                 jail_name, cfg->memory_limit_mb);

        if (rctl_add_rule(rule, NULL, 0) != 0) {
            perror("rctl_add_rule (memory)");
            return -1;
        }
    }

    /* Apply CPU limit via rctl */
    if (cfg->cpu_limit_pct > 0 && cfg->cpu_limit_pct < 100) {
        char rule[256];
        snprintf(rule, sizeof(rule),
                 "jail:%s:pcpu:deny=%d",
                 jail_name, cfg->cpu_limit_pct);

        if (rctl_add_rule(rule, NULL, 0) != 0) {
            perror("rctl_add_rule (cpu)");
            return -1;
        }
    }

    return 0;
}

static int
setup_capsicum_entry(const char *jail_path, const struct arkhe_jail_config *cfg)
{
    if (!cfg->enable_capsicum) return 0;

    /* Create capsicum entrypoint script */
    char entrypoint[512];
    snprintf(entrypoint, sizeof(entrypoint),
             "%s%s", jail_path, CAPSICUM_ENTRYPOINT);

    FILE *f = fopen(entrypoint, "w");
    if (!f) {
        perror("fopen entrypoint");
        return -1;
    }

    fprintf(f, "#!/bin/sh\n");
    fprintf(f, "# ARKHE Capsicum Entrypoint\n");
    fprintf(f, "# Canon: ∞.Ω.∇+++.∞.jails.capsicum\n\n");
    fprintf(f, "# Enter capability mode before executing agent\n");
    fprintf(f, "exec /usr/local/bin/cap_enter_wrapper \"$@\"\n");
    fclose(f);

    chmod(entrypoint, 0755);

    /* Create cap_enter_wrapper in C (separate binary) */
    /* This wrapper calls cap_enter() then execs the actual agent */

    return 0;
}

int
main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <jail_config.conf>\n", argv[0]);
        return 1;
    }

    struct arkhe_jail_config cfg = {0};
    if (parse_jail_config(argv[1], &cfg) != 0) {
        fprintf(stderr, "ERROR: Failed to parse config file\n");
        return 1;
    }

    /* Validate required fields */
    if (!cfg.name[0] || !cfg.path[0] || !cfg.ip4_addr[0]) {
        fprintf(stderr, "ERROR: Missing required config fields\n");
        return 1;
    }

    printf("[JailCreate] Creating jail: %s\n", cfg.name);

    /* Prepare jail parameters */
    struct iovec iov[MAX_JAIL_PARAMS];
    int niov = 0;

    /* Required parameters */
    iov[niov].iov_base = "path";
    iov[niov].iov_len = strlen("path") + 1;
    iov[niov+1].iov_base = cfg.path;
    iov[niov+1].iov_len = strlen(cfg.path) + 1;
    niov += 2;

    iov[niov].iov_base = "host.hostname";
    iov[niov].iov_len = strlen("host.hostname") + 1;
    iov[niov+1].iov_base = cfg.hostname[0] ? cfg.hostname : cfg.name;
    iov[niov+1].iov_len = strlen(iov[niov+1].iov_base) + 1;
    niov += 2;

    iov[niov].iov_base = "ip4.addr";
    iov[niov].iov_len = strlen("ip4.addr") + 1;
    iov[niov+1].iov_base = cfg.ip4_addr;
    iov[niov+1].iov_len = strlen(cfg.ip4_addr) + 1;
    niov += 2;

    iov[niov].iov_base = "exec.start";
    iov[niov].iov_len = strlen("exec.start") + 1;
    iov[niov+1].iov_base = "/bin/sh /etc/rc";
    iov[niov+1].iov_len = strlen("/bin/sh /etc/rc") + 1;
    niov += 2;

    iov[niov].iov_base = "exec.stop";
    iov[niov].iov_len = strlen("exec.stop") + 1;
    iov[niov+1].iov_base = "/bin/sh /etc/rc.shutdown";
    iov[niov+1].iov_len = strlen("/bin/sh /etc/rc.shutdown") + 1;
    niov += 2;

    /* Security parameters */
    iov[niov].iov_base = "allow.raw_sockets";
    iov[niov].iov_len = strlen("allow.raw_sockets") + 1;
    iov[niov+1].iov_base = cfg.allow_raw_sockets ? "1" : "0";
    iov[niov+1].iov_len = 2;
    niov += 2;

    iov[niov].iov_base = "enforce_statfs";
    iov[niov].iov_len = strlen("enforce_statfs") + 1;
    iov[niov+1].iov_base = "2";  /* Most restrictive */
    iov[niov+1].iov_len = 2;
    niov += 2;

    iov[niov].iov_base = "children.max";
    iov[niov].iov_len = strlen("children.max") + 1;
    iov[niov+1].iov_base = "10";  /* Limit nested jails */
    iov[niov+1].iov_len = 3;
    niov += 2;

    iov[niov].iov_base = "securelevel";
    iov[niov].iov_len = strlen("securelevel") + 1;
    iov[niov+1].iov_base = "3";  /* Highest securelevel */
    iov[niov+1].iov_len = 2;
    niov += 2;

    /* Create the jail */
    int jailid = jail(iov, niov);
    if (jailid < 0) {
        perror("jail");
        return 1;
    }

    printf("[JailCreate] Jail created with ID: %d\n", jailid);

    /* Apply resource limits */
    if (apply_resource_limits(cfg.name, &cfg) != 0) {
        fprintf(stderr, "WARNING: Failed to apply resource limits\n");
    }

    /* Setup Capsicum entrypoint if enabled */
    if (setup_capsicum_entry(cfg.path, &cfg) != 0) {
        fprintf(stderr, "WARNING: Failed to setup Capsicum entrypoint\n");
    }

    /* Log creation to TemporalChain (via character device or socket) */
    /* arkhe_log_to_temporalchain(cfg.name, jailid); */

    printf("[JailCreate] Jail %s ready\n", cfg.name);
    return 0;
}
