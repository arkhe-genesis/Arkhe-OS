/**
 * arkhe_edge_runtime.h — Substrato 9027: Arkhe Edge AI Runtime Header
 */
#ifndef ARKHE_EDGE_RUNTIME_H
#define ARKHE_EDGE_RUNTIME_H

#include <string>
#include <vector>
#include <optional>
#include <map>

// ============================================================================
// TIPOS E CONFIGURAÇÕES
// ============================================================================

/**
 * Backends de hardware suportados.
 */
enum class HwBackend {
    kAuto,              // Seleção automática baseada em disponibilidade
    kArmSME2,           // ARM SME2 via XNNPACK + KleidiAI
    kQualcommHexagon,   // Qualcomm Hexagon via QNN delegate
    kAppleANE,          // Apple Neural Engine via CoreML delegate
    kIntelNPU,          // Intel AI Boost via OpenVINO
    kAMDXDNA2,          // AMD Ryzen AI via Vitis AI
    kFallbackCPU,       // CPU puro (XNNPACK sem aceleração)
};

/**
 * Configuração para execução de inferência.
 */
struct InferenceConfig {
    std::string model_path;           // Caminho para o .tflite
    HwBackend preferred_backend = HwBackend::kAuto;      // Backend preferido
    int num_threads = 4;              // Número de threads
    bool enable_temporal_anchor = true;   // Ancorar cada inferência
    bool enable_phi_c_validation = true;  // Validar qualidade com Φ_C
    float phi_c_threshold = 0.95;     // Limiar mínimo de Φ_C
    std::string model_type = "audio"; // "audio", "image", "text", etc.
};

/**
 * Resultado de uma execução de inferência.
 */
struct InferenceResult {
    bool success;
    double latency_ms;
    double phi_c_before;
    double phi_c_after;
    std::string temporal_seal;
    std::string backend_used;
    std::vector<float> output_data;   // Dados de saída (áudio, imagem, etc.)
    std::string error_message;
};

// ============================================================================
// STUBS PARA ARKHE-SPECIFIC (simulados para demonstração)
// ============================================================================

struct ArkheTemporalChain {
    std::string AnchorEvent(const std::string& event_type,
                            const std::map<std::string, std::string>& payload);
};

struct ArkhePhiCMonitor {
    double ReadCurrentCoherence();
};

struct ArkheGuardian {
    bool ValidateOutput(const std::vector<float>& output, float threshold);
};

// Forward declaration of environment and compiled model to avoid litert dependency here
namespace litert {
    class Environment;
    class CompiledModel;
}

// ============================================================================
// CLASSE PRINCIPAL: ArkheEdgeRuntime
// ============================================================================

class ArkheEdgeRuntime {
public:
    explicit ArkheEdgeRuntime(const InferenceConfig& config);
    ~ArkheEdgeRuntime();

    InferenceResult Run(const std::vector<float>& input_data);

    static std::string BackendName(HwBackend backend);

private:
    InferenceConfig config_;
    void* env_ptr_; // Hide LiteRT specifics in header
    void* compiled_model_ptr_; // Hide LiteRT specifics in header
    HwBackend selected_backend_;

    std::optional<ArkheTemporalChain> temporal_chain_;
    std::optional<ArkhePhiCMonitor> phi_monitor_;
    std::optional<ArkheGuardian> guardian_;

    HwBackend SelectHardwareBackend(HwBackend preferred);
    void CompileModel(const std::string& model_path);

    bool IsArmSME2Available();
    bool IsQualcommHexagonAvailable();
    bool IsAppleANEAvailable();
    bool IsIntelNPUAvailable();
    bool IsAMDXDNA2Available();
};

#endif // ARKHE_EDGE_RUNTIME_H
