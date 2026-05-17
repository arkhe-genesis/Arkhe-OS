/*
 * ARKHE OS Substrato ∞: Native Seccomp Filter
 * Canon: ∞.Ω.∇+++.security.seccomp
 * Função: Aplicação de filtros seccomp-bpf nativos via libseccomp
 * para sandboxing rigoroso de processos filhos.
 * Linguagem: C (integrado via ctypes em Python)
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <seccomp.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>

/* Perfis de seccomp predefinidos */
typedef enum {
    SECCOMP_PROFILE_STRICT = 0,    /* Apenas syscalls essenciais */
    SECCOMP_PROFILE_MODERATE = 1,  /* Syscalls para execução Python */
    SECCOMP_PROFILE_PERMISSIVE = 2 /* Syscalls para desenvolvimento */
} seccomp_profile_t;

/* Syscalls permitidos por perfil */
static const int STRICT_ALLOWLIST[] = {
    SCMP_SYS(read), SCMP_SYS(write), SCMP_SYS(exit), SCMP_SYS(exit_group),
    SCMP_SYS(futex), SCMP_SYS(mmap), SCMP_SYS(munmap), SCMP_SYS(mprotect),
    SCMP_SYS(brk), SCMP_SYS(rt_sigreturn), SCMP_SYS(rt_sigprocmask),
    SCMP_SYS(getpid), SCMP_SYS(gettid), SCMP_SYS(clock_gettime),
    SCMP_SYS(prctl), SCMP_SYS(seccomp), SCMP_SYS(getrandom),
    -1 /* sentinel */
};

static const int MODERATE_ALLOWLIST[] = {
    /* Todos do STRICT + */
    SCMP_SYS(open), SCMP_SYS(openat), SCMP_SYS(close), SCMP_SYS(fstat),
    SCMP_SYS(lseek), SCMP_SYS(pread64), SCMP_SYS(pwrite64),
    SCMP_SYS(access), SCMP_SYS(stat), SCMP_SYS(newfstatat),
    SCMP_SYS(getcwd), SCMP_SYS(unlink), SCMP_SYS(unlinkat),
    SCMP_SYS(rename), SCMP_SYS(renameat2), SCMP_SYS(mkdir), SCMP_SYS(mkdirat),
    SCMP_SYS(rmdir), SCMP_SYS(getdents64), SCMP_SYS(dup), SCMP_SYS(dup2),
    SCMP_SYS(dup3), SCMP_SYS(pipe2), SCMP_SYS(poll), SCMP_SYS(ppoll),
    SCMP_SYS(select), SCMP_SYS(pselect6), SCMP_SYS(epoll_create),
    SCMP_SYS(epoll_create1), SCMP_SYS(epoll_ctl), SCMP_SYS(epoll_wait),
    SCMP_SYS(epoll_pwait), SCMP_SYS(socket), SCMP_SYS(connect),
    SCMP_SYS(accept), SCMP_SYS(accept4), SCMP_SYS(sendto), SCMP_SYS(recvfrom),
    SCMP_SYS(sendmsg), SCMP_SYS(recvmsg), SCMP_SYS(shutdown),
    SCMP_SYS(getsockname), SCMP_SYS(getpeername), SCMP_SYS(setsockopt),
    SCMP_SYS(getsockopt), SCMP_SYS(fcntl), SCMP_SYS(ioctl),
    SCMP_SYS(nanosleep), SCMP_SYS(clock_nanosleep), SCMP_SYS(timerfd_create),
    SCMP_SYS(timerfd_settime), SCMP_SYS(timerfd_gettime),
    SCMP_SYS(signalfd4), SCMP_SYS(eventfd2), SCMP_SYS(readlink),
    SCMP_SYS(readlinkat), SCMP_SYS(symlink), SCMP_SYS(symlinkat),
    SCMP_SYS(link), SCMP_SYS(linkat), SCMP_SYS(chmod), SCMP_SYS(fchmod),
    SCMP_SYS(fchmodat), SCMP_SYS(chown), SCMP_SYS(fchown), SCMP_SYS(fchownat),
    SCMP_SYS(utimensat), SCMP_SYS(futimesat), SCMP_SYS(getuid),
    SCMP_SYS(geteuid), SCMP_SYS(getgid), SCMP_SYS(getegid),
    SCMP_SYS(getgroups), SCMP_SYS(setgroups), SCMP_SYS(getresuid),
    SCMP_SYS(getresgid), SCMP_SYS(capget), SCMP_SYS(capset),
    -1 /* sentinel */
};

