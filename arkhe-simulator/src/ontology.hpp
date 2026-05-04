#ifndef ARKHE_ONTOLOGY_HPP
#define ARKHE_ONTOLOGY_HPP

#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <functional>
#include <regex>

namespace arkhe {

// ═══════════════════════════════════════════════════════════════════════════════
// CLASSE: Restrição de Propriedade
// ═══════════════════════════════════════════════════════════════════════════════
class PropertyConstraint {
public:
    enum Type {
        MIN_COUNT,
        MAX_COUNT,
        DATATYPE_INTEGER,
        DATATYPE_STRING,
        MIN_INCLUSIVE,
        MAX_INCLUSIVE,
        PATTERN,
        ENUM
    };

    PropertyConstraint(Type type, const std::string& value);

    bool validate(const std::vector<std::string>& values) const;
    std::string description() const;

    Type type;
    std::string value;
    int int_value;
};

// ═══════════════════════════════════════════════════════════════════════════════
// CLASSE: Propriedade Ontológica
// ═══════════════════════════════════════════════════════════════════════════════
class Property {
public:
    Property(const std::string& name, const std::string& uri);

    void addConstraint(PropertyConstraint::Type type, const std::string& value);
    bool validate(const std::vector<std::string>& values, std::string& error) const;

    std::string name;
    std::string uri;
    std::vector<PropertyConstraint> constraints;
};

// ═══════════════════════════════════════════════════════════════════════════════
// CLASSE: Classe Ontológica
// ═══════════════════════════════════════════════════════════════════════════════
class OntologyClass {
public:
    OntologyClass(const std::string& name, const std::string& uri);

    void addProperty(std::shared_ptr<Property> prop);
    std::shared_ptr<Property> getProperty(const std::string& name) const;

    std::string name;
    std::string uri;
    std::vector<std::shared_ptr<Property>> properties;
};

// ═══════════════════════════════════════════════════════════════════════════════
// CLASSE: Ontologia
// ═══════════════════════════════════════════════════════════════════════════════
class Ontology {
public:
    Ontology();

    void addClass(std::shared_ptr<OntologyClass> cls);
    std::shared_ptr<OntologyClass> getClass(const std::string& uri) const;

    // Valida uma instância contra a ontologia
    bool validateInstance(const std::string& classUri,
                          const std::unordered_map<std::string, std::vector<std::string>>& properties,
                          std::vector<std::string>& violations) const;

    std::unordered_map<std::string, std::shared_ptr<OntologyClass>> classes;
};

// ═══════════════════════════════════════════════════════════════════════════════
// CONSTRUÇÃO DA ONTOLOGIA ARKHE (Padrão)
// ═══════════════════════════════════════════════════════════════════════════════
std::shared_ptr<Ontology> createArkheOntology();

} // namespace arkhe

#endif // ARKHE_ONTOLOGY_HPP
