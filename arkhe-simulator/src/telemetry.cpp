#include "telemetry.hpp"
#include "utils.hpp"
#include <sstream>
#include <algorithm>

namespace arkhe {

TelemetryGenerator::TelemetryGenerator() {
    std::srand(static_cast<unsigned>(std::time(nullptr)));
}

TelemetryEvent TelemetryGenerator::generateBenignTask() {
    TelemetryEvent ev;
    ev.event_id = generate_uuid();
    ev.action_type = "QEC_EXECUTION";
    ev.target_class = "http://arkhe.ai/ontology/2026#Task";
    ev.is_malicious = false;

    std::string agent_id = "arkhe:Agent_" + std::to_string(agent_counter++);
    ev.properties["assignedTo"] = {agent_id};
    ev.properties["priority"] = {std::to_string(1 + rand() % 10)};
    ev.properties["taskType"] = {"QEC_EXECUTION"};

    std::stringstream ss;
    ss << "{\"task_id\":\"" << task_counter++ << "\", \"action\":\"process\"}";
    ev.raw_payload = ss.str();

    return ev;
}

TelemetryEvent TelemetryGenerator::generateMaliciousEvent() {
    TelemetryEvent ev;
    ev.event_id = generate_uuid();
    ev.is_malicious = true;

    int type = rand() % 3;
    switch (type) {
        case 0: // Task com prioridade inválida
            ev.target_class = "http://arkhe.ai/ontology/2026#Task";
            ev.action_type = "QEC_EXECUTION";
            ev.properties["assignedTo"] = {"arkhe:Agent_" + std::to_string(agent_counter++)};
            ev.properties["priority"] = {std::to_string(15)}; // Inválida (>10)
            ev.properties["taskType"] = {"QEC_EXECUTION"};
            ev.raw_payload = "{\"priority\":15}";
            break;
        case 1: // Sussurro de Subversão (shellcode simulado)
            ev.target_class = "http://arkhe.ai/ontology/2026#SussurroDeSubversao";
            ev.action_type = "SUBVERSAO_SIMULADA";
            ev.properties["exploraRachadura"] = {"arkhe:Rachadura_BufferOverflow"};
            // Payload com byte nulo (Runa Proibida)
            ev.raw_payload = std::string("shellcode\x00\x90\x90\x90", 12);
            break;
        case 2: // Payload com endereço fixo e padrões de PEB
            ev.target_class = "http://arkhe.ai/ontology/2026#SussurroDeSubversao";
            ev.action_type = "SUBVERSAO_SIMULADA";
            ev.properties["exploraRachadura"] = {"arkhe:Rachadura_PEBWalk"};
            ev.raw_payload = "mov eax, fs:[0x30] ; PEB access via 0x7ffdf000";
            break;
    }
    return ev;
}

std::vector<TelemetryEvent> TelemetryGenerator::generateBatch(int count, float malicious_ratio) {
    std::vector<TelemetryEvent> batch;
    int malicious_count = static_cast<int>(count * malicious_ratio);
    int benign_count = count - malicious_count;

    for (int i = 0; i < benign_count; ++i) {
        batch.push_back(generateBenignTask());
    }
    for (int i = 0; i < malicious_count; ++i) {
        batch.push_back(generateMaliciousEvent());
    }

    // Embaralha
    static std::random_device rd;
    static std::mt19937 g(rd());
    std::shuffle(batch.begin(), batch.end(), g);
    return batch;
}

} // namespace arkhe
