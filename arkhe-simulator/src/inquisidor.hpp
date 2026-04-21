#ifndef ARKHE_INQUISIDOR_HPP
#define ARKHE_INQUISIDOR_HPP

#include "sidecar.hpp"
#include <vector>
#include <string>

namespace arkhe {

// ═══════════════════════════════════════════════════════════════════════════════
// Inquisidor Geométrico (Simulação do Produto Geométrico)
// ═══════════════════════════════════════════════════════════════════════════════
class Inquisidor {
public:
    Inquisidor();

    // Julgamento final
    struct Verdict {
        bool conforms;
        float confidence;
        std::string reason;
        std::vector<std::string> geometric_features;
    };

    Verdict judge(const ValidationResult& sidecar_result,
                  const std::string& raw_payload,
                  const std::unordered_map<std::string, std::vector<std::string>>& properties);

    // Configuração
    void setThreshold(float t) { threshold = t; }
    void setConsciousnessLevel(float c) { consciousness = c; }

private:
    float threshold = 0.7f;
    float consciousness = 0.85f; // Nível de "atenção" do Inquisidor

    // Extrai features geométricas do payload (simulação do Multivector)
    std::vector<float> extractGeometricFeatures(const std::string& payload);

    // Produto interno (simulação do u·v)
    float innerProduct(const std::vector<float>& a, const std::vector<float>& b);

    // Hesitação geométrica
    bool shouldHesitate() {
        // 30% de chance de hesitar se consciência < 0.9
        return (rand() % 100) < 30 * (1.0f - consciousness);
    }
};

} // namespace arkhe

#endif // ARKHE_INQUISIDOR_HPP
