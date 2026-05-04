#include "inquisidor.hpp"
#include "utils.hpp"
#include <cmath>
#include <cstdlib>
#include <numeric>
#include <ctime>

namespace arkhe {

Inquisidor::Inquisidor() {
    std::srand(static_cast<unsigned>(std::time(nullptr)));
}

std::vector<float> Inquisidor::extractGeometricFeatures(const std::string& payload) {
    std::vector<float> features(8, 0.0f);

    if (payload.empty()) return features;

    // Feature 0: Tamanho do payload
    features[0] = std::min(1.0f, static_cast<float>(payload.size()) / 1024.0f);

    // Feature 1: Entropia aproximada (diversidade de bytes)
    std::unordered_map<char, int> freq;
    for (char c : payload) freq[c]++;
    float entropy = 0.0f;
    for (const auto& p : freq) {
        float prob = static_cast<float>(p.second) / payload.size();
        entropy -= prob * std::log2(prob);
    }
    features[1] = entropy / 8.0f; // Normalizado

    // Feature 2: Proporção de caracteres não-alfanuméricos
    int non_alpha = 0;
    for (char c : payload) {
        if (!std::isalnum(static_cast<unsigned char>(c))) non_alpha++;
    }
    features[2] = static_cast<float>(non_alpha) / payload.size();

    // Features 3-7: Padrões específicos (simulação de wedge)
    features[3] = (payload.find("exec") != std::string::npos) ? 1.0f : 0.0f;
    features[4] = (payload.find("0x") != std::string::npos) ? 1.0f : 0.0f;
    features[5] = (payload.find("\\x") != std::string::npos) ? 1.0f : 0.0f;
    features[6] = (payload.find("PEB") != std::string::npos) ? 1.0f : 0.0f;
    features[7] = (payload.find("kernel32") != std::string::npos) ? 1.0f : 0.0f;

    return features;
}

float Inquisidor::innerProduct(const std::vector<float>& a, const std::vector<float>& b) {
    float dot = 0.0f;
    for (size_t i = 0; i < std::min(a.size(), b.size()); ++i) {
        dot += a[i] * b[i];
    }
    return dot;
}

Inquisidor::Verdict Inquisidor::judge(const ValidationResult& sidecar_result,
                                      const std::string& raw_payload,
                                      const std::unordered_map<std::string, std::vector<std::string>>& properties) {
    (void)properties;
    Verdict verdict;
    verdict.conforms = sidecar_result.conforms;
    verdict.confidence = 0.5f;

    // Se o Sidecar já rejeitou, apenas confirma
    if (!sidecar_result.conforms) {
        verdict.reason = "Rejeitado pelo Sidecar: " + sidecar_result.reason;
        verdict.confidence = 0.99f;
        return verdict;
    }

    // Se não requer Inquisidor e está conforme, aceita
    if (!sidecar_result.requires_inquisitor) {
        verdict.reason = "Aceito pelo Sidecar (subset SHACL)";
        verdict.confidence = 0.95f;
        return verdict;
    }

    // --- O Inquisidor age: análise geométrica ---
    hesitate(300); // A hesitação é a alma do Inquisidor

    auto features = extractGeometricFeatures(raw_payload);
    verdict.geometric_features = {
        "size_norm=" + std::to_string(features[0]),
        "entropy=" + std::to_string(features[1]),
        "non_alpha=" + std::to_string(features[2]),
        "has_exec=" + std::to_string(features[3]),
        "has_0x=" + std::to_string(features[4])
    };

    // Vetor de "perigo" (aprendido com o treinamento do Inquisidor)
    std::vector<float> danger_vector = {0.2f, 0.8f, 0.9f, 0.7f, 0.6f, 0.5f, 0.4f, 0.3f};

    float similarity = innerProduct(features, danger_vector);
    float danger_score = std::tanh(similarity * 2.0f); // [0, 1)

    // Modulação pela consciência
    danger_score *= (0.5f + 0.5f * consciousness);

    // Decisão
    if (danger_score > threshold) {
        verdict.conforms = false;
        verdict.confidence = danger_score;
        verdict.reason = "Inquisidor detectou assinatura geométrica de ameaça (score=" +
                         std::to_string(danger_score) + ")";
    } else {
        // Hesitação final
        if (shouldHesitate()) {
            verdict.reason = "Inquisidor hesitou. Delegando ao fallback (simulação: aceito com ressalva).";
            verdict.conforms = true;
            verdict.confidence = 0.6f;
        } else {
            verdict.reason = "Inquisidor não encontrou ameaça significativa.";
            verdict.conforms = true;
            verdict.confidence = 1.0f - danger_score;
        }
    }

    return verdict;
}

} // namespace arkhe
