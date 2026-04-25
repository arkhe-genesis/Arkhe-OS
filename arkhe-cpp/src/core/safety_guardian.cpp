#include "arkhe/core/safety_guardian.hpp"
#include <ctime>
#include <iostream>
#include <algorithm>
#include <chrono>
#include <thread>

namespace arkhe::core {

static uint64_t get_time_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

SafetyGuardian::SafetyGuardian() : running_(true) {
    pthread_mutex_init(&lock_, nullptr);
    pthread_create(&scheduler_thread_, nullptr, scheduler_main, this);
}

SafetyGuardian::~SafetyGuardian() {
    running_ = false;
    pthread_join(scheduler_thread_, nullptr);
    pthread_mutex_destroy(&lock_);
}

int SafetyGuardian::arm_trigger(safety_trigger_t* trigger, uint64_t deadline_from_now_ns) {
    pthread_mutex_lock(&lock_);
    trigger->deadline_ns = get_time_ns() + deadline_from_now_ns;
    trigger->armed = true;
    triggers_.push_back(trigger);
    pthread_mutex_unlock(&lock_);
    return 0;
}

int SafetyGuardian::disarm_trigger(safety_trigger_t* trigger) {
    pthread_mutex_lock(&lock_);
    trigger->armed = false;
    triggers_.erase(std::remove(triggers_.begin(), triggers_.end(), trigger), triggers_.end());
    pthread_mutex_unlock(&lock_);
    return 0;
}

void* SafetyGuardian::scheduler_main(void* arg) {
    SafetyGuardian* self = static_cast<SafetyGuardian*>(arg);

    // Configurar prioridade RT
    struct sched_param param = {.sched_priority = 90};
    pthread_setschedparam(pthread_self(), SCHED_FIFO, &param);

    while (self->running_) {
        uint64_t now = get_time_ns();

        pthread_mutex_lock(&self->lock_);
        for (auto it = self->triggers_.begin(); it != self->triggers_.end(); ) {
            safety_trigger_t* t = *it;
            if (t->armed && now >= t->deadline_ns) {
                if (t->handler) {
                    t->handler(t->handler_arg);
                }
                t->armed = false;
                it = self->triggers_.erase(it);
            } else {
                ++it;
            }
        }
        pthread_mutex_unlock(&self->lock_);

        std::this_thread::sleep_for(std::chrono::microseconds(100));
    }
    return nullptr;
}

bool SafetyGuardian::run_deadline_test(int iterations) {
    int misses = 0;
    for (int i = 0; i < iterations; ++i) {
        std::atomic<bool> executed(false);
        uint64_t start = get_time_ns();
        uint64_t deadline_ns = 5000000; // 5ms

        safety_trigger_t trigger;
        trigger.handler = [&](void*) { executed = true; };
        trigger.handler_arg = nullptr;

        arm_trigger(&trigger, deadline_ns);

        // Espera um pouco mais que o deadline
        std::this_thread::sleep_for(std::chrono::milliseconds(10));

        uint64_t end = get_time_ns();
        if (!executed) {
            std::cerr << "[SafetyGuardian] Test iteration " << i << " FAILED: Trigger not executed\n";
            misses++;
        } else {
             // Verificação opcional de precisão aqui
        }
    }
    return misses == 0;
}

} // namespace arkhe::core