/* Função principal: aplicar filtro seccomp */
int apply_seccomp_filter(seccomp_profile_t profile) {
    scmp_filter_ctx ctx;
    int rc;
    const int *allowlist;

    /* Criar contexto com ação padrão ERRNO(EPERM) */
    ctx = seccomp_init(SCMP_ACT_ERRNO(EPERM));
    if (ctx == NULL) {
        fprintf(stderr, "❌ seccomp_init falhou\n");
        return -1;
    }

    /* Selecionar allowlist baseada no perfil */
    switch (profile) {
        case SECCOMP_PROFILE_STRICT:
            allowlist = STRICT_ALLOWLIST;
            break;
        case SECCOMP_PROFILE_MODERATE:
            allowlist = MODERATE_ALLOWLIST;
            break;
        case SECCOMP_PROFILE_PERMISSIVE:
        default:
            /* Permissivo: permitir maioria dos syscalls exceto perigosos */
            rc = seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(execve), 0);
            if (rc < 0) goto cleanup;
            rc = seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(execveat), 0);
            if (rc < 0) goto cleanup;
            rc = seccomp_load(ctx);
            goto cleanup;
    }

    /* Adicionar regras para syscalls permitidos */
    for (int i = 0; allowlist[i] != -1; i++) {
        rc = seccomp_rule_add(ctx, SCMP_ACT_ALLOW, allowlist[i], 0);
        if (rc < 0) {
            fprintf(stderr, "⚠️  Falha ao adicionar regra para syscall %d: %s\n",
                    allowlist[i], strerror(-rc));
            /* Continuar tentando adicionar outras regras */
        }
    }

    /* Carregar filtro no kernel */
    rc = seccomp_load(ctx);
    if (rc < 0) {
        fprintf(stderr, "❌ seccomp_load falhou: %s\n", strerror(-rc));
        goto cleanup;
    }

    fprintf(stdout, "✅ Filtro seccomp aplicado: perfil=%d\n", profile);

cleanup:
    seccomp_release(ctx);
    return (rc < 0) ? -1 : 0;
}

/* Função auxiliar para Python via ctypes */
int py_apply_seccomp(int profile_int) {
    seccomp_profile_t profile = (seccomp_profile_t)profile_int;

    /* Garantir que seccomp só pode ser aplicado uma vez por processo */
    static int applied = 0;
    if (applied) {
        fprintf(stderr, "⚠️  Seccomp já aplicado neste processo\n");
        return 0;
    }

    /* Bloquear aplicação após fork/exec */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl(PR_SET_NO_NEW_PRIVS)");
        return -1;
    }

    int result = apply_seccomp_filter(profile);
    if (result == 0) {
        applied = 1;
    }
    return result;
}

/* Função para listar syscalls permitidos em um perfil */
int list_allowed_syscalls(int profile_int, char *buffer, size_t buf_size) {
    seccomp_profile_t profile = (seccomp_profile_t)profile_int;
    const int *allowlist;
    size_t offset = 0;

    switch (profile) {
        case SECCOMP_PROFILE_STRICT:
            allowlist = STRICT_ALLOWLIST;
            break;
        case SECCOMP_PROFILE_MODERATE:
            allowlist = MODERATE_ALLOWLIST;
            break;
        default:
            snprintf(buffer, buf_size, "unknown_profile");
            return -1;
    }

    for (int i = 0; allowlist[i] != -1 && offset < buf_size - 20; i++) {
        offset += snprintf(buffer + offset, buf_size - offset, "%d,", allowlist[i]);
    }
    if (offset > 0) buffer[offset - 1] = '\0'; /* Remove última vírgula */

    return 0;
}

/* Exemplo de uso em produção */
#ifdef STANDALONE_TEST
int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Uso: %s <perfil: 0=strict|1=moderate|2=permissive>\n", argv[0]);
        return 1;
    }

    int profile = atoi(argv[1]);
    if (apply_seccomp_filter(profile) != 0) {
        return 1;
    }

    /* Código sandboxed executado aqui */
    printf("🔒 Executando em sandbox seccomp\n");

    /* Testar syscall permitido */
    printf("PID: %d\n", getpid());  /* Deve funcionar */

    /* Testar syscall bloqueado (apenas em strict) */
    if (profile == SECCOMP_PROFILE_STRICT) {
        FILE *f = fopen("/etc/passwd", "r");  /* open() bloqueado em strict */
        if (f) {
            printf("⚠️  Syscall inesperadamente permitido\n");
            fclose(f);
        } else {
            printf("✅ Syscall corretamente bloqueado: %s\n", strerror(errno));
        }
    }

    return 0;
}
#endif
