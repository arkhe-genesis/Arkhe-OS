#pragma once
#include <cstdint>
#include <atomic>
#include <pthread.h>
#include <functional>
#include <vector>

namespace arkhe::core {

typedef struct {
    pthread_t thread;
    int priority;                    // 1-99 (RT priority)
    uint64_t deadline_ns;            // Prazo absoluto para execução
    std::function<void(void*)> handler; // Callback de intervenção
    void* handler_arg;
    std::atomic<bool> armed;         // Se o gatilho está ativo
} safety_trigger_t;

class SafetyGuardian {
public:
    SafetyGuardian();
    ~SafetyGuardian();

    int arm_trigger(safety_trigger_t* trigger, uint64_t deadline_from_now_ns);
    int disarm_trigger(safety_trigger_t* trigger);

    // Teste de garantia de deadline
    bool run_deadline_test(int iterations);

private:
    static void* scheduler_main(void* arg);

    bool running_;
    pthread_t scheduler_thread_;
    std::vector<safety_trigger_t*> triggers_;
    pthread_mutex_t lock_;
};

} // namespace arkhe::core
