#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/capsicum.h>
#include <err.h>
#include <errno.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <command> [args...]\n", argv[0]);
        return 1;
    }

    if (cap_enter() < 0 && errno != ENOSYS) {
        err(1, "cap_enter failed");
    }

    execvp(argv[1], &argv[1]);
    err(1, "execvp failed");
    return 1;
}
