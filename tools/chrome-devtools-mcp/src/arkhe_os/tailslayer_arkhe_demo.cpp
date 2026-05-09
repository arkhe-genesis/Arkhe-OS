#include "arkhe_tailslayer.hpp"
#include <iostream>

int main() {
    // Pin to main core
    tailslayer::pin_to_core(tailslayer::CORE_MAIN);

    std::cout << "[🜏 ARKHE_TAILSLAYER] INITIALIZING COHERENT_PHASE_BUFFER...\n";

    try {
        arkhe::CoherentPhaseBuffer reader;

        std::cout << "[🜏 ARKHE_TAILSLAYER] INSERTING PHASE_REPLICAS...\n";

        // Sample phase 1: Optimal coherence
        arkhe_phase_t p1 = { 0.866, 0.5 }; // ~30 degrees, mag 1.0
        reader.insert(p1);

        // Sample phase 2: Low coherence
        arkhe_phase_t p2 = { 0.1, 0.1 };
        reader.insert(p2);

        std::cout << "[🜏 ARKHE_TAILSLAYER] STARTING HEDGED_READ_WORKERS...\n";
        reader.start_workers();

        // Wait for workers to finish (in this demo, they read once and exit)
        // Note: tailslayer workers in the provided header run wait_work once and then final_work once.
        // Actually, looking at worker_func in hedged_reader.hpp:
        /*
        void worker_func(std::size_t worker_idx) {
            pin_to_core(cores_[worker_idx]);
            std::size_t read_index = wait_work(WaitArgs...);
            T* target_addr = get_next_logical_index_address(worker_idx, read_index);
            final_work(*target_addr, WorkArgs...);
        }
        */
        // It's a single read.

        std::cout << "[🜏 ARKHE_TAILSLAYER] WAITING FOR ASYNC_PHASE_RESOLUTION...\n";
        sleep(1);

        std::cout << "[🜏 ARKHE_TAILSLAYER] DEMO_COMPLETE\n";
    } catch (const std::exception& e) {
        std::cerr << "[!] ERROR: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
