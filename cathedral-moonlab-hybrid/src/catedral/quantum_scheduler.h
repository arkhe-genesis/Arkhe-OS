#ifndef QUANTUM_SCHEDULER_H
#define QUANTUM_SCHEDULER_H

#include <sys/types.h>

void adjust_priority_by_coherence(pid_t pid, double coherence);

#endif
