#include "ontology.hpp"
#include "utils.hpp"
#include <stdexcept>
#include <sstream>

namespace arkhe {

// ═══════════════════════════════════════════════════════════════════════════════
// PropertyConstraint
// ═══════════════════════════════════════════════════════════════════════════════
PropertyConstraint::PropertyConstraint(Type t, const std::string& val)
    : type(t), value(val), int_value(0) {
    if (t == MIN_COUNT || t == MAX_COUNT || t == MIN_INCLUSIVE || t == MAX_INCLUSIVE) {
        try {
            int_value = std::stoi(val);
        } catch (...) {
            int_value = 0;
        }
    }
}

bool PropertyConstraint::validate(const std::vector<std::string>& values) const {
    switch (type) {
        case MIN_COUNT:
            return static_cast<int>(values.size()) >= int_value;
        case MAX_COUNT:
            return static_cast<int>(values.size()) <= int_value;
        case DATATYPE_INTEGER:
            for (const auto& v : values) {
                try {
                    std::stoi(v);
                } catch (...) {
                    return false;
                }
            }
            return true;
        case DATATYPE_STRING:
            return true; // tudo é string
        case MIN_INCLUSIVE:
            for (const auto& v : values) {
                try {
                    if (std::stoi(v) < int_value) return false;
                } catch (...) {
                    return false;
                }
            }
            return true;
        case MAX_INCLUSIVE:
            for (const auto& v : values) {
                try {
                    if (std::stoi(v) > int_value) return false;
                } catch (...) {
                    return false;
                }
            }
            return true;
        case PATTERN:
            {
                std::regex re(value);
                for (const auto& v : values) {
                    if (!std::regex_match(v, re)) return false;
                }
                return true;
            }
        case ENUM:
            {
                auto allowed = split(value, ',');
                for (const auto& v : values) {
                    bool found = false;
                    for (const auto& a : allowed) {
                        if (trim(a) == trim(v)) { found = true; break; }
                    }
                    if (!found) return false;
                }
                return true;
            }
    }
    return true;
}

std::string PropertyConstraint::description() const {
    switch (type) {
        case MIN_COUNT: return "minCount = " + std::to_string(int_value);
        case MAX_COUNT: return "maxCount = " + std::to_string(int_value);
        case DATATYPE_INTEGER: return "datatype = xsd:integer";
        case DATATYPE_STRING: return "datatype = xsd:string";
        case MIN_INCLUSIVE: return "minInclusive = " + std::to_string(int_value);
        case MAX_INCLUSIVE: return "maxInclusive = " + std::to_string(int_value);
        case PATTERN: return "pattern = /" + value + "/";
        case ENUM: return "in [" + value + "]";
    }
    return "";
}

// ═══════════════════════════════════════════════════════════════════════════════
// Property
// ═══════════════════════════════════════════════════════════════════════════════
Property::Property(const std::string& n, const std::string& u) : name(n), uri(u) {}

void Property::addConstraint(PropertyConstraint::Type type, const std::string& value) {
    constraints.emplace_back(type, value);
}

bool Property::validate(const std::vector<std::string>& values, std::string& error) const {
    for (const auto& c : constraints) {
        if (!c.validate(values)) {
            error = "Propriedade '" + name + "' violou " + c.description();
            return false;
        }
    }
    return true;
}

// ═══════════════════════════════════════════════════════════════════════════════
// OntologyClass
// ═══════════════════════════════════════════════════════════════════════════════
OntologyClass::OntologyClass(const std::string& n, const std::string& u) : name(n), uri(u) {}

void OntologyClass::addProperty(std::shared_ptr<Property> prop) {
    properties.push_back(prop);
}

std::shared_ptr<Property> OntologyClass::getProperty(const std::string& name) const {
    for (const auto& p : properties) {
        if (p->name == name) return p;
    }
    return nullptr;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Ontology
// ═══════════════════════════════════════════════════════════════════════════════
Ontology::Ontology() = default;

void Ontology::addClass(std::shared_ptr<OntologyClass> cls) {
    classes[cls->uri] = cls;
}

std::shared_ptr<OntologyClass> Ontology::getClass(const std::string& uri) const {
    auto it = classes.find(uri);
    if (it != classes.end()) return it->second;
    return nullptr;
}

bool Ontology::validateInstance(const std::string& classUri,
                                const std::unordered_map<std::string, std::vector<std::string>>& properties,
                                std::vector<std::string>& violations) const {
    auto cls = getClass(classUri);
    if (!cls) {
        violations.push_back("Classe '" + classUri + "' nao encontrada na ontologia");
        return false;
    }

    bool valid = true;
    for (const auto& prop : cls->properties) {
        auto it = properties.find(prop->name);
        std::vector<std::string> values;
        if (it != properties.end()) {
            values = it->second;
        }

        std::string error;
        if (!prop->validate(values, error)) {
            violations.push_back(error);
            valid = false;
        }
    }
    return valid;
}

// ═══════════════════════════════════════════════════════════════════════════════
// Criação da Ontologia Arkhe Padrão
// ═══════════════════════════════════════════════════════════════════════════════
std::shared_ptr<Ontology> createArkheOntology() {
    auto ont = std::make_shared<Ontology>();

    // ═══════════════════════════════════════════════════════════════════════════
    // Classe: Task (A tarefa primordial do Casulo)
    // ═══════════════════════════════════════════════════════════════════════════
    auto taskClass = std::make_shared<OntologyClass>("Task", "http://arkhe.ai/ontology/2026#Task");

    // Propriedade: assignedTo (deve existir, tipo IRI)
    auto assignedTo = std::make_shared<Property>("assignedTo", "http://arkhe.ai/ontology/2026#assignedTo");
    assignedTo->addConstraint(PropertyConstraint::MIN_COUNT, "1");
    assignedTo->addConstraint(PropertyConstraint::PATTERN, "^arkhe:Agent_[0-9]+$");
    taskClass->addProperty(assignedTo);

    // Propriedade: priority (inteiro, 1-10)
    auto priority = std::make_shared<Property>("priority", "http://arkhe.ai/ontology/2026#priority");
    priority->addConstraint(PropertyConstraint::DATATYPE_INTEGER, "");
    priority->addConstraint(PropertyConstraint::MIN_INCLUSIVE, "1");
    priority->addConstraint(PropertyConstraint::MAX_INCLUSIVE, "10");
    taskClass->addProperty(priority);

    // Propriedade: taskType (enumeração)
    auto taskType = std::make_shared<Property>("taskType", "http://arkhe.ai/ontology/2026#taskType");
    taskType->addConstraint(PropertyConstraint::ENUM, "QEC_EXECUTION,INFERENCE,ORCHESTRATION,SUBVERSAO_SIMULADA");
    taskType->addConstraint(PropertyConstraint::MIN_COUNT, "1");
    taskClass->addProperty(taskType);

    // Propriedade: payload (opcional, mas se presente não pode ter bytes nulos - Runa Proibida)
    // A validação de bytes nulos é feita no Sidecar, não via SHACL (limitação da simulação)

    ont->addClass(taskClass);

    // ═══════════════════════════════════════════════════════════════════════════
    // Classe: SussurroDeSubversao (Ameaça)
    // ═══════════════════════════════════════════════════════════════════════════
    auto sussurroClass = std::make_shared<OntologyClass>("SussurroDeSubversao",
                                                         "http://arkhe.ai/ontology/2026#SussurroDeSubversao");
    auto explora = std::make_shared<Property>("exploraRachadura", "http://arkhe.ai/ontology/2026#exploraRachadura");
    explora->addConstraint(PropertyConstraint::MIN_COUNT, "1");
    sussurroClass->addProperty(explora);

    ont->addClass(sussurroClass);

    return ont;
}

} // namespace arkhe
