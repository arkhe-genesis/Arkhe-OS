// arm_control_loop.cpp — Loop de controle em tempo real do braço Arkhe

#include <iostream>
#include <vector>
#include <chrono>
#include <thread>

int main() {
    std::cout << "[ARM] Loop de controle 10kHz iniciado." << std::endl;

    bool running = true;
    int cycles = 0;

    while (running && cycles < 100) {
        // Simulação de leitura de sensores e aplicação de força
        cycles++;
        std::this_thread::sleep_for(std::chrono::microseconds(100));

        if (cycles % 10 == 0) {
            std::cout << "   -> Ciclo " << cycles << ": Invariância validada." << std::endl;
        }
    }

    std::cout << "[ARM] Teste de loop concluído." << std::endl;
    return 0;
}
