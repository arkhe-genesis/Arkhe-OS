#include "sidecar.hpp"
#include "utils.hpp"
#include <regex>
#include <iostream>

namespace arkhe {

Sidecar::Sidecar(std::shared_ptr<Ontology> ont) : ontology(ont) {}

bool Sidecar::checkForbiddenBytes(const std::string& payload, std::vector<Violation>& violations) {
    if (contains_null_byte(payload)) {
        violations.push_back({
            "payload",
            "Runa Proibida detectada: byte nulo (0x00) encontrado. A Muralha de Quartzo rejeita o sussurro.",
            "ERROR"
        });
        return false;
    }
    return true;
}

bool Sidecar::checkFixedAddresses(const std::string& payload, std::vector<Violation>& violations) {
    // Procura por padrões de endereço fixo (0x seguido de 4+ hex)
    std::regex addr_regex("0x[0-9a-fA-F]{4,}");
    if (std::regex_search(payload, addr_regex)) {
        violations.push_back({
            "payload",
            "Violação da Lei da Posição Independente: payload contém endereço de memória fixo (0x...).",
            "WARNING"
        });
        if (strict_mode) {
            return false;
        }
    }
    return true;
}

ValidationResult Sidecar::validate(const std::string& classUri,
                                   const std::unordered_map<std::string, std::vector<std::string>>& properties,
                                   const std::string& raw_payload) {
    ValidationResult result;
    result.conforms = true;
    result.requires_inquisitor = false;

    // 1. Verificações de segurança de baixo nível (Runas Proibidas)
    if (!checkForbiddenBytes(raw_payload, result.violations)) {
        result.conforms = false;
        result.reason = "Runa Proibida detectada";
        return result;
    }

    // 2. Verificação de endereços fixos (pode delegar ao Inquisidor se complexo)
    if (!checkFixedAddresses(raw_payload, result.violations)) {
        result.conforms = false;
        result.reason = "Endereço fixo detectado";
        return result;
    }

    // 3. Validação ontológica (SHACL subset)
    std::vector<std::string> ont_violations;
    bool ont_valid = ontology->validateInstance(classUri, properties, ont_violations);

    if (!ont_valid) {
        for (const auto& v : ont_violations) {
            result.violations.push_back({classUri, v, "ERROR"});
        }
        result.conforms = false;
        result.reason = "Violação de constraints SHACL";
    }

    // 4. Se é um Sussurro de Subversão, exige escrutínio adicional (delega ao Inquisidor)
    if (classUri.find("SussurroDeSubversao") != std::string::npos) {
        result.requires_inquisitor = true;
    }

    // 5. Se contém SPARQL-like patterns, delega
    if (raw_payload.find("SPARQL") != std::string::npos ||
        raw_payload.find("sh:sparql") != std::string::npos) {
        result.requires_inquisitor = true;
    }

    return result;
}

} // namespace arkhe
