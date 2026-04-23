#include <stdio.h>
#include <sys/resource.h>
#include "quantum_scheduler.h"

void adjust_priority_by_coherence(pid_t pid, double coherence) {
    int nice = (int)((1.0 - coherence) * 39.0 - 20.0);
    if (nice < -20) nice = -20;
    if (nice > 19) nice = 19;

    // setpriority(PRIO_PROCESS, pid, nice);
    printf("[SCHEDULER] Coerência %.4f -> Nice: %d\n", coherence, nice);
}
