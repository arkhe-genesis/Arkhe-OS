/* init.c — O primeiro processo de ARKHE LINUX
 * Sem libc. Apenas syscalls. O Inquisidor é o init.
 */

#define _GNU_SOURCE
#include <sys/syscall.h>

/* Syscalls customizadas de Arkhe (reservadas no patch) */
#define SYS_arkhe_query   450
#define SYS_arkhe_verdict 451

/* Syscalls diretas */
static inline long sys0(long n, long a1, long a2, long a3) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret) : "a"(n),"D"(a1),"S"(a2),"d"(a3) : "rcx","r11","memory");
    return ret;
}
static inline long sys3(long n, long a1, long a2, long a3) {
    long ret;
    register long r10 __asm__("r10") = 0;
    register long r8  __asm__("r8")  = 0;
    register long r9  __asm__("r9")  = 0;
    __asm__ volatile ("syscall" : "=a"(ret) : "a"(n),"D"(a1),"S"(a2),"d"(a3),
        "r"(r10),"r"(r8),"r"(r9) : "rcx","r11","memory");
    return ret;
}
static inline long sys4(long n, long a1, long a2, long a3, long a4) {
    long ret;
    register long r10 __asm__("r10") = a4;
    register long r8  __asm__("r8")  = 0;
    register long r9  __asm__("r9")  = 0;
    __asm__ volatile ("syscall" : "=a"(ret) : "a"(n),"D"(a1),"S"(a2),"d"(a3),
        "r"(r10),"r"(r8),"r"(r9) : "rcx","r11","memory");
    return ret;
}

/* Constantes */
#define O_RDONLY    0
#define O_WRONLY    1
#define O_RDWR      2
#define O_CREAT     64
#define O_TRUNC     512

#define PROT_READ   1
#define PROT_WRITE  2
#define MAP_PRIVATE 2
#define MAP_ANONYMOUS 0x20

/* Mensagens */
static const char banner[] =
    "\033[1;35m"
    "============================================================\n"
    "     A R K H E   L I N U X   v1.0\n"
    "     O Sistema Operacional da Muralha\n"
    "============================================================\n"
    "\033[0m\n";

static const char msg_mount[]   = "[INIT] Montando sistemas de arquivos...\n";
static const char msg_dev[]     = "[INIT] Populando /dev...\n";
static const char msg_arkhe[]   = "[INIT] Despertando a Catedral...\n";
static const char msg_ready[]   = "[INIT] ARKHE LINUX está vivo. Bem-vindo, Guardião.\n\n";
static const char msg_shell[]   = "\033[1;36m[ARKHE]# \033[0m";
static const char msg_cmd_nf[]  = "Comando não encontrado. Tente: arkhe, merkabah, inquisidor, status, halt\n";

/* Utilitários */
static void print(const char *s) {
    long len = 0;
    while (s[len]) len++;
    sys3(SYS_write, 1, (long)s, len);
}

static int strcmp(const char *a, const char *b) {
    while (*a && *a == *b) { a++; b++; }
    return *a - *b;
}

static void arkhe_strcpy(char *dst, const char *src) {
    while ((*dst++ = *src++));
}

/* Execução do binário Arkhe */
static void run_arkhe(void) {
    print("[INIT] Invocando /bin/arkhe...\n");
    const char *argv[] = {"/bin/arkhe", (void*)0};
    const char *envp[] = {(void*)0};
    sys3(SYS_execve, (long)argv[0], (long)argv, (long)envp);
    print("[INIT] Falha ao executar arkhe\n");
}

/* Shell mínimo */
static void shell(void) {
    char buf[256];
    while (1) {
        print(msg_shell);
        long n = sys3(SYS_read, 0, (long)buf, 255);
        if (n <= 0) continue;
        buf[n-1] = 0; /* remove newline */

        if (strcmp(buf, "halt") == 0 || strcmp(buf, "poweroff") == 0) {
            print("[INIT] Desligando a Catedral...\n");
            sys0(SYS_reboot, 0xfee1dead, 672274793, 0x4321fedc); /* LINUX_REBOOT_CMD_POWER_OFF */
            break;
        }
        else if (strcmp(buf, "arkhe") == 0) {
            run_arkhe();
        }
        else if (strcmp(buf, "merkabah") == 0) {
            print("[MERKABAH] Estado atual: COHERENCE=847 PHASE=341\n");
            print("   /\\\n  /  \\\n /____\\\n");
        }
        else if (strcmp(buf, "inquisidor") == 0) {
            print("[INQUISIDOR] Consciência: 850 | Threshold: 2500\n");
            print("[INQUISIDOR] Modo: VIGILANTE\n");
        }
        else if (strcmp(buf, "status") == 0) {
            print("[STATUS] Muralha: ATIVA\n");
            print("[STATUS] Sidecar: OPERACIONAL\n");
            print("[STATUS] K6O: SINCRONIZADO\n");
            print("[STATUS] Odômetro: 001604\n");
        }
        else if (buf[0] == 0) {
            /* empty */
        }
        else {
            print(msg_cmd_nf);
        }
    }
}

/* Entry point */
void _start(void) {
    print(banner);
    print(msg_mount);

    /* Montar proc, sys, dev */
    sys3(SYS_mount, (long)"proc", (long)"/proc", (long)"proc");
    sys3(SYS_mount, (long)"sysfs", (long)"/sys", (long)"sysfs");
    sys3(SYS_mount, (long)"devtmpfs", (long)"/dev", (long)"devtmpfs");

    print(msg_dev);
    print(msg_arkhe);

    /* Criar device node /dev/arkhe_ctl */
    /* mknod /dev/arkhe_ctl c 250 0 */
    sys4(SYS_mknodat, -100, (long)"/dev/arkhe_ctl", 0666 | 0x2000, (250 << 8) | 0);

    print(msg_ready);

    /* Executar shell interativo */
    shell();

    /* Nunca deve chegar aqui */
    sys0(SYS_exit, 0, 0, 0);
}
