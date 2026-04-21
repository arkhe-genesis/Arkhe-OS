#ifndef ARKHE_TELEMETRY_HPP
#define ARKHE_TELEMETRY_HPP

#include <string>
#include <vector>
#include <unordered_map>

namespace arkhe {

// ═══════════════════════════════════════════════════════════════════════════════
// Evento de Telemetria (Simula entrada do AIDK)
// ═══════════════════════════════════════════════════════════════════════════════
struct TelemetryEvent {
    std::string event_id;
    std::string action_type;
    std::string target_class; // URI da classe ontológica
    std::unordered_map<std::string, std::vector<std::string>> properties;
    std::string raw_payload;
    bool is_malicious; // Para simulação
};

// ═══════════════════════════════════════════════════════════════════════════════
// Gerador de Eventos de Telemetria (Simulador de Jogo/Traffic)
// ═══════════════════════════════════════════════════════════════════════════════
class TelemetryGenerator {
public:
    TelemetryGenerator();

    // Gera um lote de eventos (mistura de benignos e maliciosos)
    std::vector<TelemetryEvent> generateBatch(int count, float malicious_ratio = 0.2f);

    // Gera um evento benigno (Task normal)
    TelemetryEvent generateBenignTask();

    // Gera um evento malicioso (Sussurro ou Task violada)
    TelemetryEvent generateMaliciousEvent();

private:
    int task_counter = 1;
    int agent_counter = 1;
};

} // namespace arkhe

#endif // ARKHE_TELEMETRY_HPP
