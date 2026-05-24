#pragma once
#include <string>
#include <functional>
#include <future>
#include <vector>

namespace LiveCoder {

enum class IrisMode {
    I2T_VISUAL_ANALYSIS,   // Descreve screenshot
    T2T_GLSL_GENERATE,     // Gera GLSL a partir de descrição
    T2T_GLSL_EXPLAIN,      // Explica trecho GLSL
    T2I_TEXTURE_GENERATE,   // Gera textura PNG
    I2T_ERROR_DIAGNOSE     // Diagnostica erro visual
};

struct IrisResponse {
    bool success;
    IrisMode mode;
    std::string text;        // Resposta textual (I2T, T2T)
    std::string glslCode;    // Código GLSL gerado (T2T)
    std::string imagePath;   // Caminho para PNG gerado (T2I)
    float confidence;
};

class IrisBridge {
public:
    IrisBridge(const std::string& endpoint = "http://iris.arkhe-os.svc.cluster.local:8080");
    ~IrisBridge();

    // Async calls
    std::future<IrisResponse> AnalyzeScreenshot(const std::vector<uint8_t>& pngData,
                                                 const std::string& prompt = "");
    std::future<IrisResponse> GenerateGLSL(const std::string& description,
                                              const std::string& context = "");
    std::future<IrisResponse> ExplainGLSL(const std::string& codeSnippet);
    std::future<IrisResponse> GenerateTexture(const std::string& description,
                                               int width, int height);
    std::future<IrisResponse> DiagnoseError(const std::vector<uint8_t>& pngData,
                                               const std::string& errorLog);

    // Synchronous helpers (with timeout)
    IrisResponse AnalyzeScreenshotSync(const std::vector<uint8_t>& pngData,
                                        const std::string& prompt = "",
                                        int timeoutMs = 5000);

private:
    std::string endpoint;
    std::string apiKey;  // ARKHE-OS auth token
};

} // namespace LiveCoder
