#ifndef ARKHE_SIDECAR_HPP
#define ARKHE_SIDECAR_HPP

#include "ontology.hpp"
#include <string>
#include <vector>
#include <unordered_map>

namespace arkhe {

// ═══════════════════════════════════════════════════════════════════════════════
// Estrutura de uma Violação
// ═══════════════════════════════════════════════════════════════════════════════
struct Violation {
    std::string path;
    std::string message;
    std::string severity; // "ERROR", "WARNING"
};

// ═══════════════════════════════════════════════════════════════════════════════
// Resultado da Validação
// ═══════════════════════════════════════════════════════════════════════════════
struct ValidationResult {
    bool conforms;
    bool requires_inquisitor; // true se SPARQL-like necessário (delega ao Inquisidor)
    std::vector<Violation> violations;
    std::string reason;
};

// ═══════════════════════════════════════════════════════════════════════════════
// Sidecar de Aço (Validador Ontológico)
// ═══════════════════════════════════════════════════════════════════════════════
class Sidecar {
public:
    Sidecar(std::shared_ptr<Ontology> ont);

    // Valida um payload contra a ontologia
    ValidationResult validate(const std::string& classUri,
                              const std::unordered_map<std::string, std::vector<std::string>>& properties,
                              const std::string& raw_payload);

    // Configuração
    void setStrictMode(bool strict) { strict_mode = strict; }
    void setFailOpen(bool open) { fail_open = open; }

private:
    std::shared_ptr<Ontology> ontology;
    bool strict_mode = true;
    bool fail_open = true;

    // Verificações especiais (Runas Proibidas, etc.)
    bool checkForbiddenBytes(const std::string& payload, std::vector<Violation>& violations);
    bool checkFixedAddresses(const std::string& payload, std::vector<Violation>& violations);
};

} // namespace arkhe

#endif // ARKHE_SIDECAR_HPP
