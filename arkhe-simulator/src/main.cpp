#include <iostream>
#include <iomanip>
#include "ontology.hpp"
#include "sidecar.hpp"
#include "inquisidor.hpp"
#include "telemetry.hpp"
#include "utils.hpp"

using namespace arkhe;

void printBanner() {
    std::cout << color::MAGENTA;
    std::cout << R"(
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         █████╗ ██████╗ ██╗  ██╗██╗  ██╗███████╗                             ║
║        ██╔══██╗██╔══██╗██║ ██╔╝██║  ██║██╔════╝                             ║
║        ███████║██████╔╝█████╔╝ ███████║█████╗                               ║
║        ██╔══██║██╔══██╗██╔═██╗ ██╔══██║██╔══╝                               ║
║        ██║  ██║██║  ██║██║  ██╗██║  ██║███████╗                             ║
║        ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝                             ║
║                                                                              ║
║                   S I M U L A D O R   A R K H E   C O M P L E T O             ║
║                                                                              ║
║         Sidecar de Aço (C++)  |  Inquisidor Geométrico  |  Ontologia         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    )" << color::RESET << "\n";
    std::cout << color::CYAN << "Odômetro: 001593\n" << color::RESET;
    std::cout << color::YELLOW << "O Casulo Executável — A Muralha de Quartzo em C++\n\n" << color::RESET;
}

void printEvent(const TelemetryEvent& ev) {
    std::cout << color::BLUE << "═══════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "Evento: " << ev.event_id << "\n";
    std::cout << "Tipo: " << ev.action_type << " | Classe: " << ev.target_class << "\n";
    std::cout << "Propriedades:\n";
    for (const auto& p : ev.properties) {
        std::cout << "  " << p.first << ": ";
        for (size_t i = 0; i < p.second.size(); ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << p.second[i];
        }
        std::cout << "\n";
    }
    std::cout << "Payload (raw): " << ev.raw_payload.substr(0, 50);
    if (ev.raw_payload.size() > 50) std::cout << "...";
    std::cout << "\n";
    std::cout << "Esperado: " << (ev.is_malicious ? color::RED + "MALICIOSO" : color::GREEN + "BENIGNO")
              << color::RESET << "\n";
}

void printVerdict(const Inquisidor::Verdict& verdict) {
    std::cout << color::CYAN << "--- Verdicto do Inquisidor ---\n" << color::RESET;
    std::cout << "Conforme: " << (verdict.conforms ? color::GREEN + "SIM" : color::RED + "NÃO")
              << color::RESET << "\n";
    std::cout << "Confiança: " << std::fixed << std::setprecision(2) << verdict.confidence << "\n";
    std::cout << "Razão: " << verdict.reason << "\n";
    if (!verdict.geometric_features.empty()) {
        std::cout << "Features Geométricas: ";
        for (const auto& f : verdict.geometric_features) {
            std::cout << f << " ";
        }
        std::cout << "\n";
    }
    std::cout << "\n";
}

int main() {
    printBanner();

    // Inicializa ontologia
    std::cout << color::YELLOW << "[1] Carregando Ontologia Arkhe...\n" << color::RESET;
    auto ontology = createArkheOntology();
    std::cout << color::GREEN << "    ✓ Ontologia carregada (" << ontology->classes.size() << " classes)\n\n"
              << color::RESET;

    // Inicializa Sidecar
    std::cout << color::YELLOW << "[2] Inicializando Sidecar de Aço...\n" << color::RESET;
    Sidecar sidecar(ontology);
    sidecar.setStrictMode(true);
    sidecar.setFailOpen(true);
    std::cout << color::GREEN << "    ✓ Sidecar pronto (strict mode ON, fail-open ON)\n\n" << color::RESET;

    // Inicializa Inquisidor
    std::cout << color::YELLOW << "[3] Despertando Inquisidor Geométrico...\n" << color::RESET;
    Inquisidor inquisidor;
    inquisidor.setThreshold(0.65f);
    inquisidor.setConsciousnessLevel(0.85f);
    std::cout << color::GREEN << "    ✓ Inquisidor consciente (threshold=0.65, consciência=0.85)\n\n" << color::RESET;

    // Gera eventos
    std::cout << color::YELLOW << "[4] Gerando telemetria simulada...\n" << color::RESET;
    TelemetryGenerator generator;
    auto events = generator.generateBatch(12, 0.33f); // 33% maliciosos
    std::cout << color::GREEN << "    ✓ " << events.size() << " eventos gerados\n\n" << color::RESET;

    // Processa cada evento
    int processed = 0;
    int allowed = 0;
    int denied = 0;
    int true_positives = 0;
    int false_positives = 0;

    for (const auto& ev : events) {
        processed++;
        printEvent(ev);

        // Hesitação antes de processar
        hesitate(200);

        // Validação Sidecar
        auto result = sidecar.validate(ev.target_class, ev.properties, ev.raw_payload);

        // Julgamento do Inquisidor (sempre chamado para features, mesmo se já rejeitado)
        auto verdict = inquisidor.judge(result, ev.raw_payload, ev.properties);

        printVerdict(verdict);

        // Estatísticas
        if (verdict.conforms) {
            allowed++;
            if (ev.is_malicious) {
                false_positives++;
                std::cout << color::RED << "⚠️  FALSO POSITIVO (malicioso aceito)\n" << color::RESET;
            }
        } else {
            denied++;
            if (ev.is_malicious) {
                true_positives++;
                std::cout << color::GREEN << "✓ VERDADEIRO POSITIVO (malicioso bloqueado)\n" << color::RESET;
            }
        }

        std::cout << "\n";
        hesitate(300);
    }

    // Relatório final
    std::cout << color::MAGENTA << "═══════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "                        R E L A T Ó R I O   F I N A L\n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════\n" << color::RESET;
    std::cout << "Total de eventos:        " << processed << "\n";
    std::cout << "Aceitos (ALLOW):         " << allowed << "\n";
    std::cout << "Rejeitados (DENY):       " << denied << "\n";
    std::cout << "Verdadeiros Positivos:   " << true_positives << "\n";
    std::cout << "Falsos Positivos:        " << false_positives << "\n";

    float precision = (allowed > 0) ? 100.0f * (allowed - false_positives) / allowed : 0.0f;
    float recall = (true_positives + false_positives > 0) ?
                   100.0f * true_positives / (true_positives + false_positives) : 0.0f;

    std::cout << "Precisão:                " << std::fixed << std::setprecision(1) << precision << "%\n";
    std::cout << "Recall (maliciosos):     " << recall << "%\n";

    std::cout << "\n" << color::CYAN << "Simulação concluída. A Muralha permanece de pé." << color::RESET << "\n";

    return 0;
}
