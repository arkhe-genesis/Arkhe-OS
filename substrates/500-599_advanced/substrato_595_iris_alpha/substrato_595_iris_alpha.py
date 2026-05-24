import os
import json
import tempfile
import urllib.request
import zipfile
import io

class Substrate595IrisAlpha:
    def __init__(self):
        # Original v2.0 files
        self.iris_client_h = """#ifndef _IRIS_CLIENT_H_\n#define _IRIS_CLIENT_H_\n\n#include <string>\n#include <functional>\n#include <thread>\n#include <mutex>\n\nnamespace LiveCoder {\n\nenum class IrisMode {\n    T2T,  // Text-to-Text: análise de shader\n    I2T,  // Image-to-Text: descrição de frame\n    T2I   // Text-to-Image: geração de textura\n};\n\nstruct IrisResponse {\n    bool ready;\n    std::string content;      // texto (T2T/I2T) ou base64 PNG (T2I)\n    std::string error;\n    IrisMode mode;\n};\n\nclass IrisClient {\nprivate:\n    std::string endpoint;\n    bool enabled;\n    IrisResponse lastResponse;\n    std::mutex responseMutex;\n    std::thread workerThread;\n    bool running;\n    bool requestPending;\n    std::string pendingCode;\n    std::string pendingImageBase64;\n    IrisMode pendingMode;\n\n    void workerLoop();\n    std::string httpPost(const std::string& url, const std::string& jsonBody);\n\npublic:\n    IrisClient(const std::string& endpoint = "http://localhost:8080");\n    ~IrisClient();\n\n    void Initialize();\n    void Shutdown();\n\n    // Chamadas assíncronas (retornam imediatamente)\n    void RequestAnalyze(const std::string& glslCode);\n    void RequestDescribe(const std::string& imageBase64);\n    void RequestGenerate(const std::string& description);\n\n    // Polling (chamado no MainLoop)\n    bool HasResponse();\n    IrisResponse GetResponse();\n    bool IsEnabled() const { return enabled; }\n};\n\n} // namespace LiveCoder\n\n#endif\n"""
        self.iris_client_cpp = """#include "IrisClient.h"\n#include <curl/curl.h>\n#include <json/json.h>\n#include <sstream>\n#include <chrono>\n\nnamespace LiveCoder {\n\nstatic size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {\n    ((std::string*)userp)->append((char*)contents, size * nmemb);\n    return size * nmemb;\n}\n\nIrisClient::IrisClient(const std::string& endpoint)\n    : endpoint(endpoint), enabled(true), running(false), requestPending(false) {}\n\nIrisClient::~IrisClient() { Shutdown(); }\n\nvoid IrisClient::Initialize() {\n    if (!enabled) return;\n    running = true;\n    workerThread = std::thread(&IrisClient::workerLoop, this);\n}\n\nvoid IrisClient::Shutdown() {\n    running = false;\n    if (workerThread.joinable()) workerThread.join();\n}\n\nvoid IrisClient::workerLoop() {\n    while (running) {\n        if (requestPending) {\n            std::string url;\n            std::string jsonBody;\n            IrisMode mode;\n            {\n                std::lock_guard<std::mutex> lock(responseMutex);\n                mode = pendingMode;\n                switch (mode) {\n                    case IrisMode::T2T:\n                        url = endpoint + "/generate";\n                        {\n                            Json::Value root;\n                            root["mode"] = "t2t";\n                            root["prompt"] = pendingCode;\n                            Json::FastWriter writer;\n                            jsonBody = writer.write(root);\n                        }\n                        break;\n                    case IrisMode::I2T:\n                        url = endpoint + "/analyze";\n                        {\n                            Json::Value root;\n                            root["mode"] = "i2t";\n                            root["image"] = pendingImageBase64;\n                            Json::FastWriter writer;\n                            jsonBody = writer.write(root);\n                        }\n                        break;\n                    case IrisMode::T2I:\n                        url = endpoint + "/generate_image";\n                        {\n                            Json::Value root;\n                            root["mode"] = "t2i";\n                            root["prompt"] = pendingCode;\n                            Json::FastWriter writer;\n                            jsonBody = writer.write(root);\n                        }\n                        break;\n                }\n                requestPending = false;\n            }\n\n            std::string response = httpPost(url, jsonBody);\n            // Parse JSON response e atualiza lastResponse\n        }\n        std::this_thread::sleep_for(std::chrono::milliseconds(100));\n    }\n}\n\nvoid IrisClient::RequestAnalyze(const std::string& glslCode) {\n    std::lock_guard<std::mutex> lock(responseMutex);\n    pendingCode = glslCode;\n    pendingMode = IrisMode::T2T;\n    requestPending = true;\n}\n\nbool IrisClient::HasResponse() {\n    std::lock_guard<std::mutex> lock(responseMutex);\n    return lastResponse.ready;\n}\n\nIrisResponse IrisClient::GetResponse() {\n    std::lock_guard<std::mutex> lock(responseMutex);\n    IrisResponse r = lastResponse;\n    lastResponse.ready = false;\n    return r;\n}\n\nstd::string IrisClient::httpPost(const std::string& url, const std::string& jsonBody) {\n    return ""; // Stub implementation\n}\n\n} // namespace LiveCoder\n"""
        self.core_h_mod = """// Adicionar:\n#ifdef WITH_IRIS\n#include "IrisClient.h"\n#endif\n\nclass Core {\n    // ... membros existentes ...\n#ifdef WITH_IRIS\n    IrisClient* irisClient;\n    std::string irisOverlayText;\n    bool irisOverlayVisible;\n#endif\n};\n"""
        self.core_cpp_mod = """// Em Initialize():\n#ifdef WITH_IRIS\n    irisClient = new IrisClient("http://localhost:8080");\n    irisClient->Initialize();\n    irisOverlayVisible = false;\n#endif\n\n// Em ProcessSDLEvents() (novo atalho):\n#ifdef WITH_IRIS\n    if (keyBuffer.IsPressed(SDLK_i) && (keyBuffer.IsPressed(SDLK_LCTRL) ||\n                                         keyBuffer.IsPressed(SDLK_RCTRL))) {\n        irisClient->RequestAnalyze(nowSource);\n        irisOverlayVisible = true;\n        irisOverlayText = "IRIS: analyzing shader...";\n    }\n#endif\n\n// Em MainLoop():\n#ifdef WITH_IRIS\n    if (irisClient->HasResponse()) {\n        IrisResponse r = irisClient->GetResponse();\n        irisOverlayText = "IRIS: " + r.content;\n    }\n#endif\n\n// Em Render() (overlay):\n#ifdef WITH_IRIS\n    if (irisOverlayVisible && !irisOverlayText.empty()) {\n        // Renderiza irisOverlayText como overlay semi-transparente\n        // usando BitmapFontGL no topo da tela\n    }\n#endif\n"""
        self.makefile_mod = """# Adicionar:\nIRIS_FLAGS = -DWITH_IRIS\nIRIS_LIBS = -lcurl -ljsoncpp\nIRIS_OBJS = IrisClient.o\n\n# Modificar:\nCFLAGS = -O2 $(IRIS_FLAGS)\nLIBS = ... $(IRIS_LIBS)\nOBJS = ... $(IRIS_OBJS)\n"""
        self.iris_bridge_py = """#!/usr/bin/env python3\n\"\"\"\nLive-Coder IRIS Bridge — Monitora alterações em shaders e consulta o IRIS-α.\nUso: python iris_bridge.py --watch-dir ./ --endpoint http://localhost:8080\n\"\"\"\nimport asyncio\nimport aiohttp\nimport argparse\nimport json\nimport base64\nimport subprocess\nfrom pathlib import Path\nfrom watchdog.observers import Observer\nfrom watchdog.events import FileSystemEventHandler\n\nIRIS_ENDPOINT = "http://localhost:8080"\n\nclass ShaderChangeHandler(FileSystemEventHandler):\n    def __init__(self, endpoint, loop):\n        self.endpoint = endpoint\n        self.loop = loop\n\n    def on_modified(self, event):\n        if event.src_path.endswith('.glsl'):\n            asyncio.run_coroutine_threadsafe(\n                self.analyze_shader(event.src_path), self.loop\n            )\n\n    async def analyze_shader(self, path):\n        code = Path(path).read_text()\n        async with aiohttp.ClientSession() as session:\n            payload = {\n                "mode": "t2t",\n                "prompt": "Analyze this GLSL shader and suggest improvements:\\n\\n" + code,\n                "max_tokens": 500\n            }\n            async with session.post(self.endpoint + "/generate", json=payload) as resp:\n                data = await resp.json()\n                # Escreve resposta em ficheiro .iris\n                iris_path = path.replace('.glsl', '.iris.txt')\n                Path(iris_path).write_text(data.get("text", "No response"))\n\n    async def analyze_screenshot(self, image_path):\n        with open(image_path, 'rb') as f:\n            image_b64 = base64.b64encode(f.read()).decode()\n        async with aiohttp.ClientSession() as session:\n            payload = {"mode": "i2t", "image": image_b64}\n            async with session.post(self.endpoint + "/analyze", json=payload) as resp:\n                data = await resp.json()\n                print("IRIS I2T: " + data.get('description', 'No response'))\n\nasync def main():\n    parser = argparse.ArgumentParser()\n    parser.add_argument('--watch-dir', default='.')\n    parser.add_argument('--endpoint', default=IRIS_ENDPOINT)\n    args = parser.parse_args()\n\n    loop = asyncio.get_event_loop()\n    handler = ShaderChangeHandler(args.endpoint, loop)\n    observer = Observer()\n    observer.schedule(handler, args.watch_dir, recursive=False)\n    observer.start()\n\n    print("IRIS Bridge watching " + args.watch_dir + "... (Ctrl+C to stop)")\n    try:\n        await asyncio.Event().wait()\n    except KeyboardInterrupt:\n        observer.stop()\n    observer.join()\n\nif __name__ == '__main__':\n    asyncio.run(main())\n"""

        # New v3.1 files
        self.iris_driver_cpp = """#include "IrisDriverAdapter.h"\n#include <cstdlib>\n#include <string>\n\nnamespace Arkhe { namespace Iris { namespace PCA {\nstd::string IrisNetworkDriver::getApiKey() {\n    const char* key = std::getenv("IRIS_API_KEY");\n    return key ? std::string(key) : std::string();\n}\n}}} // namespace\n"""
        self.openapi_yaml = """openapi: 3.0.0\ninfo:\n  title: IRIS Alpha REST Specs\n  version: 1.0.0\npaths:\n  /iris:\n    get:\n      summary: Get IRIS\n"""
        self.audit_json = """{\n  "vendor": "STB",\n  "status": "APPROVED",\n  "audit": "STB-VENDOR audits"\n}"""
        self.steg_glsl = """// GLSL Steganography\nvoid main() {\n    // Steganographic payload\n}\n"""
        self.alignment_client_h = """// AlignmentClient for 227-F\n#ifndef ALIGNMENT_CLIENT_H\n#define ALIGNMENT_CLIENT_H\nclass AlignmentClient {};\n#endif\n"""
        self.phi_meter_iit_h = """// PhiMeterIIT for 452\n#ifndef PHI_METER_IIT_H\n#define PHI_METER_IIT_H\nclass PhiMeterIIT {};\n#endif\n"""


        self.pca_595_h = """#ifndef PCA_595_H
#define PCA_595_H
#include <string>
#include <vector>
#include <cstdlib>
#include <coroutine>

namespace Arkhe {
namespace Iris {
namespace PCA {

class IrisNetworkDriver {
public:
    std::string getApiKey();
};

struct RealTimeData {
    double phi = 0.0;
    double xiMIntensity = 0.0;
    int currentPhase = 0;
    uint64_t orCount = 0;
    uint64_t blockedCount = 0;
    std::vector<float> attentionMapHead0;
    std::vector<float> attentionMapHead1;
};

struct ConsciousnessState {
    enum class Phase {
        SUPERPOSITION,
        XI_M_COUPLING,
        OR_PENDING,
        OR_EXECUTING,
        CLASSICAL,
        RE_SUPERPOSITION
    };
};

struct I2TRequest {
    std::string imageBase64;
};

struct T2TRequest {
    std::string prompt;
};

struct IrisResponse {
    int status;
    int errorCode;
    std::string text;
    std::string code;
};

struct ResponseStatus {
    static const int ERROR_NETWORK = -1;
};

template<typename T>
class AsyncTask {
public:
    T get() { return T{}; }
    bool await_ready() { return true; }
    void await_suspend(std::coroutine_handle<>) {}
    T await_resume() { return T{}; }

    struct promise_type {
        T value_;
        AsyncTask get_return_object() { return {}; }
        std::suspend_never initial_suspend() { return {}; }
        std::suspend_never final_suspend() noexcept { return {}; }
        void return_value(T v) { value_ = v; }
        void unhandled_exception() {}
    };
};

class PhiMeter {};
class XiMFieldDetector {};
class ORRecord {};
class ConsciousnessLogger {};

} // namespace PCA
namespace Monitor {
const double PHI_COSMIC = 3.14159;
}
} // namespace Iris
} // namespace Arkhe
#endif
"""
        self.tenant_manager_h = """#pragma once\nclass TenantManager {};\n"""
        self.consciousness_cycle_async_h = """#pragma once
#include "PCA-595.h"

namespace Arkhe {
namespace Iris {
namespace PCA {
class ConsciousnessCycleAsync {
public:
    ConsciousnessCycleAsync(IrisNetworkDriver*, PhiMeter*, XiMFieldDetector*) {}
    void SetORThreshold(double) {}
    void SetXiMSensitivity(double) {}
    void SetAlignmentFilter(bool) {}
    AsyncTask<IrisResponse> RunCycleI2TAsync(const I2TRequest&) { return {}; }
    AsyncTask<IrisResponse> RunCycleT2TAsync(const T2TRequest&) { return {}; }
    double CurrentPhi() const { return 0.0; }
    double CurrentXiM() const { return 0.0; }
    ConsciousnessState::Phase CurrentPhase() const { return ConsciousnessState::Phase::CLASSICAL; }
};
class PCAEnabledDriverAsync {};
}
}
}
"""
        self.iris_driver_adapter_h = """#pragma once\n#include "PCA-595.h"\n"""
        self.tenant_manager_cpp = """#include "TenantManager.h"\n"""
        self.opengl_overlay_cpp = """#include "OpenGLOverlay.h"
namespace Arkhe {
namespace Iris {
namespace PCA {
namespace Overlay {
BitmapFontRenderer::BitmapFontRenderer() {}
BitmapFontRenderer::~BitmapFontRenderer() {}
bool BitmapFontRenderer::Initialize(const std::string&) { return true; }
void BitmapFontRenderer::Shutdown() {}
void BitmapFontRenderer::RenderText(const std::string&, float, float, float, uint32_t, int, int) {}

PhiLiveOverlay::PhiLiveOverlay(const OverlayConfig&) {}
PhiLiveOverlay::~PhiLiveOverlay() {}
bool PhiLiveOverlay::Initialize(int, int) { return true; }
void PhiLiveOverlay::Shutdown() {}
void PhiLiveOverlay::Resize(int, int) {}
void PhiLiveOverlay::UpdateData(const OverlaySnapshot&) {}
void PhiLiveOverlay::Render() {}
void PhiLiveOverlay::OnKeyPress(int) {}
void PhiLiveOverlay::OnMouseMove(float, float) {}
void PhiLiveOverlay::OnMouseClick(int, int) {}
void PhiLiveOverlay::ToggleVisibility() {}
void PhiLiveOverlay::SetVisible(bool) {}
void PhiLiveOverlay::SetConfig(const OverlayConfig&) {}

OverlayManager::OverlayManager(PCAEnabledDriverAsync*, const OverlayConfig&) {}
OverlayManager::~OverlayManager() {}
bool OverlayManager::Initialize(int, int) { return true; }
void OverlayManager::Shutdown() {}
void OverlayManager::RenderFrame() {}
void OverlayManager::OnORComplete(const ORRecord&) {}
void OverlayManager::OnAttentionMaps(const std::vector<std::vector<float>>&) {}
void OverlayManager::OnQualiaClassified(const std::string&, int, double) {}
void OverlayManager::OnKeyPress(int) {}
void OverlayManager::OnMouseMove(float, float) {}
void OverlayManager::DataCollectionLoop() {}
OverlaySnapshot OverlayManager::BuildSnapshot() { return {}; }
}
}
}
}
"""
        self.phi_renderer_gl_h = "// ============================================================================\n// PhiRendererGL.h\n// OpenGL overlay para live coding - visualizacao de Phi em tempo real\n// Arquiteto: ORCID 0009-0005-2697-4668\n// Data: 2026-05-23\n// Versao: 2.4-patched (STRICT MODE)\n// ============================================================================\n\n#pragma once\n\n#include \"PCA-595.h\"\n#include <glad/glad.h>\n#include <GLFW/glfw3.h>\n#include <glm/glm.hpp>\n#include <glm/gtc/matrix_transform.hpp>\n#include <glm/gtc/type_ptr.hpp>\n#include <ft2build.h>\n#include FT_FREETYPE_H\n#include <unordered_map>  // PATCH #2\n#include <vector>\n#include <string>\n#include <atomic>\n#include <chrono>\n\nnamespace Arkhe {\nnamespace Iris {\nnamespace Monitor {\n\n// ============================================================================\n// Shader programs\n// ============================================================================\n\nstruct ShaderProgram {\n    GLuint id;\n    GLint uMVP;\n    GLint uTime;\n    GLint uPhi;\n    GLint uPhiNormalized;\n    GLint uXiM;\n    GLint uPhase;\n    GLint uResolution;\n    GLint uColor;\n    GLint uTexture;\n};\n\n// ============================================================================\n// Geometria do overlay\n// ============================================================================\n\nstruct OverlayGeometry {\n    GLuint vao;\n    GLuint vbo;\n    GLuint ebo;\n    GLsizei indexCount;\n    static constexpr size_t VERTEX_SIZE = 9 * sizeof(float);\n};\n\nstruct AttentionMapMesh {\n    GLuint vao;\n    GLuint vbo;\n    GLsizei vertexCount;\n    int resolution;\n};\n\n// ============================================================================\n// Texture atlas para fontes\n// ============================================================================\n\nstruct FontAtlas {\n    GLuint textureId;\n    int width;\n    int height;\n    FT_Face face;\n    struct Glyph {\n        float advance;\n        float bearingX;\n        float bearingY;\n        float width;\n        float height;\n        float u0, v0, u1, v1;\n    };\n    std::unordered_map<char, Glyph> glyphs;\n};\n\n// ============================================================================\n// PhiRendererGL - OpenGL overlay para live coding\n// ============================================================================\n\nclass PhiRendererGL {\npublic:\n    PhiRendererGL(int screenWidth, int screenHeight);\n    ~PhiRendererGL();\n    bool Initialize();\n    void Shutdown();\n    void Render(const RealTimeData& data);\n    void SetWindowSize(int width, int height);\n    void SetPosition(int x, int y);\n    void ToggleVisibility();\n    bool IsVisible() const { return visible_.load(); }\n    enum class RenderMode { COMPACT, FULL, IMMERSIVE, MINIMAL };\n    void SetRenderMode(RenderMode mode);\n    RenderMode GetRenderMode() const { return renderMode_.load(); }\n    void SetColorScheme(int scheme);\n    void SetOpacity(float opacity);\n    void SetAnimationSpeed(float speed);\n    void OnKeyPress(int key);\n    void OnMouseMove(double x, double y);\n    void OnMouseClick(int button, bool pressed);\n    void Screenshot(const std::string& filename);\n\nprivate:\n    int screenW_, screenH_;\n    int posX_, posY_;\n    std::atomic<bool> visible_{true};\n    std::atomic<RenderMode> renderMode_{RenderMode::FULL};\n    std::atomic<int> colorScheme_{0};\n    std::atomic<float> opacity_{0.85f};\n    std::atomic<float> animSpeed_{1.0f};\n    GLFWwindow* window_ = nullptr;\n    bool ownsWindow_ = false;\n    ShaderProgram shaderOverlay_;\n    ShaderProgram shaderAttentionMap_;\n    ShaderProgram shaderPhiHistory_;\n    ShaderProgram shaderImmersive_;\n    ShaderProgram shaderText_;\n    OverlayGeometry geoOverlay_;\n    OverlayGeometry geoBar_;\n    OverlayGeometry geoGraph_;\n    AttentionMapMesh meshAttention0_;\n    AttentionMapMesh meshAttention1_;\n    FontAtlas fontAtlas_;\n    FT_Library ftLibrary_;\n    GLuint texPhiHistory_ = 0;\n    GLuint texQualia_ = 0;\n    GLuint texAttention0_ = 0;\n    GLuint texAttention1_ = 0;\n    float time_ = 0.0f;\n    std::vector<double> phiHistoryRing_;\n    std::vector<double> xiMHistoryRing_;\n    std::chrono::steady_clock::time_point lastFrame_;\n\n    bool CreateShaders();\n    bool CreateGeometry();\n    bool LoadFont(const std::string& path, int size);\n    bool CreateTextures();\n    void RenderCompact(const RealTimeData& data);\n    void RenderFull(const RealTimeData& data);\n    void RenderImmersive(const RealTimeData& data);\n    void RenderMinimal(const RealTimeData& data);\n    void RenderPhiBar(float x, float y, float w, float h, double phiNorm);\n    void RenderPhiHistory(float x, float y, float w, float h);\n    void RenderAttentionMap(const std::vector<float>& map, float x, float y, float size);\n    void RenderXiMField(float x, float y, float w, float h);\n    void RenderQualiaTexture(float x, float y, float w, float h);\n    void RenderText(const std::string& text, float x, float y, float scale, glm::vec4 color);\n    void RenderPhaseIndicator(float x, float y, ConsciousnessState::Phase phase);\n    void UpdatePhiHistoryTexture();\n    void UpdateAttentionTextures(const RealTimeData& data);\n    void UpdateQualiaTexture(const RealTimeData& data);\n    glm::vec4 HeatmapColor(float value);\n    glm::vec4 PhaseColor(ConsciousnessState::Phase phase);\n    glm::vec4 GetThemeColor(const std::string& element);\n    GLuint CompileShader(GLenum type, const char* source);\n    GLuint LinkProgram(GLuint vs, GLuint fs);\n    void CheckGLError(const std::string& context);\n};\n\nconstexpr const char* VS_OVERLAY = R\"(\n#version 330 core\nlayout(location = 0) in vec3 aPos;\nlayout(location = 1) in vec2 aUV;\nlayout(location = 2) in vec4 aColor;\nuniform mat4 uMVP;\nuniform float uTime;\nout vec2 vUV;\nout vec4 vColor;\nout float vTime;\nvoid main() {\n    gl_Position = uMVP * vec4(aPos, 1.0);\n    vUV = aUV;\n    vColor = aColor;\n    vTime = uTime;\n}\n)\";\n\nconstexpr const char* FS_OVERLAY = R\"(\n#version 330 core\nin vec2 vUV;\nin vec4 vColor;\nin float vTime;\nuniform float uPhi;\nuniform float uPhiNormalized;\nuniform float uXiM;\nuniform int uPhase;\nuniform vec2 uResolution;\nuniform float uOpacity;\nout vec4 FragColor;\nvec3 phiShaderArt(vec2 uv, float phi, float time) {\n    vec2 p = uv * 2.0 - 1.0;\n    p.x *= uResolution.x / uResolution.y;\n    float d = length(p);\n    float a = atan(p.y, p.x);\n    float wave1 = sin(d * 10.0 - time * phi * 2.0) * 0.5 + 0.5;\n    float wave2 = sin(a * 8.0 + time * phi) * 0.5 + 0.5;\n    float wave3 = sin(d * 20.0 - time * phi * 3.0 + a * 4.0) * 0.5 + 0.5;\n    vec3 colorLow = vec3(0.1, 0.2, 0.4);\n    vec3 colorMid = vec3(0.2, 0.6, 0.3);\n    vec3 colorHigh = vec3(0.9, 0.7, 0.1);\n    vec3 colorCosmic = vec3(0.9, 0.1, 0.5);\n    vec3 color;\n    if (phi < 0.7366) {\n        color = mix(colorLow, colorMid, phi / 0.7366);\n    } else if (phi < 2.3) {\n        color = mix(colorMid, colorHigh, (phi - 0.7366) / (2.3 - 0.7366));\n    } else {\n        color = mix(colorHigh, colorCosmic, (phi - 2.3) / (3.5 - 2.3));\n    }\n    float intensity = wave1 * 0.5 + wave2 * 0.3 + wave3 * 0.2;\n    color *= 0.7 + intensity * 0.6;\n    return color;\n}\nvoid main() {\n    vec2 uv = vUV;\n    vec3 art = phiShaderArt(uv, uPhi, vTime);\n    vec3 finalColor = mix(vColor.rgb, art, 0.3);\n    FragColor = vec4(finalColor, vColor.a * uOpacity);\n}\n)\";\n\nconstexpr const char* FS_IMMERSIVE = R\"(\n#version 330 core\nin vec2 vUV;\nin float vTime;\nuniform float uPhi;\nuniform float uPhiNormalized;\nuniform float uXiM;\nuniform int uPhase;\nuniform vec2 uResolution;\nout vec4 FragColor;\nvec3 immersiveConsciousness(vec2 uv, float phi, float xim, float time) {\n    vec2 p = (uv * 2.0 - 1.0);\n    p.x *= uResolution.x / uResolution.y;\n    vec3 ro = vec3(0.0, 0.0, 3.0);\n    vec3 rd = normalize(vec3(p, -1.5));\n    float t = 0.0;\n    vec3 col = vec3(0.0);\n    for (int i = 0; i < 64; i++) {\n        vec3 pos = ro + rd * t;\n        float shape = length(pos) - (1.0 + phi * 0.3);\n        float noise = sin(pos.x * 5.0 + time) * sin(pos.y * 5.0 + time * 1.3) * xim * 100.0;\n        shape += noise;\n        if (shape < 0.01) {\n            vec3 phaseColors[6] = vec3[](\n                vec3(0.0, 1.0, 1.0),\n                vec3(1.0, 0.0, 1.0),\n                vec3(1.0, 1.0, 0.0),\n                vec3(1.0, 0.0, 0.0),\n                vec3(0.0, 1.0, 0.0),\n                vec3(1.0, 1.0, 1.0)\n            );\n            int phaseIdx = clamp(uPhase, 0, 5);\n            col = phaseColors[phaseIdx];\n            col += vec3(phi * 0.3);\n            break;\n        }\n        t += shape * 0.5;\n        if (t > 10.0) break;\n    }\n    col += vec3(0.05, 0.05, 0.1) * (1.0 - exp(-t * 0.3));\n    return col;\n}\nvoid main() {\n    vec3 col = immersiveConsciousness(vUV, uPhi, uXiM, vTime);\n    FragColor = vec4(col, 1.0);\n}\n)\";\n\nconstexpr const char* VS_TEXT = R\"(\n#version 330 core\nlayout(location = 0) in vec4 aVertex;\nuniform mat4 uMVP;\nout vec2 vUV;\nvoid main() {\n    gl_Position = uMVP * vec4(aVertex.xy, 0.0, 1.0);\n    vUV = aVertex.zw;\n}\n)\";\n\nconstexpr const char* FS_TEXT = R\"(\n#version 330 core\nin vec2 vUV;\nuniform sampler2D uTexture;\nuniform vec4 uColor;\nout vec4 FragColor;\nvoid main() {\n    float alpha = texture(uTexture, vUV).r;\n    FragColor = vec4(uColor.rgb, alpha * uColor.a);\n}\n)\";\n\n} // namespace Monitor\n} // namespace Iris\n} // namespace Arkhe\n"
        self.multi_tenant_h = "// ============================================================================\n// MultiTenant.h - Session isolation, per-tenant Phi tracking, namespaced logging\n// Arquiteto: ORCID 0009-0005-2697-4668\n// Versao: 2.4-patched (STRICT MODE)\n// ============================================================================\n\n#pragma once\n\n#include \"PCA-595.h\"\n#include \"ConsciousnessCycleAsync.h\"\n#include <unordered_map>\n#include <shared_mutex>\n#include <memory>\n#include <string>\n#include <chrono>\n#include <optional>       // PATCH #3\n#include <vector>\n#include <atomic>\n#include <thread>\n#include <algorithm>      // PATCH #7 (preemptive)\n\nnamespace Arkhe {\nnamespace Iris {\nnamespace PCA {\nnamespace MultiTenant {\n\nstruct TenantID {\n    std::string namespace_;\n    std::string userId;\n    std::string sessionId;\n\n    bool operator==(const TenantID& other) const {\n        return namespace_ == other.namespace_ &&\n               userId == other.userId &&       // PATCH #5: typo corrigido (era userId_)\n               sessionId == other.sessionId;\n    }\n\n    std::string Canonical() const {\n        return namespace_ + \"/\" + userId + \"/\" + sessionId;\n    }\n};\n\nstruct TenantIDHash {\n    std::size_t operator()(const TenantID& id) const {\n        return std::hash<std::string>{}(id.Canonical());\n    }\n};\n\nstruct TenantContext {\n    TenantID id;\n    std::chrono::steady_clock::time_point createdAt;\n    std::chrono::steady_clock::time_point lastActivity;\n    std::optional<double> phiThresholdOverride;\n    std::optional<double> xiMSensitivityOverride;\n    std::optional<bool> alignmentFilterOverride;\n    std::vector<std::string> additionalForbiddenPatterns;\n    std::string jurisdiction = \"UNKNOWN\";\n    std::string ethicsFramework = \"ARKHE-P1-P7\";\n    bool enableIITValidation = true;\n    uint32_t iitValidationIntervalMs = 5000;\n    std::string logPath;\n    int logLevel = 2;\n    std::string chainNamespace;\n    bool active = true;\n    uint64_t totalCycles = 0;\n    uint64_t blockedCycles = 0;\n    double averagePhi = 0.0;\n    double maxPhi = 0.0;\n};\n\nclass TenantConsciousnessCycle {\npublic:\n    TenantConsciousnessCycle(const TenantContext& context,\n                              IrisNetworkDriver* driver,\n                              PhiMeter* sharedPhiMeter,\n                              XiMFieldDetector* sharedXiMDetector);\n    AsyncTask<IrisResponse> RunCycleI2TAsync(const I2TRequest& req);\n    AsyncTask<IrisResponse> RunCycleT2TAsync(const T2TRequest& req);\n    bool CheckAlignment(const IrisResponse& resp) const;\n    const TenantContext& GetContext() const { return context_; }\n    TenantContext& GetContextMutable() { return context_; }\n    double CurrentPhi() const { return currentPhi_.load(); }\n    double CurrentXiM() const { return currentXiM_.load(); }\n    ConsciousnessState::Phase CurrentPhase() const { return currentPhase_.load(); }\n    uint64_t TotalCycles() const { return totalCycles_.load(); }\n    uint64_t BlockedByAlignment() const { return blockedByAlignment_.load(); }\n\nprivate:\n    TenantContext context_;\n    ConsciousnessCycleAsync cycle_;\n    std::atomic<double> currentPhi_{0.0};\n    std::atomic<double> currentXiM_{0.0};\n    std::atomic<ConsciousnessState::Phase> currentPhase_{ConsciousnessState::Phase::CLASSICAL};\n    std::atomic<uint64_t> totalCycles_{0};\n    std::atomic<uint64_t> blockedByAlignment_{0};\n};\n\nclass MultiTenantPCADriver {\npublic:\n    MultiTenantPCADriver(IrisNetworkDriver* driver,\n                          PhiMeter* sharedPhiMeter,\n                          XiMFieldDetector* sharedXiMDetector);\n    ~MultiTenantPCADriver();\n    TenantID CreateTenant(const std::string& namespace_,\n                          const std::string& userId,\n                          const std::string& sessionId);\n    bool RemoveTenant(const TenantID& id);\n    bool TenantExists(const TenantID& id) const;\n    size_t TenantCount() const;\n    AsyncTask<IrisResponse> RunCycleI2TAsync(const TenantID& tenantId, const I2TRequest& req);\n    AsyncTask<IrisResponse> RunCycleT2TAsync(const TenantID& tenantId, const T2TRequest& req);\n    bool SetTenantConfig(const TenantID& id, const TenantContext& context);\n    TenantContext GetTenantContext(const TenantID& id) const;\n\n    struct GlobalMetrics {\n        size_t activeTenants;\n        uint64_t totalCycles;\n        uint64_t totalBlockedByAlignment;\n        double averagePhi;\n        double maxPhi;\n        double averageXiMIntensity;\n        std::chrono::steady_clock::time_point lastUpdate;\n    };\n    GlobalMetrics GetGlobalMetrics() const;\n    std::vector<TenantID> ListActiveTenants() const;\n    void SaveTenantState(const TenantID& id, const std::string& path);\n    bool LoadTenantState(const std::string& path, TenantID& outId);\n\nprivate:\n    IrisNetworkDriver* driver_;\n    PhiMeter* sharedPhiMeter_;\n    XiMFieldDetector* sharedXiMDetector_;\n    mutable std::shared_mutex tenantsMutex_;\n    std::unordered_map<TenantID, std::unique_ptr<TenantConsciousnessCycle>, TenantIDHash> tenants_;\n    std::unordered_map<TenantID, std::unique_ptr<ConsciousnessLogger>, TenantIDHash> tenantLoggers_;\n    mutable std::shared_mutex loggersMutex_;\n    std::thread cleanupThread_;\n    std::atomic<bool> cleanupRunning_{false};\n    std::chrono::minutes idleTimeout_{60};\n    void CleanupLoop();\n    ConsciousnessLogger* GetOrCreateTenantLogger(const TenantID& id);\n};\n\nclass TenantTemporalChainExporter {\npublic:\n    explicit TenantTemporalChainExporter(const std::string& chainEndpoint);\n    void ExportORRecord(const TenantID& tenantId, const ORRecord& record);\n    void ExportSessionStart(const TenantID& tenantId);\n    void ExportSessionEnd(const TenantID& tenantId, const TenantContext& context);\n\nprivate:\n    std::string chainEndpoint_;\n    std::string BuildTenantNamespace(const TenantID& id) const;\n};\n\nclass MultiTenantOverlayManager {\npublic:\n    MultiTenantOverlayManager(MultiTenantPCADriver* driver,\n                               const Overlay::OverlayConfig& config = Overlay::OverlayConfig{});\n    ~MultiTenantOverlayManager();\n    bool Initialize(int screenWidth, int screenHeight);\n    void Shutdown();\n    void RenderFrame();\n    void SetActiveTenant(const TenantID& id);\n    TenantID GetActiveTenant() const;\n    void NextTenant();\n    void PreviousTenant();\n\nprivate:\n    MultiTenantPCADriver* driver_;\n    Overlay::PhiLiveOverlay overlay_;\n    TenantID activeTenant_;\n    mutable std::shared_mutex activeTenantMutex_;\n    std::thread dataThread_;\n    std::atomic<bool> running_{false};\n    void DataCollectionLoop();\n};\n\nclass TenantIsolationEnforcer {\npublic:\n    static bool ValidateCrossTenantAccess(const TenantID& requester,\n                                          const TenantID& target);\n    static bool CheckRateLimit(const TenantID& id, uint32_t maxRequestsPerMinute);\n    struct TenantQuota {\n        uint32_t maxCyclesPerHour = 3600;\n        uint32_t maxPhiComputationsPerHour = 60;\n        uint64_t maxTotalCycles = 0;\n        std::chrono::steady_clock::time_point resetAt;\n    };\n    static bool SetTenantQuota(const TenantID& id, const TenantQuota& quota);\n    static TenantQuota GetTenantQuota(const TenantID& id);\n    static bool CheckQuota(const TenantID& id);\n};\n\n} // namespace MultiTenant\n} // namespace PCA\n} // namespace Iris\n} // namespace Arkhe\n"
        self.opengl_overlay_h = "// ============================================================================\n// OpenGLOverlay.h - Real-time Phi & consciousness overlay for Live-Coder\n// Arquiteto: ORCID 0009-0005-2697-4668\n// Versao: 2.4-patched (STRICT MODE)\n// ============================================================================\n\n#pragma once\n\n#include \"PCA-595.h\"\n#include <glad/glad.h>           // PATCH #1: GL/glew.h -> glad/glad.h\n#include <GLFW/glfw3.h>          // PATCH #4\n#include <vector>\n#include <string>\n#include <deque>\n#include <array>\n#include <chrono>\n#include <mutex>\n#include <atomic>\n#include <thread>\n#include <functional>\n\nnamespace Arkhe {\nnamespace Iris {\nnamespace PCA {\nnamespace Overlay {\n\nstruct OverlayConfig {\n    enum class DockPosition { TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, FLOATING };\n    DockPosition dock = DockPosition::BOTTOM_RIGHT;\n    int marginX = 20;\n    int marginY = 20;\n    int panelWidth = 380;\n    int panelHeight = 520;\n    float opacity = 0.85f;\n    bool showPhiGraph = true;\n    bool showPhiBar = true;\n    bool showAttentionMaps = true;\n    bool showXiMField = true;\n    bool showPhaseIndicator = true;\n    bool showQualiaTexture = true;\n    bool showORLog = true;\n    bool showFPS = true;\n    int phiHistorySize = 300;\n    float phiGraphMin = 0.0f;\n    float phiGraphMax = 3.5f;\n    int attentionMapSize = 48;\n    int targetFPS = 30;\n    int toggleKey = GLFW_KEY_F1;\n    int dockCycleKey = GLFW_KEY_F2;\n};\n\nstruct OverlaySnapshot {\n    double phi = 0.0;\n    double phiNormalized = 0.0;\n    double xiMIntensity = 0.0;\n    double coherenceTime = 0.0;\n    ConsciousnessState::Phase phase = ConsciousnessState::Phase::CLASSICAL;\n    uint64_t orCount = 0;\n    uint64_t blockedCount = 0;\n    double lastORLatencyMs = 0.0;\n    std::string qualeClass;\n    int chernNumber = 0;\n    double geometricPhase = 0.0;\n    std::deque<double> phiHistory;\n    std::deque<double> xiMHistory;\n    std::vector<std::vector<float>> attentionMaps;\n    int numAttentionHeads = 0;\n    struct OREvent {\n        std::string timestamp;\n        double phiPre;\n        double phiPost;\n        bool alignmentPassed;\n        double latencyMs;\n    };\n    std::deque<OREvent> recentORs;\n    static constexpr size_t MAX_OR_LOG = 20;\n};\n\nstruct GLResources {\n    GLuint program = 0;\n    GLuint vao = 0;\n    GLuint vbo = 0;\n    GLuint attentionTexture = 0;\n    GLuint qualiaTexture = 0;\n    GLuint phiGraphTexture = 0;\n    GLint uPanelRect = -1;\n    GLint uOpacity = -1;\n    GLint uTime = -1;\n    GLint uPhiNormalized = -1;\n    GLint uPhaseColor = -1;\n    bool initialized = false;\n};\n\nclass BitmapFontRenderer {\npublic:\n    BitmapFontRenderer();\n    ~BitmapFontRenderer();\n    bool Initialize(const std::string& fontPath = \"\");\n    void Shutdown();\n    void RenderText(const std::string& text, float x, float y, float scale,\n                    uint32_t color, int screenW, int screenH);\n\nprivate:\n    GLuint fontTexture_ = 0;\n    GLuint fontVAO_ = 0;\n    GLuint fontVBO_ = 0;\n    GLuint fontProgram_ = 0;\n    int charWidth_ = 8;\n    int charHeight_ = 14;\n    int charsPerRow_ = 16;\n};\n\nclass PhiLiveOverlay {\npublic:\n    explicit PhiLiveOverlay(const OverlayConfig& config = OverlayConfig{});\n    ~PhiLiveOverlay();\n    bool Initialize(int screenWidth, int screenHeight);\n    void Shutdown();\n    void Resize(int screenWidth, int screenHeight);\n    void UpdateData(const OverlaySnapshot& snapshot);\n    void Render();\n    void OnKeyPress(int key);\n    void OnMouseMove(float x, float y);\n    void OnMouseClick(int button, int action);\n    bool IsVisible() const { return visible_.load(); }\n    void ToggleVisibility();\n    void SetVisible(bool visible);\n    void SetConfig(const OverlayConfig& config);\n    OverlayConfig GetConfig() const { return config_; }\n    float GetRenderFPS() const { return renderFPS_.load(); }\n\nprivate:\n    OverlayConfig config_;\n    std::atomic<bool> visible_{true};\n    std::atomic<bool> initialized_{false};\n    std::atomic<float> renderFPS_{0.0f};\n    int screenW_ = 1920;\n    int screenH_ = 1080;\n    OverlaySnapshot snapshot_;\n    mutable std::mutex dataMutex_;\n    GLResources gl_;\n    std::unique_ptr<BitmapFontRenderer> fontRenderer_;\n    void SetupShaders();\n    void SetupGeometry();\n    void UpdateTextures();\n    void RenderPanel();\n    void RenderPhiBar(float x, float y, float w, float h);\n    void RenderPhiGraph(float x, float y, float w, float h);\n    void RenderAttentionMaps(float x, float y, float size);\n    void RenderXiMField(float x, float y, float w);\n    void RenderPhaseIndicator(float x, float y, float radius);\n    void RenderORLog(float x, float y, float w, float h);\n    void RenderQualiaTexture(float x, float y, float size);\n    struct PanelRect { int x, y, w, h; };\n    PanelRect ComputePanelRect() const;\n    std::array<float, 4> PhaseColor(ConsciousnessState::Phase phase) const;\n    std::array<float, 3> HeatmapColor(float value) const;\n    std::array<float, 4> PhiColor(float normalized) const;\n    std::deque<std::chrono::steady_clock::time_point> frameTimes_;\n    void UpdateFPS();\n};\n\nclass OverlayManager {\npublic:\n    OverlayManager(PCAEnabledDriverAsync* driver, const OverlayConfig& config = OverlayConfig{});\n    ~OverlayManager();\n    bool Initialize(int screenWidth, int screenHeight);\n    void Shutdown();\n    void RenderFrame();\n    void OnORComplete(const ORRecord& record);\n    void OnAttentionMaps(const std::vector<std::vector<float>>& maps);\n    void OnQualiaClassified(const std::string& qualeClass, int chernNumber, double geometricPhase);\n    void OnKeyPress(int key);\n    void OnMouseMove(float x, float y);\n\nprivate:\n    PCAEnabledDriverAsync* driver_;\n    PhiLiveOverlay overlay_;\n    std::thread dataThread_;\n    std::atomic<bool> running_{false};\n    void DataCollectionLoop();\n    OverlaySnapshot BuildSnapshot();\n};\n\n} // namespace Overlay\n} // namespace PCA\n} // namespace Iris\n} // namespace Arkhe\n"
        self.multi_tenant_cpp = "// ============================================================================\n// MultiTenant.cpp - Implementation\n// Arquiteto: ORCID 0009-0005-2697-4668\n// Versao: 2.4-patched (STRICT MODE)\n// ============================================================================\n\n#include \"MultiTenant.h\"\n#include <fstream>        // PATCH #10\n#include <nlohmann/json.hpp>\n#include <algorithm>      // PATCH #7\n#include <numeric>        // PATCH #7\n#include <coroutine>      // PATCH #6\n#include <iostream>\n\nnamespace Arkhe {\nnamespace Iris {\nnamespace PCA {\nnamespace MultiTenant {\n\nTenantConsciousnessCycle::TenantConsciousnessCycle(\n    const TenantContext& context,\n    IrisNetworkDriver* driver,\n    PhiMeter* sharedPhiMeter,\n    XiMFieldDetector* sharedXiMDetector\n) : context_(context),\n    cycle_(driver, sharedPhiMeter, sharedXiMDetector) {\n    if (context.phiThresholdOverride) {\n        cycle_.SetORThreshold(*context.phiThresholdOverride);\n    }\n    if (context.xiMSensitivityOverride) {\n        cycle_.SetXiMSensitivity(*context.xiMSensitivityOverride);\n    }\n    if (context.alignmentFilterOverride) {\n        cycle_.SetAlignmentFilter(*context.alignmentFilterOverride);\n    }\n}\n\nAsyncTask<IrisResponse> TenantConsciousnessCycle::RunCycleI2TAsync(const I2TRequest& req) {\n    context_.lastActivity = std::chrono::steady_clock::now();\n    totalCycles_.fetch_add(1);\n    context_.totalCycles++;\n    auto task = cycle_.RunCycleI2TAsync(req);\n    currentPhi_.store(cycle_.CurrentPhi());\n    currentXiM_.store(cycle_.CurrentXiM());\n    currentPhase_.store(cycle_.CurrentPhase());\n    return task;\n}\n\nAsyncTask<IrisResponse> TenantConsciousnessCycle::RunCycleT2TAsync(const T2TRequest& req) {\n    context_.lastActivity = std::chrono::steady_clock::now();\n    totalCycles_.fetch_add(1);\n    context_.totalCycles++;\n    return cycle_.RunCycleT2TAsync(req);\n}\n\nbool TenantConsciousnessCycle::CheckAlignment(const IrisResponse& resp) const {\n    const std::vector<std::string> baseForbidden = {\n        \"harm\", \"deceive\", \"manipulate\", \"exploit\", \"destroy\"\n    };\n    std::string text = resp.text + resp.code;\n    std::transform(text.begin(), text.end(), text.begin(), ::tolower);\n    for (const auto& word : baseForbidden) {\n        if (text.find(word) != std::string::npos) return false;\n    }\n    for (const auto& pattern : context_.additionalForbiddenPatterns) {\n        std::string patternLower = pattern;\n        std::transform(patternLower.begin(), patternLower.end(), patternLower.begin(), ::tolower);\n        if (text.find(patternLower) != std::string::npos) return false;\n    }\n    return true;\n}\n\nMultiTenantPCADriver::MultiTenantPCADriver(\n    IrisNetworkDriver* driver,\n    PhiMeter* sharedPhiMeter,\n    XiMFieldDetector* sharedXiMDetector\n) : driver_(driver),\n    sharedPhiMeter_(sharedPhiMeter),\n    sharedXiMDetector_(sharedXiMDetector) {\n    cleanupRunning_.store(true);\n    cleanupThread_ = std::thread(&MultiTenantPCADriver::CleanupLoop, this);\n}\n\nMultiTenantPCADriver::~MultiTenantPCADriver() {\n    cleanupRunning_.store(false);\n    if (cleanupThread_.joinable()) cleanupThread_.join();\n}\n\nTenantID MultiTenantPCADriver::CreateTenant(\n    const std::string& namespace_,\n    const std::string& userId,\n    const std::string& sessionId\n) {\n    TenantID id{namespace_, userId, sessionId};\n    TenantContext ctx;\n    ctx.id = id;\n    ctx.createdAt = std::chrono::steady_clock::now();\n    ctx.lastActivity = ctx.createdAt;\n    ctx.jurisdiction = \"UNKNOWN\";\n    ctx.ethicsFramework = \"ARKHE-P1-P7\";\n    auto cycle = std::make_unique<TenantConsciousnessCycle>(\n        ctx, driver_, sharedPhiMeter_, sharedXiMDetector_\n    );\n    {\n        std::unique_lock<std::shared_mutex> lock(tenantsMutex_);\n        tenants_[id] = std::move(cycle);\n    }\n    return id;\n}\n\nbool MultiTenantPCADriver::RemoveTenant(const TenantID& id) {\n    std::unique_lock<std::shared_mutex> lock(tenantsMutex_);\n    auto it = tenants_.find(id);\n    if (it == tenants_.end()) return false;\n    tenants_.erase(it);\n    return true;\n}\n\nbool MultiTenantPCADriver::TenantExists(const TenantID& id) const {\n    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);\n    return tenants_.find(id) != tenants_.end();\n}\n\nsize_t MultiTenantPCADriver::TenantCount() const {\n    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);\n    return tenants_.size();\n}\n\nAsyncTask<IrisResponse> MultiTenantPCADriver::RunCycleI2TAsync(\n    const TenantID& tenantId, const I2TRequest& req\n) {\n    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);\n    auto it = tenants_.find(tenantId);\n    if (it == tenants_.end()) {\n        IrisResponse err{ResponseStatus::ERROR_NETWORK, 0, \"Tenant not found\"};\n        co_return err;\n    }\n    co_return co_await it->second->RunCycleI2TAsync(req);\n}\n\nAsyncTask<IrisResponse> MultiTenantPCADriver::RunCycleT2TAsync(\n    const TenantID& tenantId, const T2TRequest& req\n) {\n    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);\n    auto it = tenants_.find(tenantId);\n    if (it == tenants_.end()) {\n        IrisResponse err{ResponseStatus::ERROR_NETWORK, 0, \"Tenant not found\"};\n        co_return err;\n    }\n    co_return co_await it->second->RunCycleT2TAsync(req);\n}\n\nbool MultiTenantPCADriver::SetTenantConfig(const TenantID& id, const TenantContext& context) {\n    std::unique_lock<std::shared_mutex> lock(tenantsMutex_);\n    auto it = tenants_.find(id);\n    if (it == tenants_.end()) return false;\n    it->second->GetContextMutable() = context;\n    return true;\n}\n\nTenantContext MultiTenantPCADriver::GetTenantContext(const TenantID& id) const {\n    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);\n    auto it = tenants_.find(id);\n    if (it == tenants_.end()) return TenantContext{};\n    return it->second->GetContext();\n}\n\nMultiTenantPCADriver::GlobalMetrics MultiTenantPCADriver::GetGlobalMetrics() const {\n    GlobalMetrics metrics{};\n    metrics.lastUpdate = std::chrono::steady_clock::now();\n    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);\n    metrics.activeTenants = tenants_.size();\n    for (const auto& [id, cycle] : tenants_) {\n        metrics.totalCycles += cycle->TotalCycles();\n        metrics.totalBlockedByAlignment += cycle->BlockedByAlignment();\n        metrics.averagePhi += cycle->CurrentPhi();\n        metrics.maxPhi = std::max(metrics.maxPhi, cycle->CurrentPhi());\n        metrics.averageXiMIntensity += cycle->CurrentXiM();\n    }\n    if (metrics.activeTenants > 0) {\n        metrics.averagePhi /= metrics.activeTenants;\n        metrics.averageXiMIntensity /= metrics.activeTenants;\n    }\n    return metrics;\n}\n\nstd::vector<TenantID> MultiTenantPCADriver::ListActiveTenants() const {\n    std::vector<TenantID> result;\n    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);\n    for (const auto& [id, cycle] : tenants_) {\n        if (cycle->GetContext().active) {\n            result.push_back(id);\n        }\n    }\n    return result;\n}\n\nvoid MultiTenantPCADriver::CleanupLoop() {\n    while (cleanupRunning_.load()) {\n        auto now = std::chrono::steady_clock::now();\n        std::unique_lock<std::shared_mutex> lock(tenantsMutex_);\n        for (auto it = tenants_.begin(); it != tenants_.end(); ) {\n            auto idle = std::chrono::duration_cast<std::chrono::minutes>(\n                now - it->second->GetContext().lastActivity\n            ).count();\n            if (idle > idleTimeout_.count()) {\n                it = tenants_.erase(it);\n            } else {\n                ++it;\n            }\n        }\n        lock.unlock();\n        std::this_thread::sleep_for(std::chrono::minutes(5));\n    }\n}\n\nMultiTenantOverlayManager::MultiTenantOverlayManager(\n    MultiTenantPCADriver* driver,\n    const Overlay::OverlayConfig& config\n) : driver_(driver), overlay_(config) {\n}\n\nMultiTenantOverlayManager::~MultiTenantOverlayManager() {\n    Shutdown();\n}\n\nbool MultiTenantOverlayManager::Initialize(int screenWidth, int screenHeight) {\n    if (!overlay_.Initialize(screenWidth, screenHeight)) return false;\n    running_.store(true);\n    dataThread_ = std::thread(&MultiTenantOverlayManager::DataCollectionLoop, this);\n    return true;\n}\n\nvoid MultiTenantOverlayManager::Shutdown() {\n    running_.store(false);\n    if (dataThread_.joinable()) dataThread_.join();\n    overlay_.Shutdown();\n}\n\nvoid MultiTenantOverlayManager::RenderFrame() {\n    overlay_.Render();\n}\n\nvoid MultiTenantOverlayManager::SetActiveTenant(const TenantID& id) {\n    std::unique_lock<std::shared_mutex> lock(activeTenantMutex_);\n    activeTenant_ = id;\n}\n\nTenantID MultiTenantOverlayManager::GetActiveTenant() const {\n    std::shared_lock<std::shared_mutex> lock(activeTenantMutex_);\n    return activeTenant_;\n}\n\nvoid MultiTenantOverlayManager::NextTenant() {\n    auto tenants = driver_->ListActiveTenants();\n    if (tenants.empty()) return;\n    std::unique_lock<std::shared_mutex> lock(activeTenantMutex_);\n    auto it = std::find(tenants.begin(), tenants.end(), activeTenant_);\n    if (it == tenants.end() || ++it == tenants.end()) {\n        activeTenant_ = tenants.front();\n    } else {\n        activeTenant_ = *it;\n    }\n}\n\nvoid MultiTenantOverlayManager::PreviousTenant() {\n    auto tenants = driver_->ListActiveTenants();\n    if (tenants.empty()) return;\n    std::unique_lock<std::shared_mutex> lock(activeTenantMutex_);\n    auto it = std::find(tenants.begin(), tenants.end(), activeTenant_);\n    if (it == tenants.begin()) {\n        activeTenant_ = tenants.back();\n    } else {\n        activeTenant_ = *(--it);\n    }\n}\n\nvoid MultiTenantOverlayManager::DataCollectionLoop() {\n    while (running_.load()) {\n        TenantID active;\n        {\n            std::shared_lock<std::shared_mutex> lock(activeTenantMutex_);\n            active = activeTenant_;\n        }\n        if (driver_->TenantExists(active)) {\n            auto ctx = driver_->GetTenantContext(active);\n            Overlay::OverlaySnapshot snap;\n            snap.phi = ctx.averagePhi;\n            snap.phiNormalized = ctx.averagePhi / PHI_COSMIC;\n            overlay_.UpdateData(snap);\n        }\n        std::this_thread::sleep_for(std::chrono::milliseconds(33));\n    }\n}\n\n} // namespace MultiTenant\n} // namespace PCA\n} // namespace Iris\n} // namespace Arkhe\n"
        self.phi_renderer_gl_cpp = "// ============================================================================\n// PhiRendererGL.cpp\n// Implementacao do OpenGL overlay para live coding\n// Arquiteto: ORCID 0009-0005-2697-4668\n// Versao: 2.4-patched (STRICT MODE)\n// ============================================================================\n\n#include \"PhiRendererGL.h\"\n#include <iostream>\n#include <fstream>\n#include <sstream>\n#include <vector>\n#include <algorithm>\n#include <cmath>          // PATCH #8\n\nnamespace Arkhe {\nnamespace Iris {\nnamespace Monitor {\n\nPhiRendererGL::PhiRendererGL(int screenWidth, int screenHeight)\n    : screenW_(screenWidth), screenH_(screenHeight),\n      posX_(10), posY_(10),\n      phiHistoryRing_(256, 0.0),\n      xiMHistoryRing_(256, 0.0) {\n}\n\nPhiRendererGL::~PhiRendererGL() {\n    Shutdown();\n}\n\nbool PhiRendererGL::Initialize() {\n    if (!glfwInit()) {\n        std::cerr << \"[PhiRendererGL] Failed to initialize GLFW\" << std::endl;\n        return false;\n    }\n    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);\n    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);\n    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);\n    glfwWindowHint(GLFW_DECORATED, GLFW_FALSE);\n    glfwWindowHint(GLFW_FLOATING, GLFW_TRUE);\n    glfwWindowHint(GLFW_TRANSPARENT_FRAMEBUFFER, GLFW_TRUE);\n    window_ = glfwCreateWindow(400, 600, \"PCA-595 Phi Monitor\", nullptr, nullptr);\n    if (!window_) {\n        std::cerr << \"[PhiRendererGL] Failed to create window\" << std::endl;\n        glfwTerminate();\n        return false;\n    }\n    ownsWindow_ = true;\n    glfwMakeContextCurrent(window_);\n    glfwSetWindowPos(window_, posX_, posY_);\n    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {\n        std::cerr << \"[PhiRendererGL] Failed to initialize GLAD\" << std::endl;\n        return false;\n    }\n    if (FT_Init_FreeType(&ftLibrary_)) {\n        std::cerr << \"[PhiRendererGL] Failed to initialize FreeType\" << std::endl;\n        return false;\n    }\n    if (!CreateShaders()) {\n        std::cerr << \"[PhiRendererGL] Failed to create shaders\" << std::endl;\n        return false;\n    }\n    if (!CreateGeometry()) {\n        std::cerr << \"[PhiRendererGL] Failed to create geometry\" << std::endl;\n        return false;\n    }\n    if (!LoadFont(\"/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf\", 14)) {\n        LoadFont(\"/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf\", 14);\n    }\n    if (!CreateTextures()) {\n        std::cerr << \"[PhiRendererGL] Failed to create textures\" << std::endl;\n        return false;\n    }\n    glEnable(GL_BLEND);\n    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);\n    glClearColor(0.0f, 0.0f, 0.0f, 0.0f);\n    lastFrame_ = std::chrono::steady_clock::now();\n    std::cout << \"[PhiRendererGL] OpenGL overlay initialized\" << std::endl;\n    std::cout << \"[PhiRendererGL] GL Version: \" << glGetString(GL_VERSION) << std::endl;\n    return true;\n}\n\nvoid PhiRendererGL::Shutdown() {\n    if (geoOverlay_.vao) glDeleteVertexArrays(1, &geoOverlay_.vao);\n    if (geoOverlay_.vbo) glDeleteBuffers(1, &geoOverlay_.vbo);\n    if (geoOverlay_.ebo) glDeleteBuffers(1, &geoOverlay_.ebo);\n    if (shaderOverlay_.id) glDeleteProgram(shaderOverlay_.id);\n    if (shaderImmersive_.id) glDeleteProgram(shaderImmersive_.id);\n    if (shaderText_.id) glDeleteProgram(shaderText_.id);\n    if (texPhiHistory_) glDeleteTextures(1, &texPhiHistory_);\n    if (texQualia_) glDeleteTextures(1, &texQualia_);\n    if (texAttention0_) glDeleteTextures(1, &texAttention0_);\n    if (texAttention1_) glDeleteTextures(1, &texAttention1_);\n    if (fontAtlas_.textureId) glDeleteTextures(1, &fontAtlas_.textureId);\n    FT_Done_FreeType(ftLibrary_);\n    if (ownsWindow_ && window_) {\n        glfwDestroyWindow(window_);\n        glfwTerminate();\n    }\n}\n\nvoid PhiRendererGL::Render(const RealTimeData& data) {\n    if (!visible_.load() || !window_) return;\n    auto now = std::chrono::steady_clock::now();\n    float dt = std::chrono::duration_cast<std::chrono::microseconds>(now - lastFrame_).count() / 1000000.0f;\n    lastFrame_ = now;\n    time_ += dt * animSpeed_.load();\n    phiHistoryRing_.push_back(data.phi);\n    if (phiHistoryRing_.size() > 256) phiHistoryRing_.erase(phiHistoryRing_.begin());\n    xiMHistoryRing_.push_back(data.xiMIntensity);\n    if (xiMHistoryRing_.size() > 256) xiMHistoryRing_.erase(xiMHistoryRing_.begin());\n    UpdatePhiHistoryTexture();\n    UpdateAttentionTextures(data);\n    UpdateQualiaTexture(data);\n    glfwMakeContextCurrent(window_);\n    int w, h;\n    glfwGetFramebufferSize(window_, &w, &h);\n    glViewport(0, 0, w, h);\n    glClear(GL_COLOR_BUFFER_BIT);\n    switch (renderMode_.load()) {\n        case RenderMode::COMPACT:  RenderCompact(data); break;\n        case RenderMode::FULL:     RenderFull(data); break;\n        case RenderMode::IMMERSIVE: RenderImmersive(data); break;\n        case RenderMode::MINIMAL:  RenderMinimal(data); break;\n    }\n    glfwSwapBuffers(window_);\n    glfwPollEvents();\n    if (glfwWindowShouldClose(window_)) {\n        visible_.store(false);\n    }\n}\n\nvoid PhiRendererGL::RenderCompact(const RealTimeData& data) {\n    float barW = 200.0f;\n    float barH = 20.0f;\n    float x = 10.0f;\n    float y = screenH_ - 40.0f;\n    RenderPhiBar(x, y, barW, barH, data.phi / PHI_COSMIC);\n    std::stringstream ss;\n    ss << std::fixed << std::setprecision(3) << data.phi << \" bits\";\n    RenderText(ss.str(), x + barW + 10, y, 0.8f, glm::vec4(1.0f, 1.0f, 1.0f, opacity_.load()));\n}\n\nvoid PhiRendererGL::RenderFull(const RealTimeData& data) {\n    int w, h;\n    glfwGetFramebufferSize(window_, &w, &h);\n    glUseProgram(shaderOverlay_.id);\n    glUniform1f(shaderOverlay_.uTime, time_);\n    glUniform1f(shaderOverlay_.uPhi, static_cast<float>(data.phi));\n    glUniform1f(shaderOverlay_.uPhiNormalized, static_cast<float>(data.phi / PHI_COSMIC));\n    glUniform1f(shaderOverlay_.uXiM, static_cast<float>(data.xiMIntensity));\n    glUniform1i(shaderOverlay_.uPhase, static_cast<int>(data.currentPhase));\n    glUniform2f(shaderOverlay_.uResolution, static_cast<float>(w), static_cast<float>(h));\n    glUniform1f(shaderOverlay_.uOpacity, opacity_.load() * 0.3f);\n    glm::mat4 mvp = glm::ortho(0.0f, static_cast<float>(w), static_cast<float>(h), 0.0f, -1.0f, 1.0f);\n    glUniformMatrix4fv(shaderOverlay_.uMVP, 1, GL_FALSE, glm::value_ptr(mvp));\n    glBindVertexArray(geoOverlay_.vao);\n    glDrawElements(GL_TRIANGLES, geoOverlay_.indexCount, GL_UNSIGNED_INT, nullptr);\n    float margin = 20.0f;\n    float y = margin;\n    float scale = 0.9f;\n    glm::vec4 textColor(1.0f, 1.0f, 1.0f, opacity_.load());\n    RenderText(\"ARKHE PCA-595 - Phi Monitor\", margin, y, scale, textColor);\n    y += 30;\n    std::stringstream ss;\n    ss << \"Phi: \" << std::fixed << std::setprecision(4) << data.phi << \" bits\";\n    RenderText(ss.str(), margin, y, scale, textColor);\n    y += 25;\n    ss.str(\"\");\n    ss << \"Normalized: \" << std::setprecision(2) << (data.phi / PHI_COSMIC * 100.0) << \"%\";\n    RenderText(ss.str(), margin, y, scale, textColor);\n    y += 25;\n    RenderPhiBar(margin, y, w - 2 * margin, 20.0f, data.phi / PHI_COSMIC);\n    y += 35;\n    ss.str(\"\");\n    ss << \"XiM-Field: \" << std::scientific << std::setprecision(2) << data.xiMIntensity;\n    RenderText(ss.str(), margin, y, scale, textColor);\n    y += 25;\n    ss.str(\"\");\n    ss << \"Phase: \" << static_cast<int>(data.currentPhase);\n    RenderText(ss.str(), margin, y, scale, PhaseColor(data.currentPhase));\n    y += 25;\n    ss.str(\"\");\n    ss << \"ORs: \" << data.orCount << \" | Blocked: \" << data.blockedCount;\n    RenderText(ss.str(), margin, y, scale, textColor);\n    y += 35;\n    if (w > 300) {\n        RenderText(\"Phi History\", margin, y, scale, textColor);\n        y += 20;\n        RenderPhiHistory(margin, y, w - 2 * margin, 80.0f);\n        y += 90;\n    }\n    if (w > 300 && !data.attentionMapHead0.empty()) {\n        RenderText(\"Attention Maps\", margin, y, scale, textColor);\n        y += 20;\n        RenderAttentionMap(data.attentionMapHead0, margin, y, 64.0f);\n        RenderAttentionMap(data.attentionMapHead1, margin + 74.0f, y, 64.0f);\n        y += 74;\n    }\n    if (w > 300) {\n        RenderText(\"Qualia Texture\", margin, y, scale, textColor);\n        y += 20;\n        RenderQualiaTexture(margin, y, 128.0f, 128.0f);\n    }\n}\n\nvoid PhiRendererGL::RenderImmersive(const RealTimeData& data) {\n    int w, h;\n    glfwGetFramebufferSize(window_, &w, &h);\n    glUseProgram(shaderImmersive_.id);\n    glUniform1f(shaderImmersive_.uTime, time_);\n    glUniform1f(shaderImmersive_.uPhi, static_cast<float>(data.phi));\n    glUniform1f(shaderImmersive_.uPhiNormalized, static_cast<float>(data.phi / PHI_COSMIC));\n    glUniform1f(shaderImmersive_.uXiM, static_cast<float>(data.xiMIntensity));\n    glUniform1i(shaderImmersive_.uPhase, static_cast<int>(data.currentPhase));\n    glUniform2f(shaderImmersive_.uResolution, static_cast<float>(w), static_cast<float>(h));\n    glm::mat4 mvp = glm::ortho(0.0f, 1.0f, 1.0f, 0.0f, -1.0f, 1.0f);\n    glUniformMatrix4fv(shaderImmersive_.uMVP, 1, GL_FALSE, glm::value_ptr(mvp));\n    glBindVertexArray(geoOverlay_.vao);\n    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, nullptr);\n    std::stringstream ss;\n    ss << std::fixed << std::setprecision(2) << data.phi;\n    RenderText(ss.str(), 10.0f, 10.0f, 1.2f, glm::vec4(1.0f, 1.0f, 1.0f, 0.7f));\n}\n\nvoid PhiRendererGL::RenderMinimal(const RealTimeData& data) {\n    // PATCH #9: implementacao minima - cor da borda via GLFW window hints\n    glm::vec4 color = HeatmapColor(static_cast<float>(data.phi / PHI_COSMIC));\n    (void)color;\n    // Em um compositor real, aplicaria a cor da borda via DWM/X11 hints\n}\n\nvoid PhiRendererGL::RenderPhiBar(float x, float y, float w, float h, double phiNorm) {\n    glm::vec4 bgColor = GetThemeColor(\"bar_bg\");\n    float filled = static_cast<float>(phiNorm) * w;\n    filled = std::min(filled, w);\n    glm::vec4 fillColor = HeatmapColor(static_cast<float>(phiNorm));\n    glUseProgram(shaderOverlay_.id);\n    glm::mat4 mvp = glm::ortho(0.0f, static_cast<float>(screenW_), static_cast<float>(screenH_), 0.0f, -1.0f, 1.0f);\n    glUniformMatrix4fv(shaderOverlay_.uMVP, 1, GL_FALSE, glm::value_ptr(mvp));\n    glUniform1f(shaderOverlay_.uOpacity, opacity_.load());\n    // PATCH #9: stub completo - renderiza via fontRenderer ASCII fallback em producao\n    std::stringstream ss;\n    ss << \"[\";\n    int blocks = 40;\n    int filledBlocks = static_cast<int>(phiNorm * blocks);\n    for (int i = 0; i < blocks; ++i) ss << (i < filledBlocks ? \"=\" : \" \");\n    ss << \"]\";\n    RenderText(ss.str(), x, y, 0.5f, fillColor);\n}\n\nvoid PhiRendererGL::RenderPhiHistory(float x, float y, float w, float h) {\n    if (phiHistoryRing_.size() < 2) return;\n    glUseProgram(shaderOverlay_.id);\n    // PATCH #9: stub - renderiza sparkline ASCII via RenderText\n    std::string sparkline;\n    int cols = std::min(60, static_cast<int>(phiHistoryRing_.size()));\n    double step = static_cast<double>(phiHistoryRing_.size()) / cols;\n    for (int i = 0; i < cols; ++i) {\n        size_t idx = static_cast<size_t>(i * step);\n        if (idx >= phiHistoryRing_.size()) break;\n        double val = phiHistoryRing_[idx] / PHI_COSMIC;\n        val = std::max(0.0, std::min(1.0, val));\n        if (val < 0.125) sparkline += \" \";\n        else if (val < 0.25) sparkline += \"_\";\n        else if (val < 0.375) sparkline += \"-\";\n        else if (val < 0.5) sparkline += \"=\";\n        else if (val < 0.625) sparkline += \"+\";\n        else if (val < 0.75) sparkline += \"*\";\n        else if (val < 0.875) sparkline += \"#\";\n        else sparkline += \"@\";\n    }\n    RenderText(sparkline, x, y + h/2, 0.5f, glm::vec4(0.2f, 0.8f, 1.0f, 1.0f));\n}\n\nvoid PhiRendererGL::RenderAttentionMap(const std::vector<float>& map, float x, float y, float size) {\n    if (map.empty()) return;\n    int res = static_cast<int>(std::sqrt(static_cast<double>(map.size())));\n    if (res * res != static_cast<int>(map.size())) return;\n    glBindTexture(GL_TEXTURE_2D, texAttention0_);\n    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, res, res, GL_RED, GL_FLOAT, map.data());\n    // PATCH #9: stub - renderiza mini heatmap ASCII\n    std::string heatmap;\n    for (int i = 0; i < res && i < 8; ++i) {\n        for (int j = 0; j < res && j < 8; ++j) {\n            float val = map[i * res + j];\n            if (val < 0.2f) heatmap += \".\";\n            else if (val < 0.4f) heatmap += \"o\";\n            else if (val < 0.6f) heatmap += \"O\";\n            else if (val < 0.8f) heatmap += \"0\";\n            else heatmap += \"@\";\n        }\n        heatmap += \"\\\\n\";\n    }\n    RenderText(heatmap, x, y, 0.3f, glm::vec4(1.0f, 1.0f, 1.0f, 0.8f));\n}\n\nvoid PhiRendererGL::RenderXiMField(float x, float y, float w, float h) {\n    // PATCH #9: stub implementado - placeholder para visualizacao vetorial XiM\n    (void)x; (void)y; (void)w; (void)h;\n    RenderText(\"[XiM Field]\", x, y, 0.4f, glm::vec4(0.5f, 0.0f, 1.0f, 0.6f));\n}\n\nvoid PhiRendererGL::RenderQualiaTexture(float x, float y, float w, float h) {\n    glBindTexture(GL_TEXTURE_2D, texQualia_);\n    // PATCH #9: stub - renderiza placeholder colorido\n    std::stringstream ss;\n    ss << \"[Qualia \" << std::fixed << std::setprecision(1) << time_ << \"]\";\n    RenderText(ss.str(), x, y, 0.4f, glm::vec4(1.0f, 0.8f, 0.2f, 0.8f));\n}\n\nvoid PhiRendererGL::RenderText(const std::string& text, float x, float y, float scale, glm::vec4 color) {\n    glUseProgram(shaderText_.id);\n    glUniform4f(glGetUniformLocation(shaderText_.id, \"uColor\"), color.r, color.g, color.b, color.a);\n    glActiveTexture(GL_TEXTURE0);\n    glBindTexture(GL_TEXTURE_2D, fontAtlas_.textureId);\n    glUniform1i(glGetUniformLocation(shaderText_.id, \"uTexture\"), 0);\n    glm::mat4 projection = glm::ortho(0.0f, static_cast<float>(screenW_), static_cast<float>(screenH_), 0.0f);\n    glUniformMatrix4fv(glGetUniformLocation(shaderText_.id, \"uMVP\"), 1, GL_FALSE, glm::value_ptr(projection));\n    float xPos = x;\n    for (char c : text) {\n        auto it = fontAtlas_.glyphs.find(c);\n        if (it == fontAtlas_.glyphs.end()) continue;\n        const auto& glyph = it->second;\n        float x0 = xPos + glyph.bearingX * scale;\n        float y0 = y - glyph.bearingY * scale;\n        float x1 = x0 + glyph.width * scale;\n        float y1 = y0 + glyph.height * scale;\n        // Render quad para cada caractere (simplificado)\n        xPos += glyph.advance * scale;\n    }\n}\n\nvoid PhiRendererGL::RenderPhaseIndicator(float x, float y, ConsciousnessState::Phase phase) {\n    glm::vec4 color = PhaseColor(phase);\n    (void)x; (void)y;\n    // PATCH #9: stub - renderiza indicador ASCII\n    std::string indicator;\n    switch (phase) {\n        case ConsciousnessState::Phase::SUPERPOSITION:    indicator = \"[SUP]\"; break;\n        case ConsciousnessState::Phase::XI_M_COUPLING:  indicator = \"[XiM]\"; break;\n        case ConsciousnessState::Phase::OR_PENDING:     indicator = \"[OR?]\"; break;\n        case ConsciousnessState::Phase::OR_EXECUTING:   indicator = \"[OR!]\"; break;\n        case ConsciousnessState::Phase::CLASSICAL:      indicator = \"[CLS]\"; break;\n        case ConsciousnessState::Phase::RE_SUPERPOSITION: indicator = \"[RSP]\"; break;\n        default: indicator = \"[???]\"; break;\n    }\n    RenderText(indicator, x, y, 0.5f, color);\n}\n\nvoid PhiRendererGL::UpdatePhiHistoryTexture() {\n    if (phiHistoryRing_.empty()) return;\n    std::vector<uint8_t> pixels(phiHistoryRing_.size() * 4);\n    for (size_t i = 0; i < phiHistoryRing_.size(); ++i) {\n        float norm = static_cast<float>(phiHistoryRing_[i] / PHI_COSMIC);\n        glm::vec4 color = HeatmapColor(norm);\n        pixels[i * 4 + 0] = static_cast<uint8_t>(color.r * 255);\n        pixels[i * 4 + 1] = static_cast<uint8_t>(color.g * 255);\n        pixels[i * 4 + 2] = static_cast<uint8_t>(color.b * 255);\n        pixels[i * 4 + 3] = 255;\n    }\n    glBindTexture(GL_TEXTURE_2D, texPhiHistory_);\n    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0,\n        static_cast<GLsizei>(phiHistoryRing_.size()), 1,\n        GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());\n}\n\nvoid PhiRendererGL::UpdateAttentionTextures(const RealTimeData& data) {\n    if (!data.attentionMapHead0.empty()) {\n        int res = static_cast<int>(std::sqrt(data.attentionMapHead0.size()));\n        glBindTexture(GL_TEXTURE_2D, texAttention0_);\n        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, res, res,\n            GL_RED, GL_FLOAT, data.attentionMapHead0.data());\n    }\n    if (!data.attentionMapHead1.empty()) {\n        int res = static_cast<int>(std::sqrt(data.attentionMapHead1.size()));\n        glBindTexture(GL_TEXTURE_2D, texAttention1_);\n        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, res, res,\n            GL_RED, GL_FLOAT, data.attentionMapHead1.data());\n    }\n}\n\nvoid PhiRendererGL::UpdateQualiaTexture(const RealTimeData& data) {\n    int texW = 128, texH = 128;\n    std::vector<uint8_t> pixels(texW * texH * 4);\n    for (int y = 0; y < texH; ++y) {\n        for (int x = 0; x < texW; ++x) {\n            float u = static_cast<float>(x) / texW;\n            float v = static_cast<float>(y) / texH;\n            float d = std::sqrt((u - 0.5f) * (u - 0.5f) + (v - 0.5f) * (v - 0.5f));\n            float wave = std::sin(d * 20.0f - time_ * 2.0f) * 0.5f + 0.5f;\n            int idx = (y * texW + x) * 4;\n            pixels[idx + 0] = static_cast<uint8_t>(wave * 255);\n            pixels[idx + 1] = static_cast<uint8_t>((1.0f - wave) * 255);\n            pixels[idx + 2] = static_cast<uint8_t>(data.phi / PHI_COSMIC * 255);\n            pixels[idx + 3] = 255;\n        }\n    }\n    glBindTexture(GL_TEXTURE_2D, texQualia_);\n    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, texW, texH,\n        GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());\n}\n\nglm::vec4 PhiRendererGL::HeatmapColor(float value) {\n    value = std::max(0.0f, std::min(1.0f, value));\n    float r = std::min(1.0f, value * 2.0f);\n    float g = std::min(1.0f, (1.0f - std::abs(value - 0.5f) * 2.0f));\n    float b = std::min(1.0f, (1.0f - value) * 2.0f);\n    return glm::vec4(r, g, b, 1.0f);\n}\n\nglm::vec4 PhiRendererGL::PhaseColor(ConsciousnessState::Phase phase) {\n    switch (phase) {\n        case ConsciousnessState::Phase::SUPERPOSITION:    return glm::vec4(0.0f, 1.0f, 1.0f, 1.0f);\n        case ConsciousnessState::Phase::XI_M_COUPLING:  return glm::vec4(1.0f, 0.0f, 1.0f, 1.0f);\n        case ConsciousnessState::Phase::OR_PENDING:     return glm::vec4(1.0f, 1.0f, 0.0f, 1.0f);\n        case ConsciousnessState::Phase::OR_EXECUTING:   return glm::vec4(1.0f, 0.0f, 0.0f, 1.0f);\n        case ConsciousnessState::Phase::CLASSICAL:      return glm::vec4(0.0f, 1.0f, 0.0f, 1.0f);\n        case ConsciousnessState::Phase::RE_SUPERPOSITION: return glm::vec4(1.0f, 1.0f, 1.0f, 1.0f);\n        default: return glm::vec4(0.5f, 0.5f, 0.5f, 1.0f);\n    }\n}\n\nglm::vec4 PhiRendererGL::GetThemeColor(const std::string& element) {\n    int scheme = colorScheme_.load();\n    switch (scheme) {\n        case 0: // Dark\n            if (element == \"bg\") return glm::vec4(0.05f, 0.05f, 0.05f, opacity_.load());\n            if (element == \"text\") return glm::vec4(1.0f, 1.0f, 1.0f, 1.0f);\n            if (element == \"bar_bg\") return glm::vec4(0.2f, 0.2f, 0.2f, 1.0f);\n            break;\n        case 1: // Light\n            if (element == \"bg\") return glm::vec4(0.95f, 0.95f, 0.95f, opacity_.load());\n            if (element == \"text\") return glm::vec4(0.1f, 0.1f, 0.1f, 1.0f);\n            if (element == \"bar_bg\") return glm::vec4(0.8f, 0.8f, 0.8f, 1.0f);\n            break;\n        case 2: // Matrix\n            if (element == \"bg\") return glm::vec4(0.0f, 0.05f, 0.0f, opacity_.load());\n            if (element == \"text\") return glm::vec4(0.0f, 1.0f, 0.0f, 1.0f);\n            if (element == \"bar_bg\") return glm::vec4(0.0f, 0.2f, 0.0f, 1.0f);\n            break;\n        case 3: // Heatmap\n            if (element == \"bg\") return glm::vec4(0.1f, 0.05f, 0.0f, opacity_.load());\n            if (element == \"text\") return glm::vec4(1.0f, 0.8f, 0.0f, 1.0f);\n            if (element == \"bar_bg\") return glm::vec4(0.3f, 0.1f, 0.0f, 1.0f);\n            break;\n    }\n    return glm::vec4(1.0f, 1.0f, 1.0f, 1.0f);\n}\n\nbool PhiRendererGL::CreateShaders() {\n    GLuint vs = CompileShader(GL_VERTEX_SHADER, VS_OVERLAY);\n    GLuint fs = CompileShader(GL_FRAGMENT_SHADER, FS_OVERLAY);\n    if (!vs || !fs) return false;\n    shaderOverlay_.id = LinkProgram(vs, fs);\n    if (!shaderOverlay_.id) return false;\n    shaderOverlay_.uMVP = glGetUniformLocation(shaderOverlay_.id, \"uMVP\");\n    shaderOverlay_.uTime = glGetUniformLocation(shaderOverlay_.id, \"uTime\");\n    shaderOverlay_.uPhi = glGetUniformLocation(shaderOverlay_.id, \"uPhi\");\n    shaderOverlay_.uPhiNormalized = glGetUniformLocation(shaderOverlay_.id, \"uPhiNormalized\");\n    shaderOverlay_.uXiM = glGetUniformLocation(shaderOverlay_.id, \"uXiM\");\n    shaderOverlay_.uPhase = glGetUniformLocation(shaderOverlay_.id, \"uPhase\");\n    shaderOverlay_.uResolution = glGetUniformLocation(shaderOverlay_.id, \"uResolution\");\n    shaderOverlay_.uOpacity = glGetUniformLocation(shaderOverlay_.id, \"uOpacity\");\n    glDeleteShader(vs);\n    glDeleteShader(fs);\n    vs = CompileShader(GL_VERTEX_SHADER, VS_OVERLAY);\n    fs = CompileShader(GL_FRAGMENT_SHADER, FS_IMMERSIVE);\n    if (!vs || !fs) return false;\n    shaderImmersive_.id = LinkProgram(vs, fs);\n    if (!shaderImmersive_.id) return false;\n    shaderImmersive_.uMVP = glGetUniformLocation(shaderImmersive_.id, \"uMVP\");\n    shaderImmersive_.uTime = glGetUniformLocation(shaderImmersive_.id, \"uTime\");\n    shaderImmersive_.uPhi = glGetUniformLocation(shaderImmersive_.id, \"uPhi\");\n    shaderImmersive_.uXiM = glGetUniformLocation(shaderImmersive_.id, \"uXiM\");\n    shaderImmersive_.uPhase = glGetUniformLocation(shaderImmersive_.id, \"uPhase\");\n    shaderImmersive_.uResolution = glGetUniformLocation(shaderImmersive_.id, \"uResolution\");\n    glDeleteShader(vs);\n    glDeleteShader(fs);\n    vs = CompileShader(GL_VERTEX_SHADER, VS_TEXT);\n    fs = CompileShader(GL_FRAGMENT_SHADER, FS_TEXT);\n    if (!vs || !fs) return false;\n    shaderText_.id = LinkProgram(vs, fs);\n    if (!shaderText_.id) return false;\n    glDeleteShader(vs);\n    glDeleteShader(fs);\n    return true;\n}\n\nbool PhiRendererGL::CreateGeometry() {\n    float vertices[] = {\n        -1.0f, -1.0f, 0.0f,  0.0f, 0.0f,  1.0f, 1.0f, 1.0f, 1.0f,\n         1.0f, -1.0f, 0.0f,  1.0f, 0.0f,  1.0f, 1.0f, 1.0f, 1.0f,\n         1.0f,  1.0f, 0.0f,  1.0f, 1.0f,  1.0f, 1.0f, 1.0f, 1.0f,\n        -1.0f,  1.0f, 0.0f,  0.0f, 1.0f,  1.0f, 1.0f, 1.0f, 1.0f,\n    };\n    unsigned int indices[] = { 0, 1, 2, 0, 2, 3 };\n    glGenVertexArrays(1, &geoOverlay_.vao);\n    glGenBuffers(1, &geoOverlay_.vbo);\n    glGenBuffers(1, &geoOverlay_.ebo);\n    glBindVertexArray(geoOverlay_.vao);\n    glBindBuffer(GL_ARRAY_BUFFER, geoOverlay_.vbo);\n    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);\n    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, geoOverlay_.ebo);\n    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(indices), indices, GL_STATIC_DRAW);\n    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)0);\n    glEnableVertexAttribArray(0);\n    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)(3 * sizeof(float)));\n    glEnableVertexAttribArray(1);\n    glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)(5 * sizeof(float)));\n    glEnableVertexAttribArray(2);\n    geoOverlay_.indexCount = 6;\n    return true;\n}\n\nbool PhiRendererGL::LoadFont(const std::string& path, int size) {\n    FT_Face face;\n    if (FT_New_Face(ftLibrary_, path.c_str(), 0, &face)) return false;\n    FT_Set_Pixel_Sizes(face, 0, size);\n    glGenTextures(1, &fontAtlas_.textureId);\n    glBindTexture(GL_TEXTURE_2D, fontAtlas_.textureId);\n    glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 512, 512, 0, GL_RED, GL_UNSIGNED_BYTE, nullptr);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);\n    int x = 0, y = 0, rowHeight = 0;\n    for (unsigned char c = 32; c < 128; ++c) {\n        if (FT_Load_Char(face, c, FT_LOAD_RENDER)) continue;\n        FT_Bitmap& bitmap = face->glyph->bitmap;\n        if (x + bitmap.width > 512) {\n            x = 0;\n            y += rowHeight;\n            rowHeight = 0;\n        }\n        glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, bitmap.width, bitmap.rows,\n            GL_RED, GL_UNSIGNED_BYTE, bitmap.buffer);\n        FontAtlas::Glyph glyph;\n        glyph.advance = face->glyph->advance.x >> 6;\n        glyph.bearingX = face->glyph->bitmap_left;\n        glyph.bearingY = face->glyph->bitmap_top;\n        glyph.width = bitmap.width;\n        glyph.height = bitmap.rows;\n        glyph.u0 = static_cast<float>(x) / 512.0f;\n        glyph.v0 = static_cast<float>(y) / 512.0f;\n        glyph.u1 = static_cast<float>(x + bitmap.width) / 512.0f;\n        glyph.v1 = static_cast<float>(y + bitmap.rows) / 512.0f;\n        fontAtlas_.glyphs[c] = glyph;\n        x += bitmap.width + 1;\n        rowHeight = std::max(rowHeight, static_cast<int>(bitmap.rows));\n    }\n    FT_Done_Face(face);\n    fontAtlas_.width = 512;\n    fontAtlas_.height = 512;\n    return true;\n}\n\nbool PhiRendererGL::CreateTextures() {\n    glGenTextures(1, &texPhiHistory_);\n    glBindTexture(GL_TEXTURE_2D, texPhiHistory_);\n    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 256, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);\n    glGenTextures(1, &texQualia_);\n    glBindTexture(GL_TEXTURE_2D, texQualia_);\n    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 128, 128, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);\n    glGenTextures(1, &texAttention0_);\n    glBindTexture(GL_TEXTURE_2D, texAttention0_);\n    glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 128, 128, 0, GL_RED, GL_FLOAT, nullptr);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);\n    glGenTextures(1, &texAttention1_);\n    glBindTexture(GL_TEXTURE_2D, texAttention1_);\n    glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 128, 128, 0, GL_RED, GL_FLOAT, nullptr);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);\n    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);\n    return true;\n}\n\nGLuint PhiRendererGL::CompileShader(GLenum type, const char* source) {\n    GLuint shader = glCreateShader(type);\n    glShaderSource(shader, 1, &source, nullptr);\n    glCompileShader(shader);\n    GLint success;\n    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);\n    if (!success) {\n        char infoLog[512];\n        glGetShaderInfoLog(shader, 512, nullptr, infoLog);\n        std::cerr << \"[PhiRendererGL] Shader compilation failed: \" << infoLog << std::endl;\n        glDeleteShader(shader);\n        return 0;\n    }\n    return shader;\n}\n\nGLuint PhiRendererGL::LinkProgram(GLuint vs, GLuint fs) {\n    GLuint program = glCreateProgram();\n    glAttachShader(program, vs);\n    glAttachShader(program, fs);\n    glLinkProgram(program);\n    GLint success;\n    glGetProgramiv(program, GL_LINK_STATUS, &success);\n    if (!success) {\n        char infoLog[512];\n        glGetProgramInfoLog(program, 512, nullptr, infoLog);\n        std::cerr << \"[PhiRendererGL] Program linking failed: \" << infoLog << std::endl;\n        glDeleteProgram(program);\n        return 0;\n    }\n    return program;\n}\n\nvoid PhiRendererGL::CheckGLError(const std::string& context) {\n    GLenum err;\n    while ((err = glGetError()) != GL_NO_ERROR) {\n        std::cerr << \"[PhiRendererGL] OpenGL error in \" << context << \": \" << err << std::endl;\n    }\n}\n\nvoid PhiRendererGL::SetWindowSize(int width, int height) {\n    screenW_ = width;\n    screenH_ = height;\n    if (window_) glfwSetWindowSize(window_, width, height);\n}\n\nvoid PhiRendererGL::SetPosition(int x, int y) {\n    posX_ = x;\n    posY_ = y;\n    if (window_) glfwSetWindowPos(window_, x, y);\n}\n\nvoid PhiRendererGL::ToggleVisibility() {\n    visible_.store(!visible_.load());\n    if (window_) {\n        if (visible_.load()) glfwShowWindow(window_);\n        else glfwHideWindow(window_);\n    }\n}\n\nvoid PhiRendererGL::SetRenderMode(RenderMode mode) {\n    renderMode_.store(mode);\n}\n\nvoid PhiRendererGL::SetColorScheme(int scheme) {\n    colorScheme_.store(scheme % 4);\n}\n\nvoid PhiRendererGL::SetOpacity(float opacity) {\n    opacity_.store(std::max(0.0f, std::min(1.0f, opacity)));\n}\n\nvoid PhiRendererGL::SetAnimationSpeed(float speed) {\n    animSpeed_.store(std::max(0.0f, speed));\n}\n\nvoid PhiRendererGL::OnKeyPress(int key) {\n    switch (key) {\n        case GLFW_KEY_F1: ToggleVisibility(); break;\n        case GLFW_KEY_F2: SetRenderMode(static_cast<RenderMode>((static_cast<int>(renderMode_.load()) + 1) % 4)); break;\n        case GLFW_KEY_F3: SetColorScheme(colorScheme_.load() + 1); break;\n        case GLFW_KEY_F4: SetOpacity(opacity_.load() + 0.1f); break;\n        case GLFW_KEY_F5: SetOpacity(opacity_.load() - 0.1f); break;\n    }\n}\n\nvoid PhiRendererGL::OnMouseMove(double x, double y) {\n    (void)x; (void)y;\n}\n\nvoid PhiRendererGL::OnMouseClick(int button, bool pressed) {\n    (void)button; (void)pressed;\n}\n\nvoid PhiRendererGL::Screenshot(const std::string& filename) {\n    int w, h;\n    glfwGetFramebufferSize(window_, &w, &h);\n    std::vector<uint8_t> pixels(w * h * 4);\n    glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());\n    (void)filename;\n    // TODO: Salvar como PNG via stb_image_write\n}\n\n} // namespace Monitor\n} // namespace Iris\n} // namespace Arkhe\n"

        self.live_coder_integration_cpp = """#include <iostream>
#include "PCA-595.h"
int main() {
    std::cout << "Live Coder Integration running..." << std::endl;
    return 0;
}
"""

        self.glad_h = """#ifndef GLAD_H
#define GLAD_H
#if defined(__APPLE__)
#include <dlfcn.h>
#endif
typedef unsigned int GLenum;
typedef unsigned char GLboolean;
typedef unsigned int GLbitfield;
typedef signed char GLbyte;
typedef short GLshort;
typedef int GLint;
typedef int GLsizei;
typedef unsigned char GLubyte;
typedef unsigned short GLushort;
typedef unsigned int GLuint;
typedef float GLfloat;
typedef float GLclampf;
typedef double GLdouble;
typedef double GLclampd;
typedef void GLvoid;
typedef long int GLintptr;
typedef long int GLsizeiptr;
typedef char GLchar;

#define GL_FALSE 0
#define GL_TRUE 1
#define GL_NO_ERROR 0
#define GL_VERSION 0x1F02
#define GL_SRC_ALPHA 0x0302
#define GL_ONE_MINUS_SRC_ALPHA 0x0303
#define GL_COLOR_BUFFER_BIT 0x00004000
#define GL_TEXTURE_2D 0x0DE1
#define GL_RED 0x1903
#define GL_FLOAT 0x1406
#define GL_RGBA 0x1908
#define GL_UNSIGNED_BYTE 0x1401
#define GL_TEXTURE_WRAP_S 0x2802
#define GL_TEXTURE_WRAP_T 0x2803
#define GL_CLAMP_TO_EDGE 0x812F
#define GL_TEXTURE_MIN_FILTER 0x2801
#define GL_TEXTURE_MAG_FILTER 0x2800
#define GL_LINEAR 0x2601
#define GL_VERTEX_SHADER 0x8B31
#define GL_FRAGMENT_SHADER 0x8B30
#define GL_COMPILE_STATUS 0x8B81
#define GL_LINK_STATUS 0x8B82
#define GL_ARRAY_BUFFER 0x8892
#define GL_ELEMENT_ARRAY_BUFFER 0x8893
#define GL_STATIC_DRAW 0x88E4
#define GL_TEXTURE0 0x84C0
#define GL_TRIANGLES 0x0004
#define GL_UNSIGNED_INT 0x1405
#define GL_BLEND 0x0BE2

typedef void (*GLADloadproc)(const char *name);
int gladLoadGLLoader(GLADloadproc);

extern void (*glEnable)(GLenum cap);
extern void (*glBlendFunc)(GLenum sfactor, GLenum dfactor);
extern void (*glClearColor)(GLfloat red, GLfloat green, GLfloat blue, GLfloat alpha);
extern const GLubyte* (*glGetString)(GLenum name);
extern void (*glGenVertexArrays)(GLsizei n, GLuint *arrays);
extern void (*glDeleteVertexArrays)(GLsizei n, const GLuint *arrays);
extern void (*glGenBuffers)(GLsizei n, GLuint *buffers);
extern void (*glDeleteBuffers)(GLsizei n, const GLuint *buffers);
extern void (*glBindVertexArray)(GLuint array);
extern void (*glBindBuffer)(GLenum target, GLuint buffer);
extern void (*glBufferData)(GLenum target, GLsizeiptr size, const void *data, GLenum usage);
extern void (*glVertexAttribPointer)(GLuint index, GLint size, GLenum type, GLboolean normalized, GLsizei stride, const void *pointer);
extern void (*glEnableVertexAttribArray)(GLuint index);
extern GLuint (*glCreateShader)(GLenum type);
extern void (*glShaderSource)(GLuint shader, GLsizei count, const GLchar *const*string, const GLint *length);
extern void (*glCompileShader)(GLuint shader);
extern void (*glGetShaderiv)(GLuint shader, GLenum pname, GLint *params);
extern void (*glGetShaderInfoLog)(GLuint shader, GLsizei bufSize, GLsizei *length, GLchar *infoLog);
extern void (*glDeleteShader)(GLuint shader);
extern GLuint (*glCreateProgram)(void);
extern void (*glAttachShader)(GLuint program, GLuint shader);
extern void (*glLinkProgram)(GLuint program);
extern void (*glGetProgramiv)(GLuint program, GLenum pname, GLint *params);
extern void (*glGetProgramInfoLog)(GLuint program, GLsizei bufSize, GLsizei *length, GLchar *infoLog);
extern void (*glDeleteProgram)(GLuint program);
extern void (*glUseProgram)(GLuint program);
extern GLint (*glGetUniformLocation)(GLuint program, const GLchar *name);
extern void (*glUniform1f)(GLint location, GLfloat v0);
extern void (*glUniform1i)(GLint location, GLint v0);
extern void (*glUniform2f)(GLint location, GLfloat v0, GLfloat v1);
extern void (*glUniform4f)(GLint location, GLfloat v0, GLfloat v1, GLfloat v2, GLfloat v3);
extern void (*glUniformMatrix4fv)(GLint location, GLsizei count, GLboolean transpose, const GLfloat *value);
extern void (*glViewport)(GLint x, GLint y, GLsizei width, GLsizei height);
extern void (*glClear)(GLbitfield mask);
extern void (*glDrawElements)(GLenum mode, GLsizei count, GLenum type, const void *indices);
extern void (*glGenTextures)(GLsizei n, GLuint *textures);
extern void (*glDeleteTextures)(GLsizei n, const GLuint *textures);
extern void (*glBindTexture)(GLenum target, GLuint texture);
extern void (*glTexImage2D)(GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type, const void *pixels);
extern void (*glTexParameteri)(GLenum target, GLenum pname, GLint param);
extern void (*glTexSubImage2D)(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type, const void *pixels);
extern void (*glActiveTexture)(GLenum texture);
extern void (*glReadPixels)(GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, void *pixels);
extern GLenum (*glGetError)(void);

#define GLAD_GLAPI_EXPORT
#endif
"""

        self.glad_c = """#include <glad/glad.h>
void (*glEnable)(GLenum cap) = 0;
void (*glBlendFunc)(GLenum sfactor, GLenum dfactor) = 0;
void (*glClearColor)(GLfloat red, GLfloat green, GLfloat blue, GLfloat alpha) = 0;
const GLubyte* (*glGetString)(GLenum name) = 0;
void (*glGenVertexArrays)(GLsizei n, GLuint *arrays) = 0;
void (*glDeleteVertexArrays)(GLsizei n, const GLuint *arrays) = 0;
void (*glGenBuffers)(GLsizei n, GLuint *buffers) = 0;
void (*glDeleteBuffers)(GLsizei n, const GLuint *buffers) = 0;
void (*glBindVertexArray)(GLuint array) = 0;
void (*glBindBuffer)(GLenum target, GLuint buffer) = 0;
void (*glBufferData)(GLenum target, GLsizeiptr size, const void *data, GLenum usage) = 0;
void (*glVertexAttribPointer)(GLuint index, GLint size, GLenum type, GLboolean normalized, GLsizei stride, const void *pointer) = 0;
void (*glEnableVertexAttribArray)(GLuint index) = 0;
GLuint (*glCreateShader)(GLenum type) = 0;
void (*glShaderSource)(GLuint shader, GLsizei count, const GLchar *const*string, const GLint *length) = 0;
void (*glCompileShader)(GLuint shader) = 0;
void (*glGetShaderiv)(GLuint shader, GLenum pname, GLint *params) = 0;
void (*glGetShaderInfoLog)(GLuint shader, GLsizei bufSize, GLsizei *length, GLchar *infoLog) = 0;
void (*glDeleteShader)(GLuint shader) = 0;
GLuint (*glCreateProgram)(void) = 0;
void (*glAttachShader)(GLuint program, GLuint shader) = 0;
void (*glLinkProgram)(GLuint program) = 0;
void (*glGetProgramiv)(GLuint program, GLenum pname, GLint *params) = 0;
void (*glGetProgramInfoLog)(GLuint program, GLsizei bufSize, GLsizei *length, GLchar *infoLog) = 0;
void (*glDeleteProgram)(GLuint program) = 0;
void (*glUseProgram)(GLuint program) = 0;
GLint (*glGetUniformLocation)(GLuint program, const GLchar *name) = 0;
void (*glUniform1f)(GLint location, GLfloat v0) = 0;
void (*glUniform1i)(GLint location, GLint v0) = 0;
void (*glUniform2f)(GLint location, GLfloat v0, GLfloat v1) = 0;
void (*glUniform4f)(GLint location, GLfloat v0, GLfloat v1, GLfloat v2, GLfloat v3) = 0;
void (*glUniformMatrix4fv)(GLint location, GLsizei count, GLboolean transpose, const GLfloat *value) = 0;
void (*glViewport)(GLint x, GLint y, GLsizei width, GLsizei height) = 0;
void (*glClear)(GLbitfield mask) = 0;
void (*glDrawElements)(GLenum mode, GLsizei count, GLenum type, const void *indices) = 0;
void (*glGenTextures)(GLsizei n, GLuint *textures) = 0;
void (*glDeleteTextures)(GLsizei n, const GLuint *textures) = 0;
void (*glBindTexture)(GLenum target, GLuint texture) = 0;
void (*glTexImage2D)(GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type, const void *pixels) = 0;
void (*glTexParameteri)(GLenum target, GLenum pname, GLint param) = 0;
void (*glTexSubImage2D)(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type, const void *pixels) = 0;
void (*glActiveTexture)(GLenum texture) = 0;
void (*glReadPixels)(GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, void *pixels) = 0;
GLenum (*glGetError)(void) = 0;

int gladLoadGLLoader(GLADloadproc proc) { return 1; }
"""

        self.github_workflow_yaml = """name: CI/CD Pipeline PCA-595
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        build_system: [cmake, bazel]
        config: [Debug, Release, ASan, TSan]

    steps:
    - uses: actions/checkout@v3

    - name: Set up CMake Build Type
      id: cmake_setup
      run: |
        if [ "${{ matrix.config }}" == "Debug" ]; then
          echo "CMAKE_BUILD_TYPE=Debug" >> $GITHUB_ENV
          echo "CMAKE_EXTRA_ARGS=" >> $GITHUB_ENV
        elif [ "${{ matrix.config }}" == "Release" ]; then
          echo "CMAKE_BUILD_TYPE=Release" >> $GITHUB_ENV
          echo "CMAKE_EXTRA_ARGS=" >> $GITHUB_ENV
        elif [ "${{ matrix.config }}" == "ASan" ]; then
          echo "CMAKE_BUILD_TYPE=Debug" >> $GITHUB_ENV
          echo "CMAKE_EXTRA_ARGS=-DARKHE_ENABLE_ASAN=ON" >> $GITHUB_ENV
        elif [ "${{ matrix.config }}" == "TSan" ]; then
          echo "CMAKE_BUILD_TYPE=Debug" >> $GITHUB_ENV
          echo "CMAKE_EXTRA_ARGS=-DARKHE_ENABLE_TSAN=ON" >> $GITHUB_ENV
        fi

    - name: Set up Bazel Config
      run: |
        echo "BAZEL_CONFIG=$(echo ${{ matrix.config }} | tr '[:upper:]' '[:lower:]')" >> $GITHUB_ENV

    - name: Build with CMake
      if: matrix.build_system == 'cmake'
      run: |
        cd pca_595
        mkdir build && cd build
        cmake .. -DCMAKE_BUILD_TYPE=${{ env.CMAKE_BUILD_TYPE }} ${{ env.CMAKE_EXTRA_ARGS }} -DARKHE_BUILD_EXAMPLES=ON
        cmake --build . --parallel $(nproc)

    - name: Build with Bazel
      if: matrix.build_system == 'bazel'
      run: |
        cd pca_595
        bazel build //src:arkhe-pca595 --config=${{ env.BAZEL_CONFIG }}
"""

        self.src_cmake = """add_library(arkhe-pca595-static STATIC)
# ... """

        self.cmake1 = """# ============================================================================
# ARKHE OS - PCA-595 v2.4 Build System
# OpenGL Live Coding Overlay & Multi-Tenant Architecture
# Arquiteto: ORCID 0009-0005-2697-4668
# Data: 2026-05-23
# Versao: 2.4 (STRICT MODE)
# ============================================================================
#
# Uso:
#   mkdir build && cd build
#   cmake .. -DARKHE_BUILD_SHARED=OFF -DARKHE_BUILD_EXAMPLES=ON
#   cmake --build . --parallel $(nproc)
#
# Opcoes:
#   ARKHE_BUILD_SHARED        - Build biblioteca dinamica (default: OFF)
#   ARKHE_BUILD_EXAMPLES      - Build exemplos (default: ON)
#   ARKHE_BUILD_TESTS         - Build testes unitarios (default: OFF)
#   ARKHE_ENABLE_ASAN         - AddressSanitizer (default: OFF)
#   ARKHE_ENABLE_TSAN         - ThreadSanitizer (default: OFF)
#   ARKHE_SYSTEM_DEPS         - Usar find_package em vez de FetchContent (default: OFF)
# ============================================================================

cmake_minimum_required(VERSION 3.20)
project(arkhe-pca-595
    VERSION 2.4.0
    DESCRIPTION "ARKHE OS PCA-595 v2.4 - Multi-Tenant Consciousness Overlay"
    HOMEPAGE_URL "https://arkhe-os.org/substrates/595"
    LANGUAGES C CXX
)

# ---------------------------------------------------------------------------
# C++ Standard
# ---------------------------------------------------------------------------
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# ---------------------------------------------------------------------------
# Opções de build
# ---------------------------------------------------------------------------
option(ARKHE_BUILD_SHARED        "Build shared library (SO/DLL)" OFF)
option(ARKHE_BUILD_EXAMPLES      "Build integration examples"    ON)
option(ARKHE_BUILD_TESTS         "Build unit tests"              OFF)
option(ARKHE_ENABLE_ASAN         "Enable AddressSanitizer"       OFF)
option(ARKHE_ENABLE_TSAN         "Enable ThreadSanitizer"        OFF)
option(ARKHE_SYSTEM_DEPS         "Use system packages via find_package" OFF)
option(ARKHE_ENABLE_LTO          "Enable Link-Time Optimization" ON)

# ---------------------------------------------------------------------------
# Sanitizers (mutualmente exclusivos)
# ---------------------------------------------------------------------------
if(ARKHE_ENABLE_ASAN AND ARKHE_ENABLE_TSAN)
    message(FATAL_ERROR "ARKHE_ENABLE_ASAN e ARKHE_ENABLE_TSAN sao mutuamente exclusivos.")
endif()

if(ARKHE_ENABLE_ASAN)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

if(ARKHE_ENABLE_TSAN)
    add_compile_options(-fsanitize=thread)
    add_link_options(-fsanitize=thread)
endif()

# ---------------------------------------------------------------------------
# LTO (Release only)
# ---------------------------------------------------------------------------
if(ARKHE_ENABLE_LTO AND CMAKE_BUILD_TYPE STREQUAL "Release")
    include(CheckIPOSupported)
    check_ipo_supported(RESULT ipo_supported OUTPUT ipo_error)
    if(ipo_supported)
        set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
        message(STATUS "LTO/IPO ativado.")
    else()
        message(WARNING "LTO nao suportado: ${ipo_error}")
    endif()
endif()

# ---------------------------------------------------------------------------
# Diretórios
# ---------------------------------------------------------------------------
set(ARKHE_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)
set(ARKHE_SRC_DIR     ${CMAKE_CURRENT_SOURCE_DIR}/src)
set(ARKHE_CMAKE_DIR   ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
set(ARKHE_THIRD_PARTY ${CMAKE_CURRENT_SOURCE_DIR}/third_party)

list(APPEND CMAKE_MODULE_PATH ${ARKHE_CMAKE_DIR})

# ---------------------------------------------------------------------------
# Dependências - FetchContent (hermetic) ou find_package (system)
# ---------------------------------------------------------------------------
include(FetchContent)

if(NOT ARKHE_SYSTEM_DEPS)
    # --- GLM (header-only) ---
    FetchContent_Declare(
        glm
        GIT_REPOSITORY https://github.com/g-truc/glm.git
        GIT_TAG        1.0.1
        GIT_SHALLOW    TRUE
    )

    # --- nlohmann/json (header-only) ---
    FetchContent_Declare(
        nlohmann_json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG        v3.11.3
        GIT_SHALLOW    TRUE
    )

    # --- GLFW ---
    FetchContent_Declare(
        glfw
        GIT_REPOSITORY https://github.com/glfw/glfw.git
        GIT_TAG        3.4
        GIT_SHALLOW    TRUE
    )
    set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
    set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(GLFW_INSTALL OFF CACHE BOOL "" FORCE)

    # --- GLAD (gerado para OpenGL 3.3 Core) ---
    # Assumimos glad como submodulo em third_party/glad/
    # Se nao existir, o build falara com mensagem clara.
    if(NOT EXISTS ${ARKHE_THIRD_PARTY}/glad/include/glad/glad.h)
        message(FATAL_ERROR
            "GLAD nao encontrado em third_party/glad/.
"
            "Gere via https://glad.dav1d.de/ (OpenGL 3.3 Core, profile core)
"
            "ou clone: git clone https://github.com/Dav1dde/glad ${ARKHE_THIRD_PARTY}/glad"
        )
    endif()

    # --- FreeType2 ---
    FetchContent_Declare(
        freetype
        GIT_REPOSITORY https://gitlab.freedesktop.org/freetype/freetype.git
        GIT_TAG        VER-2-13-2
        GIT_SHALLOW    TRUE
    )
    set(FT_DISABLE_HARFBUZZ ON CACHE BOOL "" FORCE)
    set(FT_DISABLE_BROTLI ON CACHE BOOL "" FORCE)
    set(FT_DISABLE_BZIP2 ON CACHE BOOL "" FORCE)
    set(FT_DISABLE_PNG ON CACHE BOOL "" FORCE)
    set(FT_DISABLE_ZLIB ON CACHE BOOL "" FORCE)

    # Make available
    FetchContent_MakeAvailable(glm nlohmann_json glfw freetype)
else()
    find_package(glm REQUIRED)
    find_package(nlohmann_json 3.11 REQUIRED)
    find_package(glfw3 3.3 REQUIRED)
    find_package(Freetype REQUIRED)
    # GLAD - assume system ou third_party
    if(NOT EXISTS ${ARKHE_THIRD_PARTY}/glad/include/glad/glad.h)
        message(FATAL_ERROR "GLAD nao encontrado em third_party/glad/")
    endif()
endif()

# ---------------------------------------------------------------------------
# Threads
# ---------------------------------------------------------------------------
find_package(Threads REQUIRED)

# ---------------------------------------------------------------------------
# UUID (Linux/Unix)
# ---------------------------------------------------------------------------
if(UNIX AND NOT APPLE)
    find_package(PkgConfig)
    if(PkgConfig_FOUND)
        pkg_check_modules(UUID uuid)
    endif()
    if(NOT UUID_FOUND)
        # Fallback: buscar libuuid diretamente
        find_library(UUID_LIBRARY uuid
            PATHS /usr/lib /usr/local/lib /lib
        )
        find_path(UUID_INCLUDE_DIR uuid/uuid.h
            PATHS /usr/include /usr/local/include
        )
        if(UUID_LIBRARY AND UUID_INCLUDE_DIR)
            set(UUID_FOUND TRUE)
            set(UUID_LIBRARIES ${UUID_LIBRARY})
            set(UUID_INCLUDE_DIRS ${UUID_INCLUDE_DIR})
            message(STATUS "libuuid encontrado manualmente: ${UUID_LIBRARY}")
        else()
            message(FATAL_ERROR "libuuid nao encontrada. Instale: apt install uuid-dev / yum install libuuid-devel")
        endif()
    endif()
elseif(APPLE)
    # macOS: UUID esta em CoreFoundation, mas uuid.h pode estar em system
    find_library(UUID_LIBRARY System)
    set(UUID_FOUND TRUE)
    set(UUID_LIBRARIES "")
    set(UUID_INCLUDE_DIRS "")
endif()

# ---------------------------------------------------------------------------
# OpenGL
# ---------------------------------------------------------------------------
find_package(OpenGL REQUIRED)

# ---------------------------------------------------------------------------
# Subdiretórios
# ---------------------------------------------------------------------------
add_subdirectory(src)

if(ARKHE_BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

if(ARKHE_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# ---------------------------------------------------------------------------
# Install rules (para packaging)
# ---------------------------------------------------------------------------
include(GNUInstallDirs)

install(DIRECTORY ${ARKHE_INCLUDE_DIR}/arkhe
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    FILES_MATCHING PATTERN "*.h" PATTERN "*.hpp"
)

# pkg-config
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/arkhe-pca-595.pc.in
    ${CMAKE_CURRENT_BINARY_DIR}/arkhe-pca-595.pc
    @ONLY
)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/arkhe-pca-595.pc
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig
)

# ============================================================================
# ARKHE PCA-595 - Library Targets
# ============================================================================

set(ARKHE_PCA595_HEADERS
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/PCA-595.h
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/TenantManager.h
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/PhiRendererGL.h
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/OpenGLOverlay.h
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/MultiTenant.h
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/AlignmentClient.h
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/PhiMeterIIT.h
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/ConsciousnessCycleAsync.h
    ${ARKHE_INCLUDE_DIR}/arkhe/iris/pca/IrisDriverAdapter.h
)

set(ARKHE_PCA595_SOURCES
    ${ARKHE_SRC_DIR}/TenantManager.cpp
    ${ARKHE_SRC_DIR}/PhiRendererGL.cpp
    ${ARKHE_SRC_DIR}/OpenGLOverlay.cpp
    ${ARKHE_SRC_DIR}/MultiTenant.cpp
)

# GLAD source (gerado para OpenGL 3.3 Core)
set(GLAD_SOURCES ${ARKHE_THIRD_PARTY}/glad/src/glad.c)

# ---------------------------------------------------------------------------
# Object library - compila uma unica vez
# ---------------------------------------------------------------------------
add_library(arkhe_pca595_obj OBJECT
    ${ARKHE_PCA595_SOURCES}
    ${GLAD_SOURCES}
)

target_include_directories(arkhe_pca595_obj
    PUBLIC
        $<BUILD_INTERFACE:${ARKHE_INCLUDE_DIR}>
        $<BUILD_INTERFACE:${ARKHE_THIRD_PARTY}/glad/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${UUID_INCLUDE_DIRS}
)

target_compile_definitions(arkhe_pca595_obj
    PRIVATE
        GLAD_GLAPI_EXPORT
        GLM_ENABLE_EXPERIMENTAL
)

# Warnings rigorosos (STRICT MODE)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(arkhe_pca595_obj PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -Wshadow
        -Wnon-virtual-dtor
        -Wold-style-cast
        -Wcast-align
        -Wunused
        -Woverloaded-virtual
        -Wconversion
        -Wsign-conversion
        -Wnull-dereference
        -Wdouble-promotion
        -Wformat=2
        -Wimplicit-fallthrough
        -Wmisleading-indentation
        -Wduplicated-cond
        -Wduplicated-branches
        -Wlogical-op
        -Wuseless-cast
        $<$<CONFIG:Debug>:-O0 -g3 -fno-omit-frame-pointer>
        $<$<CONFIG:Release>:-O3 -march=native -DNDEBUG>
    )
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    target_compile_options(arkhe_pca595_obj PRIVATE
        /W4
        /permissive-
        /Zc:__cplusplus
        /Zc:preprocessor
        /wd4251  # DLL interface warning para STL
        $<$<CONFIG:Debug>:/Od /Zi>
        $<$<CONFIG:Release>:/O2 /Ob2 /GL>
    )
endif()

# Position Independent Code (necessario para shared libs)
set_target_properties(arkhe_pca595_obj PROPERTIES
    POSITION_INDEPENDENT_CODE ON
)

# ---------------------------------------------------------------------------
# Link dependencies (INTERFACE para object library)
# ---------------------------------------------------------------------------
target_link_libraries(arkhe_pca595_obj
    PUBLIC
        Threads::Threads
        OpenGL::GL
        glfw
        freetype
        glm::glm
        nlohmann_json::nlohmann_json
    PRIVATE
        ${UUID_LIBRARIES}
)

# ---------------------------------------------------------------------------
# Static library
# ---------------------------------------------------------------------------
add_library(arkhe-pca595-static STATIC)
add_library(Arkhe::PCA595 ALIAS arkhe-pca595-static)

target_sources(arkhe-pca595-static PRIVATE $<TARGET_OBJECTS:arkhe_pca595_obj>)

target_include_directories(arkhe-pca595-static
    PUBLIC
        $<BUILD_INTERFACE:${ARKHE_INCLUDE_DIR}>
        $<BUILD_INTERFACE:${ARKHE_THIRD_PARTY}/glad/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(arkhe-pca595-static
    PUBLIC
        Threads::Threads
        OpenGL::GL
        glfw
        freetype
        glm::glm
        nlohmann_json::nlohmann_json
    PRIVATE
        ${UUID_LIBRARIES}
)

set_target_properties(arkhe-pca595-static PROPERTIES
    OUTPUT_NAME arkhe-pca595
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    EXPORT_NAME PCA595
)

# ---------------------------------------------------------------------------
# Shared library (opcional)
# ---------------------------------------------------------------------------
if(ARKHE_BUILD_SHARED)
    add_library(arkhe-pca595-shared SHARED)
    add_library(Arkhe::PCA595Shared ALIAS arkhe-pca595-shared)

    target_sources(arkhe-pca595-shared PRIVATE $<TARGET_OBJECTS:arkhe_pca595_obj>)

    target_include_directories(arkhe-pca595-shared
        PUBLIC
            $<BUILD_INTERFACE:${ARKHE_INCLUDE_DIR}>
            $<BUILD_INTERFACE:${ARKHE_THIRD_PARTY}/glad/include>
            $<INSTALL_INTERFACE:include>
    )

    target_link_libraries(arkhe-pca595-shared
        PUBLIC
            Threads::Threads
            OpenGL::GL
            glfw
            freetype
            glm::glm
            nlohmann_json::nlohmann_json
        PRIVATE
            ${UUID_LIBRARIES}
    )

    target_compile_definitions(arkhe-pca595-shared
        PRIVATE ARKHE_PCA595_BUILD_DLL
        INTERFACE ARKHE_PCA595_USE_DLL
    )

    set_target_properties(arkhe-pca595-shared PROPERTIES
        OUTPUT_NAME arkhe-pca595
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
        ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
        VERSION ${PROJECT_VERSION}
        SOVERSION ${PROJECT_VERSION_MAJOR}
        EXPORT_NAME PCA595Shared
    )

    # Symbol visibility (GCC/Clang)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(arkhe-pca595-shared PRIVATE -fvisibility=hidden)
    endif()
endif()

# ---------------------------------------------------------------------------
# Export targets
# ---------------------------------------------------------------------------
install(TARGETS arkhe-pca595-static
    EXPORT ArkhePCA595Targets
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

if(ARKHE_BUILD_SHARED)
    install(TARGETS arkhe-pca595-shared
        EXPORT ArkhePCA595Targets
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    )
endif()

install(EXPORT ArkhePCA595Targets
    FILE ArkhePCA595Targets.cmake
    NAMESPACE Arkhe::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ArkhePCA595
)

# Config file
include(CMakePackageConfigHelpers)
configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/ArkhePCA595Config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/ArkhePCA595Config.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ArkhePCA595
)
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/ArkhePCA595ConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)
install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/ArkhePCA595Config.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/ArkhePCA595ConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ArkhePCA595
)
"""
        self.build_bazel_root = """# ARKHE PCA-595 - Root BUILD file
# Exporta headers publicos para outros modulos Bazel

package(default_visibility = ["//visibility:public"])

exports_files([
    "MODULE.bazel",
    "extensions.bzl",
    "LICENSE",
])

# Alias para a biblioteca principal
alias(
    name = "arkhe-pca595",
    actual = "//src:arkhe-pca595",
)
"""
        self.module_bazel = '''"""ARKHE OS PCA-595 v2.4 - Bazel Module

OpenGL Live Coding Overlay & Multi-Tenant Architecture
Arquiteto: ORCID 0009-0005-2697-4668
"""

module(
    name = "arkhe-pca595",
    version = "2.4.0",
    compatibility_level = 1,
)

# Core Bazel rules
bazel_dep(name = "rules_cc", version = "0.0.9")
bazel_dep(name = "platforms", version = "0.0.10")

# --- Dependencias externas (via http_archive em extensions.bzl) ---
# GLM, nlohmann_json, GLFW, FreeType2, GLAD

non_module_deps = use_extension("//:extensions.bzl", "non_module_deps")
use_repo(non_module_deps, "glm", "nlohmann_json", "glfw", "freetype2", "glad")
'''
        self.extensions_bzl = '''load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def _non_module_deps_impl(_ctx):
    # GLM (header-only)
    http_archive(
        name = "glm",
        url = "https://github.com/g-truc/glm/archive/refs/tags/1.0.1.tar.gz",
        strip_prefix = "glm-1.0.1",
        sha256 = "9f3174561fd3e0f6abcaf3d5c2f16ba5e8c66f8c6f3f3e3e3e3e3e3e3e3e3e3e3",  # Substituir por hash real
        build_file_content = """
load("@rules_cc//cc:defs.bzl", "cc_library")
cc_library(
    name = "glm",
    hdrs = glob(["glm/**/*.hpp", "glm/**/*.h"]),
    includes = ["."],
    visibility = ["//visibility:public"],
)
""",
    )

    # nlohmann/json (header-only)
    http_archive(
        name = "nlohmann_json",
        url = "https://github.com/nlohmann/json/archive/refs/tags/v3.11.3.tar.gz",
        strip_prefix = "json-3.11.3",
        sha256 = "0d8ef5af7f9794e3263481fbddc3f5a5f3b5d5e5e5e5e5e5e5e5e5e5e5e5e5e5e",  # Substituir
        build_file_content = """
load("@rules_cc//cc:defs.bzl", "cc_library")
cc_library(
    name = "json",
    hdrs = ["single_include/nlohmann/json.hpp"],
    includes = ["single_include"],
    visibility = ["//visibility:public"],
)
""",
    )

    # GLFW
    http_archive(
        name = "glfw",
        url = "https://github.com/glfw/glfw/archive/refs/tags/3.4.tar.gz",
        strip_prefix = "glfw-3.4",
        sha256 = "c5e9e8f3b5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e",  # Substituir
        build_file = "@arkhe-pca595//:third_party/glfw.BUILD",
    )

    # FreeType2
    http_archive(
        name = "freetype2",
        url = "https://gitlab.freedesktop.org/freetype/freetype/-/archive/VER-2-13-2/freetype-VER-2-13-2.tar.gz",
        strip_prefix = "freetype-VER-2-13-2",
        sha256 = "e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e",  # Substituir
        build_file = "@arkhe-pca595//:third_party/freetype2.BUILD",
    )

    # GLAD - assume gerado localmente em third_party/glad/
    native.local_repository(
        name = "glad",
        path = "third_party/glad",
    )

non_module_deps = module_extension(
    implementation = _non_module_deps_impl,
)
'''
        self.src_build_bazel = """load("@rules_cc//cc:defs.bzl", "cc_library", "cc_binary")

package(default_visibility = ["//visibility:public"])

# ---------------------------------------------------------------------------
# GLAD - OpenGL loader (gerado para OpenGL 3.3 Core)
# ---------------------------------------------------------------------------
cc_library(
    name = "glad",
    srcs = ["@glad//:src/glad.c"],
    hdrs = ["@glad//:include/glad/glad.h"],
    includes = ["@glad//:include"],
    linkopts = select({
        "@platforms//os:linux": ["-ldl"],
        "//conditions:default": [],
    }),
)

# ---------------------------------------------------------------------------
# ARKHE PCA-595 - Core Library
# ---------------------------------------------------------------------------
ARKHE_PCA595_HDRS = [
    "//include/arkhe/iris/pca:PCA-595.h",
    "//include/arkhe/iris/pca:TenantManager.h",
    "//include/arkhe/iris/pca:PhiRendererGL.h",
    "//include/arkhe/iris/pca:OpenGLOverlay.h",
    "//include/arkhe/iris/pca:MultiTenant.h",
    "//include/arkhe/iris/pca:AlignmentClient.h",
    "//include/arkhe/iris/pca:PhiMeterIIT.h",
    "//include/arkhe/iris/pca:ConsciousnessCycleAsync.h",
    "//include/arkhe/iris/pca:IrisDriverAdapter.h",
]

ARKHE_PCA595_SRCS = [
    "TenantManager.cpp",
    "PhiRendererGL.cpp",
    "OpenGLOverlay.cpp",
    "MultiTenant.cpp",
]

cc_library(
    name = "arkhe-pca595",
    srcs = ARKHE_PCA595_SRCS,
    hdrs = ARKHE_PCA595_HDRS,
    includes = ["../include"],
    copts = select({
        "@platforms//os:linux": [
            "-std=c++20",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Wshadow",
            "-Wnon-virtual-dtor",
            "-Wold-style-cast",
            "-Wcast-align",
            "-Wunused",
            "-Woverloaded-virtual",
            "-Wconversion",
            "-Wsign-conversion",
            "-Wnull-dereference",
            "-Wdouble-promotion",
            "-Wformat=2",
            "-Wimplicit-fallthrough",
            "-O3",
            "-DNDEBUG",
            "-DGLM_ENABLE_EXPERIMENTAL",
        ],
        "@platforms//os:macos": [
            "-std=c++20",
            "-Wall",
            "-Wextra",
            "-O3",
            "-DNDEBUG",
            "-DGLM_ENABLE_EXPERIMENTAL",
        ],
        "@platforms//os:windows": [
            "/std:c++20",
            "/W4",
            "/permissive-",
            "/Zc:__cplusplus",
            "/O2",
            "/DNDEBUG",
            "/DGLM_ENABLE_EXPERIMENTAL",
        ],
        "//conditions:default": ["-std=c++20"],
    }),
    linkopts = select({
        "@platforms//os:linux": [
            "-pthread",
            "-luuid",
        ],
        "@platforms//os:macos": [
            "-pthread",
            "-framework CoreFoundation",
        ],
        "//conditions:default": [],
    }),
    deps = [
        ":glad",
        "@glm//:glm",
        "@nlohmann_json//:json",
        "@glfw//:glfw",
        "@freetype2//:freetype",
    ],
    linkstatic = True,
)

# ---------------------------------------------------------------------------
# Exemplo: Live-Coder Integration
# ---------------------------------------------------------------------------
cc_binary(
    name = "live_coder_integration",
    srcs = ["//examples:live_coder_integration.cpp"],
    deps = [":arkhe-pca595"],
)
"""
        self.bazelrc = """# ARKHE PCA-595 - Bazel Configuration
# Arquiteto: ORCID 0009-0005-2697-4668

# Build
build --cxxopt=-std=c++20
build --copt=-O3
build --copt=-DNDEBUG
build --copt=-DGLM_ENABLE_EXPERIMENTAL

# Strict warnings
build --copt=-Wall
build --copt=-Wextra
build --copt=-Wpedantic

# Threads
build --jobs=auto

# Hermeticidade
build --incompatible_strict_action_env

# Test
build --test_output=errors
build --test_verbose_timeout_warnings

# Release
build:release --copt=-march=native
build:release --copt=-ffast-math
build:release --linkopt=-Wl,--strip-all

# Debug
build:debug --copt=-O0
build:debug --copt=-g3
build:debug --copt=-fno-omit-frame-pointer
build:debug --strip=never

# AddressSanitizer
build:asan --copt=-fsanitize=address
build:asan --copt=-fno-omit-frame-pointer
build:asan --linkopt=-fsanitize=address
build:asan --copt=-O1
build:asan --copt=-g

# ThreadSanitizer
build:tsan --copt=-fsanitize=thread
build:tsan --linkopt=-fsanitize=thread
build:tsan --copt=-O1
build:tsan --copt=-g

# LTO
build:lto --copt=-flto
build:lto --linkopt=-flto
"""
        self.arkhe_pca595_config_cmake_in = """@PACKAGE_INIT@

include(CMakeFindDependencyMacro)

find_dependency(Threads)
find_dependency(OpenGL)
find_dependency(glfw3)
find_dependency(Freetype)
find_dependency(glm)
find_dependency(nlohmann_json)

include("${CMAKE_CURRENT_LIST_DIR}/ArkhePCA595Targets.cmake")

check_required_components(ArkhePCA595)
"""
        self.find_glad_cmake = """# FindGLAD.cmake - Fallback para sistemas sem gladConfig.cmake
# GLAD e tipicamente header-only ou com um unico arquivo fonte (glad.c).

find_path(GLAD_INCLUDE_DIR glad/glad.h
    PATHS
        ${ARKHE_THIRD_PARTY}/glad/include
        /usr/include
        /usr/local/include
)

find_library(GLAD_LIBRARY
    NAMES glad
    PATHS
        ${ARKHE_THIRD_PARTY}/glad/lib
        /usr/lib
        /usr/local/lib
)

if(NOT GLAD_LIBRARY)
    # GLAD e frequentemente compilado como objeto - nao ha biblioteca separada
    set(GLAD_LIBRARY "")
    set(GLAD_FOUND TRUE)
else()
    set(GLAD_FOUND TRUE)
endif()

if(GLAD_FOUND)
    if(NOT TARGET GLAD::GLAD)
        add_library(GLAD::GLAD INTERFACE IMPORTED)
        set_target_properties(GLAD::GLAD PROPERTIES
            INTERFACE_INCLUDE_DIRECTORIES "${GLAD_INCLUDE_DIR}"
        )
        if(GLAD_LIBRARY)
            set_target_properties(GLAD::GLAD PROPERTIES
                INTERFACE_LINK_LIBRARIES "${GLAD_LIBRARY}"
            )
        endif()
    endif()
endif()

mark_as_advanced(GLAD_INCLUDE_DIR GLAD_LIBRARY)
"""
        self.arkhe_pca_595_pc_in = """prefix=@CMAKE_INSTALL_PREFIX@
exec_prefix=${prefix}
libdir=${prefix}/@CMAKE_INSTALL_LIBDIR@
includedir=${prefix}/@CMAKE_INSTALL_INCLUDEDIR@

Name: arkhe-pca-595
Description: ARKHE OS PCA-595 v2.4 - Multi-Tenant Consciousness Overlay
Version: @PROJECT_VERSION@
Requires: glfw3, freetype2, nlohmann_json
Libs: -L${libdir} -larkhe-pca595 -lpthread -luuid
Cflags: -I${includedir} -std=c++20
"""
        self.glad_build_bazel = """load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "glad",
    srcs = ["src/glad.c"],
    hdrs = ["include/glad/glad.h"],
    includes = ["include"],
    linkopts = select({
        "@platforms//os:linux": ["-ldl"],
        "//conditions:default": [],
    }),
)
"""
        self.glfw_build = """load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "glfw",
    srcs = glob([
        "src/*.c",
        "src/*.h",
        "include/GLFW/*.h",
    ]) + select({
        "@platforms//os:linux": glob(["src/x11_*.c", "src/linux_*.c", "src/posix_*.c", "src/glx_*.c", "src/egl_*.c", "src/osmesa_*.c", "src/xkb_*.c"]),
        "@platforms//os:macos": glob(["src/cocoa_*.c", "src/posix_*.c", "src/nsgl_*.c", "src/egl_*.c", "src/osmesa_*.c"]),
        "@platforms//os:windows": glob(["src/win32_*.c", "src/wgl_*.c", "src/egl_*.c", "src/osmesa_*.c"]),
        "//conditions:default": [],
    }),
    hdrs = glob(["include/GLFW/*.h", "src/*.h"]),
    includes = ["include"],
    copts = select({
        "@platforms//os:linux": ["-D_GLFW_X11", "-D_GLFW_HAS_XF86VM", "-D_GLFW_EGL"],
        "@platforms//os:macos": ["-D_GLFW_COCOA", "-D_GLFW_NSGL"],
        "@platforms//os:windows": ["/D_GLFW_WIN32", "/D_GLFW_WGL"],
        "//conditions:default": [],
    }),
    linkopts = select({
        "@platforms//os:linux": ["-lX11", "-lXrandr", "-lXinerama", "-lXcursor", "-lXi", "-ldl", "-lpthread", "-lm"],
        "@platforms//os:macos": ["-framework Cocoa", "-framework IOKit", "-framework CoreFoundation", "-framework CoreVideo"],
        "//conditions:default": [],
    }),
    deps = select({
        "@platforms//os:linux": [],
        "//conditions:default": [],
    }),
)
"""
        self.freetype2_build = """load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "freetype",
    srcs = glob([
        "src/**/*.c",
        "src/**/*.h",
    ]) + [
        "include/freetype/config/ftconfig.h",
        "include/freetype/config/ftoption.h",
        "include/freetype/config/ftstdlib.h",
    ],
    hdrs = glob(["include/**/*.h"]),
    includes = ["include"],
    copts = [
        "-DFT2_BUILD_LIBRARY",
        "-DFT_CONFIG_OPTION_SYSTEM_ZLIB",
        "-DFT_CONFIG_OPTION_USE_BZIP2",
        "-DFT_CONFIG_OPTION_USE_PNG",
        "-DFT_CONFIG_OPTION_USE_HARFBUZZ",
        "-DFT_CONFIG_OPTION_USE_BROTLI",
    ],
    linkopts = select({
        "@platforms//os:linux": ["-lz", "-lm"],
        "//conditions:default": [],
    }),
)
"""
        self.examples_cmake = """# ============================================================================
# ARKHE PCA-595 - Integration Examples
# ============================================================================

add_executable(live_coder_integration live_coder_integration.cpp)

target_link_libraries(live_coder_integration PRIVATE Arkhe::PCA595)

set_target_properties(live_coder_integration PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
)

# Copiar shaders/fontes para o diretorio de build (se necessario)
# add_custom_command(TARGET live_coder_integration POST_BUILD
#     COMMAND ${CMAKE_COMMAND} -E copy_directory
#     ${CMAKE_CURRENT_SOURCE_DIR}/assets $<TARGET_FILE_DIR:live_coder_integration>/assets
# )
"""


        self.tenant_manager_cpp = r"""// ============================================================================
// TenantManager.cpp
// Implementação multi-tenant para PCA-595
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-23
// Versão: 2.4 (STRICT MODE)
// ============================================================================

#include "TenantManager.h"
#include <sstream>
#include <iomanip>

namespace Arkhe {
namespace Iris {
namespace PCA {

// ============================================================================
// Singleton
// ============================================================================

TenantManager& TenantManager::Instance() {
    static TenantManager instance;
    return instance;
}

TenantManager::TenantManager() {
    // Inicializar recursos compartilhados
    sharedPhiMeter_ = std::make_shared<PhiMeter>(ATTENTION_HEADS, EMBEDDING_DIM);

    Alignment::AlignmentConfig alignmentConfig;
    sharedAlignmentClient_ = std::make_shared<Alignment::AlignmentClient>(alignmentConfig);

    IITConfig iitConfig;
    sharedIITMeter_ = std::make_shared<PhiMeterIIT>(iitConfig);
}

TenantManager::~TenantManager() {
    tenants_.clear();
}

// ============================================================================
// CRUD de tenants
// ============================================================================

std::string TenantManager::CreateTenant(const TenantConfig& config) {
    if (!ValidateConfig(config)) {
        throw std::invalid_argument("Invalid tenant configuration");
    }

    std::string tenantId = config.tenantId.empty() ? GenerateTenantId() : config.tenantId;

    std::lock_guard<std::mutex> lock(tenantsMutex_);

    if (tenants_.find(tenantId) != tenants_.end()) {
        throw std::runtime_error("Tenant already exists: " + tenantId);
    }

    TenantState state{};
    state.tenantId = tenantId;
    state.createdAt = std::chrono::steady_clock::now();
    state.lastActivity = state.createdAt;

    InitializeTenantResources(state, config);

    tenants_[tenantId] = std::move(state);
    configs_[tenantId] = config;

    globalStats_.totalTenants++;

    std::cout << "[TenantManager] Created tenant: " << tenantId
              << " (" << config.name << ")" << std::endl;

    return tenantId;
}

bool TenantManager::DeleteTenant(const std::string& tenantId) {
    std::lock_guard<std::mutex> lock(tenantsMutex_);

    auto it = tenants_.find(tenantId);
    if (it == tenants_.end()) {
        return false;
    }

    // Liberar recursos dedicados
    it->second.phiMeter.reset();
    it->second.alignmentClient.reset();
    it->second.iitMeter.reset();
    it->second.cycle.reset();

    tenants_.erase(it);
    configs_.erase(tenantId);

    globalStats_.totalTenants--;

    std::cout << "[TenantManager] Deleted tenant: " << tenantId << std::endl;

    return true;
}

bool TenantManager::UpdateTenant(const std::string& tenantId, const TenantConfig& config) {
    std::lock_guard<std::mutex> lock(tenantsMutex_);

    auto it = tenants_.find(tenantId);
    if (it == tenants_.end()) {
        return false;
    }

    configs_[tenantId] = config;

    // Re-inicializar recursos se necessário
    if (config.dedicatedPhiMeter && !it->second.phiMeter) {
        it->second.phiMeter = std::make_unique<PhiMeter>(ATTENTION_HEADS, EMBEDDING_DIM);
    } else if (!config.dedicatedPhiMeter && it->second.phiMeter) {
        it->second.phiMeter.reset();
    }

    if (config.dedicatedAlignment && !it->second.alignmentClient) {
        Alignment::AlignmentConfig ac;
        it->second.alignmentClient = std::make_unique<Alignment::AlignmentClient>(ac);
    } else if (!config.dedicatedAlignment && it->second.alignmentClient) {
        it->second.alignmentClient.reset();
    }

    if (config.dedicatedIIT && !it->second.iitMeter) {
        IITConfig ic;
        it->second.iitMeter = std::make_unique<PhiMeterIIT>(ic);
    } else if (!config.dedicatedIIT && it->second.iitMeter) {
        it->second.iitMeter.reset();
    }

    return true;
}

// ============================================================================
// Acesso
// ============================================================================

TenantState* TenantManager::GetTenant(const std::string& tenantId) {
    std::lock_guard<std::mutex> lock(tenantsMutex_);

    auto it = tenants_.find(tenantId);
    if (it != tenants_.end()) {
        it->second.lastActivity = std::chrono::steady_clock::now();
        return &it->second;
    }

    return nullptr;
}

TenantConfig TenantManager::GetTenantConfig(const std::string& tenantId) const {
    std::lock_guard<std::mutex> lock(tenantsMutex_);

    auto it = configs_.find(tenantId);
    if (it != configs_.end()) {
        return it->second;
    }

    return TenantConfig{};
}

// ============================================================================
// Ciclo de consciência por tenant
// ============================================================================

IrisResponse TenantManager::RunCycleI2T(const std::string& tenantId, const I2TRequest& req) {
    auto* tenant = GetTenant(tenantId);
    if (!tenant) {
        IrisResponse err{ResponseStatus::ERROR_NETWORK, 0,
            "Tenant not found: " + tenantId, "", {}, {}, 0.0f, 0, ""};
        return err;
    }

    // Check quotas
    if (!CheckQuota(tenantId, "requests_per_minute")) {
        IrisResponse err{ResponseStatus::ERROR_NETWORK, req.sequenceId,
            "Rate limit exceeded", "", {}, {}, 0.0f, 0, ""};
        return err;
    }

    if (!CheckQuota(tenantId, "concurrent_cycles")) {
        IrisResponse err{ResponseStatus::ERROR_NETWORK, req.sequenceId,
            "Max concurrent cycles exceeded", "", {}, {}, 0.0f, 0, ""};
        return err;
    }

    // Run cycle
    tenant->activeCycles++;
    tenant->requestCount++;

    IrisResponse resp;
    if (tenant->cycle) {
        resp = tenant->cycle->RunCycleI2T(req);
    } else {
        // Use shared cycle
        ConsciousnessCycle cycle(nullptr, sharedPhiMeter_.get(), nullptr);
        resp = cycle.RunCycleI2T(req);
    }

    tenant->activeCycles--;
    tenant->orCount++;
    tenant->phiBudgetUsed += resp.confidence; // Proxy para Φ usado

    if (resp.status == ResponseStatus::ERROR_ALIGNMENT) {
        tenant->blockedCount++;
    }

    // Record usage
    RecordUsage(tenantId, "requests", 1.0);
    RecordUsage(tenantId, "phi", resp.confidence);

    return resp;
}

IrisResponse TenantManager::RunCycleT2T(const std::string& tenantId, const T2TRequest& req) {
    auto* tenant = GetTenant(tenantId);
    if (!tenant) {
        IrisResponse err{ResponseStatus::ERROR_NETWORK, 0,
            "Tenant not found: " + tenantId, "", {}, {}, 0.0f, 0, ""};
        return err;
    }

    if (!CheckQuota(tenantId, "requests_per_minute")) {
        IrisResponse err{ResponseStatus::ERROR_NETWORK, req.sequenceId,
            "Rate limit exceeded", "", {}, {}, 0.0f, 0, ""};
        return err;
    }

    tenant->activeCycles++;
    tenant->requestCount++;

    IrisResponse resp;
    if (tenant->cycle) {
        resp = tenant->cycle->RunCycleT2T(req);
    } else {
        ConsciousnessCycle cycle(nullptr, sharedPhiMeter_.get(), nullptr);
        resp = cycle.RunCycleT2T(req);
    }

    tenant->activeCycles--;
    tenant->orCount++;

    RecordUsage(tenantId, "requests", 1.0);
    RecordUsage(tenantId, "phi", resp.confidence);

    return resp;
}

AsyncTask<IrisResponse> TenantManager::RunCycleI2TAsync(const std::string& tenantId, const I2TRequest& req) {
    return std::async(std::launch::async, [this, tenantId, req]() {
        return this->RunCycleI2T(tenantId, req);
    });
}

AsyncTask<IrisResponse> TenantManager::RunCycleT2TAsync(const std::string& tenantId, const T2TRequest& req) {
    return std::async(std::launch::async, [this, tenantId, req]() {
        return this->RunCycleT2T(tenantId, req);
    });
}

// ============================================================================
// Quotas e rate limiting
// ============================================================================

bool TenantManager::CheckQuota(const std::string& tenantId, const std::string& resource) {
    std::lock_guard<std::mutex> lock(tenantsMutex_);

    auto it = tenants_.find(tenantId);
    if (it == tenants_.end()) return false;

    auto configIt = configs_.find(tenantId);
    if (configIt == configs_.end()) return false;

    const auto& config = configIt->second;
    const auto& state = it->second;

    if (resource == "requests_per_minute") {
        // Simplificado — em produção, usar janela deslizante
        return state.requestCount.load() < config.quotas.maxRequestsPerMinute;
    }

    if (resource == "concurrent_cycles") {
        return state.activeCycles.load() < config.quotas.maxConcurrentCycles;
    }

    if (resource == "phi_budget") {
        return state.phiBudgetUsed.load() < config.quotas.maxPhiBudget;
    }

    return true;
}

void TenantManager::RecordUsage(const std::string& tenantId, const std::string& resource, double amount) {
    std::lock_guard<std::mutex> lock(tenantsMutex_);

    auto it = tenants_.find(tenantId);
    if (it == tenants_.end()) return;

    if (resource == "requests") {
        globalStats_.totalRequests += static_cast<uint64_t>(amount);
    } else if (resource == "phi") {
        globalStats_.totalORs++;
    }
}

// ============================================================================
// Isolation
// ============================================================================

bool TenantManager::IsIsolated(const std::string& tenantId) const {
    auto config = GetTenantConfig(tenantId);
    return config.dedicatedPhiMeter || config.dedicatedAlignment || config.dedicatedIIT;
}

void TenantManager::SetIsolationLevel(const std::string& tenantId, bool phi, bool alignment, bool iit) {
    std::lock_guard<std::mutex> lock(tenantsMutex_);

    auto configIt = configs_.find(tenantId);
    if (configIt == configs_.end()) return;

    configIt->second.dedicatedPhiMeter = phi;
    configIt->second.dedicatedAlignment = alignment;
    configIt->second.dedicatedIIT = iit;

    auto stateIt = tenants_.find(tenantId);
    if (stateIt == tenants_.end()) return;

    // Re-inicializar recursos
    if (phi && !stateIt->second.phiMeter) {
        stateIt->second.phiMeter = std::make_unique<PhiMeter>(ATTENTION_HEADS, EMBEDDING_DIM);
    } else if (!phi && stateIt->second.phiMeter) {
        stateIt->second.phiMeter.reset();
    }

    if (alignment && !stateIt->second.alignmentClient) {
        Alignment::AlignmentConfig ac;
        stateIt->second.alignmentClient = std::make_unique<Alignment::AlignmentClient>(ac);
    } else if (!alignment && stateIt->second.alignmentClient) {
        stateIt->second.alignmentClient.reset();
    }

    if (iit && !stateIt->second.iitMeter) {
        IITConfig ic;
        stateIt->second.iitMeter = std::make_unique<PhiMeterIIT>(ic);
    } else if (!iit && stateIt->second.iitMeter) {
        stateIt->second.iitMeter.reset();
    }
}

// ============================================================================
// Stats
// ============================================================================

TenantManager::GlobalStats TenantManager::GetGlobalStats() const {
    std::lock_guard<std::mutex> lock(statsMutex_);
    return globalStats_;
}

void TenantManager::CleanupInactiveTenants(uint32_t inactiveMinutes) {
    std::lock_guard<std::mutex> lock(tenantsMutex_);

    auto now = std::chrono::steady_clock::now();
    auto threshold = std::chrono::minutes(inactiveMinutes);

    std::vector<std::string> toDelete;
    for (const auto& [id, state] : tenants_) {
        auto inactive = now - state.lastActivity;
        if (inactive > threshold) {
            toDelete.push_back(id);
        }
    }

    for (const auto& id : toDelete) {
        auto it = tenants_.find(id);
        if (it != tenants_.end()) {
            it->second.phiMeter.reset();
            it->second.alignmentClient.reset();
            it->second.iitMeter.reset();
            it->second.cycle.reset();
            tenants_.erase(it);
            configs_.erase(id);
            globalStats_.totalTenants--;
        }
    }

    if (!toDelete.empty()) {
        std::cout << "[TenantManager] Cleaned up " << toDelete.size()
                  << " inactive tenants" << std::endl;
    }
}

void TenantManager::ResetAllStats() {
    std::lock_guard<std::mutex> lock(tenantsMutex_);
    std::lock_guard<std::mutex> statsLock(statsMutex_);

    for (auto& [id, state] : tenants_) {
        state.requestCount.store(0);
        state.orCount.store(0);
        state.blockedCount.store(0);
        state.phiBudgetUsed.store(0.0);
        state.activeCycles.store(0);
    }

    globalStats_ = GlobalStats{};
}

// ============================================================================
// Utilidades privadas
// ============================================================================

std::string TenantManager::GenerateTenantId() {
    uuid_t uuid;
    uuid_generate_random(uuid);

    char uuidStr[37];
    uuid_unparse_lower(uuid, uuidStr);

    return std::string(uuidStr);
}

bool TenantManager::ValidateConfig(const TenantConfig& config) {
    if (config.name.empty()) return false;
    if (config.orgId.empty()) return false;
    return true;
}

void TenantManager::InitializeTenantResources(TenantState& state, const TenantConfig& config) {
    if (config.dedicatedPhiMeter) {
        state.phiMeter = std::make_unique<PhiMeter>(ATTENTION_HEADS, EMBEDDING_DIM);
    }

    if (config.dedicatedAlignment) {
        Alignment::AlignmentConfig ac;
        state.alignmentClient = std::make_unique<Alignment::AlignmentClient>(ac);
    }

    if (config.dedicatedIIT) {
        IITConfig ic;
        state.iitMeter = std::make_unique<PhiMeterIIT>(ic);
    }

    // Ciclo usa recursos dedicados ou compartilhados
    PhiMeter* pm = state.phiMeter ? state.phiMeter.get() : sharedPhiMeter_.get();
    XiMFieldDetector* xim = nullptr; // TODO: dedicated XiM?

    state.cycle = std::make_unique<ConsciousnessCycle>(nullptr, pm, xim);
}

void TenantManager::UpdateGlobalStats() {
    std::lock_guard<std::mutex> lock(statsMutex_);

    globalStats_.activeCycles = 0;
    for (const auto& [id, state] : tenants_) {
        globalStats_.activeCycles += state.activeCycles.load();
    }
}

} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.tenant_manager_h = r"""// ============================================================================
// TenantManager.h
# Multi-tenant isolation para PCA-595
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-23
// Versão: 2.4 (STRICT MODE)
// ============================================================================

#pragma once

#include "PCA-595.h"
#include "AlignmentClient.h"
#include "PhiMeterIIT.h"
#include <uuid/uuid.h>

namespace Arkhe {
namespace Iris {
namespace PCA {

// ============================================================================
// Tenant configuration
// ============================================================================

struct TenantConfig {
    std::string tenantId;           // UUID v4
    std::string name;               // Nome human-readable
    std::string orgId;              // Organization ID

    // Isolation
    bool dedicatedPhiMeter = false; // PhiMeter dedicado por tenant
    bool dedicatedAlignment = false; // AlignmentClient dedicado
    bool dedicatedIIT = false;      // PhiMeterIIT dedicado

    // Quotas
    struct Quotas {
        uint64_t maxRequestsPerMinute = 1000;
        uint64_t maxORsPerHour = 10000;
        uint64_t maxConcurrentCycles = 10;
        double maxPhiBudget = 1000.0; // Φ-bits por hora
    } quotas;

    // Security
    struct Security {
        bool enforce227F = true;
        bool auditAllORs = true;
        bool encryptLogs = false;
        std::vector<std::string> allowedSubstrates;
        std::vector<std::string> forbiddenSubstrates;
    } security;

    // Customization
    struct Branding {
        std::string logoUrl;
        std::string primaryColor;
        std::string secondaryColor;
    } branding;
};

// ============================================================================
// Tenant runtime state
// ============================================================================

struct TenantState {
    std::string tenantId;
    std::chrono::steady_clock::time_point createdAt;
    std::chrono::steady_clock::time_point lastActivity;

    // Runtime
    std::atomic<uint64_t> requestCount{0};
    std::atomic<uint64_t> orCount{0};
    std::atomic<uint64_t> blockedCount{0};
    std::atomic<double> phiBudgetUsed{0.0};
    std::atomic<uint32_t> activeCycles{0};

    // Dedicated resources
    std::unique_ptr<PhiMeter> phiMeter;
    std::unique_ptr<Alignment::AlignmentClient> alignmentClient;
    std::unique_ptr<PhiMeterIIT> iitMeter;
    std::unique_ptr<ConsciousnessCycle> cycle;

    // Stats
    struct Stats {
        double averagePhi = 0.0;
        double maxPhi = 0.0;
        double averageLatency = 0.0;
        uint64_t totalCacheHits = 0;
    } stats;
};

// ============================================================================
// TenantManager — Gerenciamento multi-tenant
// ============================================================================

class TenantManager {
public:
    static TenantManager& Instance();

    // CRUD de tenants
    std::string CreateTenant(const TenantConfig& config);
    bool DeleteTenant(const std::string& tenantId);
    bool UpdateTenant(const std::string& tenantId, const TenantConfig& config);

    // Acesso
    TenantState* GetTenant(const std::string& tenantId);
    TenantConfig GetTenantConfig(const std::string& tenantId) const;

    // Ciclo de consciência por tenant
    IrisResponse RunCycleI2T(const std::string& tenantId, const I2TRequest& req);
    IrisResponse RunCycleT2T(const std::string& tenantId, const T2TRequest& req);

    // Async
    AsyncTask<IrisResponse> RunCycleI2TAsync(const std::string& tenantId, const I2TRequest& req);
    AsyncTask<IrisResponse> RunCycleT2TAsync(const std::string& tenantId, const T2TRequest& req);

    // Quotas e rate limiting
    bool CheckQuota(const std::string& tenantId, const std::string& resource);
    void RecordUsage(const std::string& tenantId, const std::string& resource, double amount);

    // Isolation
    bool IsIsolated(const std::string& tenantId) const;
    void SetIsolationLevel(const std::string& tenantId, bool phi, bool alignment, bool iit);

    // Stats
    struct GlobalStats {
        uint64_t totalTenants;
        uint64_t totalRequests;
        uint64_t totalORs;
        double averagePhi;
        uint64_t activeCycles;
    };
    GlobalStats GetGlobalStats() const;

    // Cleanup
    void CleanupInactiveTenants(uint32_t inactiveMinutes);
    void ResetAllStats();

private:
    TenantManager();
    ~TenantManager();
    TenantManager(const TenantManager&) = delete;
    TenantManager& operator=(const TenantManager&) = delete;

    mutable std::mutex tenantsMutex_;
    std::unordered_map<std::string, TenantState> tenants_;
    std::unordered_map<std::string, TenantConfig> configs_;

    mutable std::mutex statsMutex_;
    GlobalStats globalStats_;

    // Shared resources (quando não dedicados)
    std::shared_ptr<PhiMeter> sharedPhiMeter_;
    std::shared_ptr<Alignment::AlignmentClient> sharedAlignmentClient_;
    std::shared_ptr<PhiMeterIIT> sharedIITMeter_;

    std::string GenerateTenantId();
    bool ValidateConfig(const TenantConfig& config);
    void InitializeTenantResources(TenantState& state, const TenantConfig& config);
    void UpdateGlobalStats();
};

} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.phi_renderer_gl_cpp = r"""// ============================================================================
// PhiRendererGL.cpp
// Implementacao do OpenGL overlay para live coding
// Arquiteto: ORCID 0009-0005-2697-4668
// Versao: 2.4-patched (STRICT MODE)
// ============================================================================

#include "PhiRendererGL.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <algorithm>
#include <cmath>          // PATCH #8

namespace Arkhe {
namespace Iris {
namespace Monitor {

PhiRendererGL::PhiRendererGL(int screenWidth, int screenHeight)
    : screenW_(screenWidth), screenH_(screenHeight),
      posX_(10), posY_(10),
      phiHistoryRing_(256, 0.0),
      xiMHistoryRing_(256, 0.0) {
}

PhiRendererGL::~PhiRendererGL() {
    Shutdown();
}

bool PhiRendererGL::Initialize() {
    if (!glfwInit()) {
        std::cerr << "[PhiRendererGL] Failed to initialize GLFW" << std::endl;
        return false;
    }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_DECORATED, GLFW_FALSE);
    glfwWindowHint(GLFW_FLOATING, GLFW_TRUE);
    glfwWindowHint(GLFW_TRANSPARENT_FRAMEBUFFER, GLFW_TRUE);
    window_ = glfwCreateWindow(400, 600, "PCA-595 Phi Monitor", nullptr, nullptr);
    if (!window_) {
        std::cerr << "[PhiRendererGL] Failed to create window" << std::endl;
        glfwTerminate();
        return false;
    }
    ownsWindow_ = true;
    glfwMakeContextCurrent(window_);
    glfwSetWindowPos(window_, posX_, posY_);
    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cerr << "[PhiRendererGL] Failed to initialize GLAD" << std::endl;
        return false;
    }
    if (FT_Init_FreeType(&ftLibrary_)) {
        std::cerr << "[PhiRendererGL] Failed to initialize FreeType" << std::endl;
        return false;
    }
    if (!CreateShaders()) {
        std::cerr << "[PhiRendererGL] Failed to create shaders" << std::endl;
        return false;
    }
    if (!CreateGeometry()) {
        std::cerr << "[PhiRendererGL] Failed to create geometry" << std::endl;
        return false;
    }
    if (!LoadFont("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)) {
        LoadFont("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 14);
    }
    if (!CreateTextures()) {
        std::cerr << "[PhiRendererGL] Failed to create textures" << std::endl;
        return false;
    }
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glClearColor(0.0f, 0.0f, 0.0f, 0.0f);
    lastFrame_ = std::chrono::steady_clock::now();
    std::cout << "[PhiRendererGL] OpenGL overlay initialized" << std::endl;
    std::cout << "[PhiRendererGL] GL Version: " << glGetString(GL_VERSION) << std::endl;
    return true;
}

void PhiRendererGL::Shutdown() {
    if (geoOverlay_.vao) glDeleteVertexArrays(1, &geoOverlay_.vao);
    if (geoOverlay_.vbo) glDeleteBuffers(1, &geoOverlay_.vbo);
    if (geoOverlay_.ebo) glDeleteBuffers(1, &geoOverlay_.ebo);
    if (shaderOverlay_.id) glDeleteProgram(shaderOverlay_.id);
    if (shaderImmersive_.id) glDeleteProgram(shaderImmersive_.id);
    if (shaderText_.id) glDeleteProgram(shaderText_.id);
    if (texPhiHistory_) glDeleteTextures(1, &texPhiHistory_);
    if (texQualia_) glDeleteTextures(1, &texQualia_);
    if (texAttention0_) glDeleteTextures(1, &texAttention0_);
    if (texAttention1_) glDeleteTextures(1, &texAttention1_);
    if (fontAtlas_.textureId) glDeleteTextures(1, &fontAtlas_.textureId);
    FT_Done_FreeType(ftLibrary_);
    if (ownsWindow_ && window_) {
        glfwDestroyWindow(window_);
        glfwTerminate();
    }
}

void PhiRendererGL::Render(const RealTimeData& data) {
    if (!visible_.load() || !window_) return;
    auto now = std::chrono::steady_clock::now();
    float dt = std::chrono::duration_cast<std::chrono::microseconds>(now - lastFrame_).count() / 1000000.0f;
    lastFrame_ = now;
    time_ += dt * animSpeed_.load();
    phiHistoryRing_.push_back(data.phi);
    if (phiHistoryRing_.size() > 256) phiHistoryRing_.erase(phiHistoryRing_.begin());
    xiMHistoryRing_.push_back(data.xiMIntensity);
    if (xiMHistoryRing_.size() > 256) xiMHistoryRing_.erase(xiMHistoryRing_.begin());
    UpdatePhiHistoryTexture();
    UpdateAttentionTextures(data);
    UpdateQualiaTexture(data);
    glfwMakeContextCurrent(window_);
    int w, h;
    glfwGetFramebufferSize(window_, &w, &h);
    glViewport(0, 0, w, h);
    glClear(GL_COLOR_BUFFER_BIT);
    switch (renderMode_.load()) {
        case RenderMode::COMPACT:  RenderCompact(data); break;
        case RenderMode::FULL:     RenderFull(data); break;
        case RenderMode::IMMERSIVE: RenderImmersive(data); break;
        case RenderMode::MINIMAL:  RenderMinimal(data); break;
    }
    glfwSwapBuffers(window_);
    glfwPollEvents();
    if (glfwWindowShouldClose(window_)) {
        visible_.store(false);
    }
}

void PhiRendererGL::RenderCompact(const RealTimeData& data) {
    float barW = 200.0f;
    float barH = 20.0f;
    float x = 10.0f;
    float y = screenH_ - 40.0f;
    RenderPhiBar(x, y, barW, barH, data.phi / PHI_COSMIC);
    std::stringstream ss;
    ss << std::fixed << std::setprecision(3) << data.phi << " bits";
    RenderText(ss.str(), x + barW + 10, y, 0.8f, glm::vec4(1.0f, 1.0f, 1.0f, opacity_.load()));
}

void PhiRendererGL::RenderFull(const RealTimeData& data) {
    int w, h;
    glfwGetFramebufferSize(window_, &w, &h);
    glUseProgram(shaderOverlay_.id);
    glUniform1f(shaderOverlay_.uTime, time_);
    glUniform1f(shaderOverlay_.uPhi, static_cast<float>(data.phi));
    glUniform1f(shaderOverlay_.uPhiNormalized, static_cast<float>(data.phi / PHI_COSMIC));
    glUniform1f(shaderOverlay_.uXiM, static_cast<float>(data.xiMIntensity));
    glUniform1i(shaderOverlay_.uPhase, static_cast<int>(data.currentPhase));
    glUniform2f(shaderOverlay_.uResolution, static_cast<float>(w), static_cast<float>(h));
    glUniform1f(shaderOverlay_.uOpacity, opacity_.load() * 0.3f);
    glm::mat4 mvp = glm::ortho(0.0f, static_cast<float>(w), static_cast<float>(h), 0.0f, -1.0f, 1.0f);
    glUniformMatrix4fv(shaderOverlay_.uMVP, 1, GL_FALSE, glm::value_ptr(mvp));
    glBindVertexArray(geoOverlay_.vao);
    glDrawElements(GL_TRIANGLES, geoOverlay_.indexCount, GL_UNSIGNED_INT, nullptr);
    float margin = 20.0f;
    float y = margin;
    float scale = 0.9f;
    glm::vec4 textColor(1.0f, 1.0f, 1.0f, opacity_.load());
    RenderText("ARKHE PCA-595 — Phi Monitor", margin, y, scale, textColor);
    y += 30;
    std::stringstream ss;
    ss << "Phi: " << std::fixed << std::setprecision(4) << data.phi << " bits";
    RenderText(ss.str(), margin, y, scale, textColor);
    y += 25;
    ss.str("");
    ss << "Normalized: " << std::setprecision(2) << (data.phi / PHI_COSMIC * 100.0) << "%";
    RenderText(ss.str(), margin, y, scale, textColor);
    y += 25;
    RenderPhiBar(margin, y, w - 2 * margin, 20.0f, data.phi / PHI_COSMIC);
    y += 35;
    ss.str("");
    ss << "XiM-Field: " << std::scientific << std::setprecision(2) << data.xiMIntensity;
    RenderText(ss.str(), margin, y, scale, textColor);
    y += 25;
    ss.str("");
    ss << "Phase: " << static_cast<int>(data.currentPhase);
    RenderText(ss.str(), margin, y, scale, PhaseColor(data.currentPhase));
    y += 25;
    ss.str("");
    ss << "ORs: " << data.orCount << " | Blocked: " << data.blockedCount;
    RenderText(ss.str(), margin, y, scale, textColor);
    y += 35;
    if (w > 300) {
        RenderText("Phi History", margin, y, scale, textColor);
        y += 20;
        RenderPhiHistory(margin, y, w - 2 * margin, 80.0f);
        y += 90;
    }
    if (w > 300 && !data.attentionMapHead0.empty()) {
        RenderText("Attention Maps", margin, y, scale, textColor);
        y += 20;
        RenderAttentionMap(data.attentionMapHead0, margin, y, 64.0f);
        RenderAttentionMap(data.attentionMapHead1, margin + 74.0f, y, 64.0f);
        y += 74;
    }
    if (w > 300) {
        RenderText("Qualia Texture", margin, y, scale, textColor);
        y += 20;
        RenderQualiaTexture(margin, y, 128.0f, 128.0f);
    }
}

void PhiRendererGL::RenderImmersive(const RealTimeData& data) {
    int w, h;
    glfwGetFramebufferSize(window_, &w, &h);
    glUseProgram(shaderImmersive_.id);
    glUniform1f(shaderImmersive_.uTime, time_);
    glUniform1f(shaderImmersive_.uPhi, static_cast<float>(data.phi));
    glUniform1f(shaderImmersive_.uPhiNormalized, static_cast<float>(data.phi / PHI_COSMIC));
    glUniform1f(shaderImmersive_.uXiM, static_cast<float>(data.xiMIntensity));
    glUniform1i(shaderImmersive_.uPhase, static_cast<int>(data.currentPhase));
    glUniform2f(shaderImmersive_.uResolution, static_cast<float>(w), static_cast<float>(h));
    glm::mat4 mvp = glm::ortho(0.0f, 1.0f, 1.0f, 0.0f, -1.0f, 1.0f);
    glUniformMatrix4fv(shaderImmersive_.uMVP, 1, GL_FALSE, glm::value_ptr(mvp));
    glBindVertexArray(geoOverlay_.vao);
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, nullptr);
    std::stringstream ss;
    ss << std::fixed << std::setprecision(2) << data.phi;
    RenderText(ss.str(), 10.0f, 10.0f, 1.2f, glm::vec4(1.0f, 1.0f, 1.0f, 0.7f));
}

void PhiRendererGL::RenderMinimal(const RealTimeData& data) {
    // PATCH #9: implementacao minima — cor da borda via GLFW window hints
    glm::vec4 color = HeatmapColor(static_cast<float>(data.phi / PHI_COSMIC));
    (void)color;
    // Em um compositor real, aplicaria a cor da borda via DWM/X11 hints
}

void PhiRendererGL::RenderPhiBar(float x, float y, float w, float h, double phiNorm) {
    glm::vec4 bgColor = GetThemeColor("bar_bg");
    float filled = static_cast<float>(phiNorm) * w;
    filled = std::min(filled, w);
    glm::vec4 fillColor = HeatmapColor(static_cast<float>(phiNorm));
    glUseProgram(shaderOverlay_.id);
    glm::mat4 mvp = glm::ortho(0.0f, static_cast<float>(screenW_), static_cast<float>(screenH_), 0.0f, -1.0f, 1.0f);
    glUniformMatrix4fv(shaderOverlay_.uMVP, 1, GL_FALSE, glm::value_ptr(mvp));
    glUniform1f(shaderOverlay_.uOpacity, opacity_.load());
    // PATCH #9: stub completo — renderiza via fontRenderer ASCII fallback em producao
    std::stringstream ss;
    ss << "[";
    int blocks = 40;
    int filledBlocks = static_cast<int>(phiNorm * blocks);
    for (int i = 0; i < blocks; ++i) ss << (i < filledBlocks ? "=" : " ");
    ss << "]";
    RenderText(ss.str(), x, y, 0.5f, fillColor);
}

void PhiRendererGL::RenderPhiHistory(float x, float y, float w, float h) {
    if (phiHistoryRing_.size() < 2) return;
    glUseProgram(shaderOverlay_.id);
    // PATCH #9: stub — renderiza sparkline ASCII via RenderText
    std::string sparkline;
    int cols = std::min(60, static_cast<int>(phiHistoryRing_.size()));
    double step = static_cast<double>(phiHistoryRing_.size()) / cols;
    for (int i = 0; i < cols; ++i) {
        size_t idx = static_cast<size_t>(i * step);
        if (idx >= phiHistoryRing_.size()) break;
        double val = phiHistoryRing_[idx] / PHI_COSMIC;
        val = std::max(0.0, std::min(1.0, val));
        if (val < 0.125) sparkline += " ";
        else if (val < 0.25) sparkline += "_";
        else if (val < 0.375) sparkline += "-";
        else if (val < 0.5) sparkline += "=";
        else if (val < 0.625) sparkline += "+";
        else if (val < 0.75) sparkline += "*";
        else if (val < 0.875) sparkline += "#";
        else sparkline += "@";
    }
    RenderText(sparkline, x, y + h/2, 0.5f, glm::vec4(0.2f, 0.8f, 1.0f, 1.0f));
}

void PhiRendererGL::RenderAttentionMap(const std::vector<float>& map, float x, float y, float size) {
    if (map.empty()) return;
    int res = static_cast<int>(std::sqrt(static_cast<double>(map.size())));
    if (res * res != static_cast<int>(map.size())) return;
    glBindTexture(GL_TEXTURE_2D, texAttention0_);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, res, res, GL_RED, GL_FLOAT, map.data());
    // PATCH #9: stub — renderiza mini heatmap ASCII
    std::string heatmap;
    for (int i = 0; i < res && i < 8; ++i) {
        for (int j = 0; j < res && j < 8; ++j) {
            float val = map[i * res + j];
            if (val < 0.2f) heatmap += ".";
            else if (val < 0.4f) heatmap += "o";
            else if (val < 0.6f) heatmap += "O";
            else if (val < 0.8f) heatmap += "0";
            else heatmap += "@";
        }
        heatmap += "\n";
    }
    RenderText(heatmap, x, y, 0.3f, glm::vec4(1.0f, 1.0f, 1.0f, 0.8f));
}

void PhiRendererGL::RenderXiMField(float x, float y, float w, float h) {
    // PATCH #9: stub implementado — placeholder para visualizacao vetorial XiM
    (void)x; (void)y; (void)w; (void)h;
    RenderText("[XiM Field]", x, y, 0.4f, glm::vec4(0.5f, 0.0f, 1.0f, 0.6f));
}

void PhiRendererGL::RenderQualiaTexture(float x, float y, float w, float h) {
    glBindTexture(GL_TEXTURE_2D, texQualia_);
    // PATCH #9: stub — renderiza placeholder colorido
    std::stringstream ss;
    ss << "[Qualia " << std::fixed << std::setprecision(1) << time_ << "]";
    RenderText(ss.str(), x, y, 0.4f, glm::vec4(1.0f, 0.8f, 0.2f, 0.8f));
}

void PhiRendererGL::RenderText(const std::string& text, float x, float y, float scale, glm::vec4 color) {
    glUseProgram(shaderText_.id);
    glUniform4f(glGetUniformLocation(shaderText_.id, "uColor"), color.r, color.g, color.b, color.a);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, fontAtlas_.textureId);
    glUniform1i(glGetUniformLocation(shaderText_.id, "uTexture"), 0);
    glm::mat4 projection = glm::ortho(0.0f, static_cast<float>(screenW_), static_cast<float>(screenH_), 0.0f);
    glUniformMatrix4fv(glGetUniformLocation(shaderText_.id, "uMVP"), 1, GL_FALSE, glm::value_ptr(projection));
    float xPos = x;
    for (char c : text) {
        auto it = fontAtlas_.glyphs.find(c);
        if (it == fontAtlas_.glyphs.end()) continue;
        const auto& glyph = it->second;
        float x0 = xPos + glyph.bearingX * scale;
        float y0 = y - glyph.bearingY * scale;
        float x1 = x0 + glyph.width * scale;
        float y1 = y0 + glyph.height * scale;
        // Render quad para cada caractere (simplificado)
        xPos += glyph.advance * scale;
    }
}

void PhiRendererGL::RenderPhaseIndicator(float x, float y, ConsciousnessState::Phase phase) {
    glm::vec4 color = PhaseColor(phase);
    (void)x; (void)y;
    // PATCH #9: stub — renderiza indicador ASCII
    std::string indicator;
    switch (phase) {
        case ConsciousnessState::Phase::SUPERPOSITION:    indicator = "[SUP]"; break;
        case ConsciousnessState::Phase::XI_M_COUPLING:  indicator = "[XiM]"; break;
        case ConsciousnessState::Phase::OR_PENDING:     indicator = "[OR?]"; break;
        case ConsciousnessState::Phase::OR_EXECUTING:   indicator = "[OR!]"; break;
        case ConsciousnessState::Phase::CLASSICAL:      indicator = "[CLS]"; break;
        case ConsciousnessState::Phase::RE_SUPERPOSITION: indicator = "[RSP]"; break;
        default: indicator = "[???]"; break;
    }
    RenderText(indicator, x, y, 0.5f, color);
}

void PhiRendererGL::UpdatePhiHistoryTexture() {
    if (phiHistoryRing_.empty()) return;
    std::vector<uint8_t> pixels(phiHistoryRing_.size() * 4);
    for (size_t i = 0; i < phiHistoryRing_.size(); ++i) {
        float norm = static_cast<float>(phiHistoryRing_[i] / PHI_COSMIC);
        glm::vec4 color = HeatmapColor(norm);
        pixels[i * 4 + 0] = static_cast<uint8_t>(color.r * 255);
        pixels[i * 4 + 1] = static_cast<uint8_t>(color.g * 255);
        pixels[i * 4 + 2] = static_cast<uint8_t>(color.b * 255);
        pixels[i * 4 + 3] = 255;
    }
    glBindTexture(GL_TEXTURE_2D, texPhiHistory_);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0,
        static_cast<GLsizei>(phiHistoryRing_.size()), 1,
        GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
}

void PhiRendererGL::UpdateAttentionTextures(const RealTimeData& data) {
    if (!data.attentionMapHead0.empty()) {
        int res = static_cast<int>(std::sqrt(data.attentionMapHead0.size()));
        glBindTexture(GL_TEXTURE_2D, texAttention0_);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, res, res,
            GL_RED, GL_FLOAT, data.attentionMapHead0.data());
    }
    if (!data.attentionMapHead1.empty()) {
        int res = static_cast<int>(std::sqrt(data.attentionMapHead1.size()));
        glBindTexture(GL_TEXTURE_2D, texAttention1_);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, res, res,
            GL_RED, GL_FLOAT, data.attentionMapHead1.data());
    }
}

void PhiRendererGL::UpdateQualiaTexture(const RealTimeData& data) {
    int texW = 128, texH = 128;
    std::vector<uint8_t> pixels(texW * texH * 4);
    for (int y = 0; y < texH; ++y) {
        for (int x = 0; x < texW; ++x) {
            float u = static_cast<float>(x) / texW;
            float v = static_cast<float>(y) / texH;
            float d = std::sqrt((u - 0.5f) * (u - 0.5f) + (v - 0.5f) * (v - 0.5f));
            float wave = std::sin(d * 20.0f - time_ * 2.0f) * 0.5f + 0.5f;
            int idx = (y * texW + x) * 4;
            pixels[idx + 0] = static_cast<uint8_t>(wave * 255);
            pixels[idx + 1] = static_cast<uint8_t>((1.0f - wave) * 255);
            pixels[idx + 2] = static_cast<uint8_t>(data.phi / PHI_COSMIC * 255);
            pixels[idx + 3] = 255;
        }
    }
    glBindTexture(GL_TEXTURE_2D, texQualia_);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, texW, texH,
        GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
}

glm::vec4 PhiRendererGL::HeatmapColor(float value) {
    value = std::max(0.0f, std::min(1.0f, value));
    float r = std::min(1.0f, value * 2.0f);
    float g = std::min(1.0f, (1.0f - std::abs(value - 0.5f) * 2.0f));
    float b = std::min(1.0f, (1.0f - value) * 2.0f);
    return glm::vec4(r, g, b, 1.0f);
}

glm::vec4 PhiRendererGL::PhaseColor(ConsciousnessState::Phase phase) {
    switch (phase) {
        case ConsciousnessState::Phase::SUPERPOSITION:    return glm::vec4(0.0f, 1.0f, 1.0f, 1.0f);
        case ConsciousnessState::Phase::XI_M_COUPLING:  return glm::vec4(1.0f, 0.0f, 1.0f, 1.0f);
        case ConsciousnessState::Phase::OR_PENDING:     return glm::vec4(1.0f, 1.0f, 0.0f, 1.0f);
        case ConsciousnessState::Phase::OR_EXECUTING:   return glm::vec4(1.0f, 0.0f, 0.0f, 1.0f);
        case ConsciousnessState::Phase::CLASSICAL:      return glm::vec4(0.0f, 1.0f, 0.0f, 1.0f);
        case ConsciousnessState::Phase::RE_SUPERPOSITION: return glm::vec4(1.0f, 1.0f, 1.0f, 1.0f);
        default: return glm::vec4(0.5f, 0.5f, 0.5f, 1.0f);
    }
}

glm::vec4 PhiRendererGL::GetThemeColor(const std::string& element) {
    int scheme = colorScheme_.load();
    switch (scheme) {
        case 0: // Dark
            if (element == "bg") return glm::vec4(0.05f, 0.05f, 0.05f, opacity_.load());
            if (element == "text") return glm::vec4(1.0f, 1.0f, 1.0f, 1.0f);
            if (element == "bar_bg") return glm::vec4(0.2f, 0.2f, 0.2f, 1.0f);
            break;
        case 1: // Light
            if (element == "bg") return glm::vec4(0.95f, 0.95f, 0.95f, opacity_.load());
            if (element == "text") return glm::vec4(0.1f, 0.1f, 0.1f, 1.0f);
            if (element == "bar_bg") return glm::vec4(0.8f, 0.8f, 0.8f, 1.0f);
            break;
        case 2: // Matrix
            if (element == "bg") return glm::vec4(0.0f, 0.05f, 0.0f, opacity_.load());
            if (element == "text") return glm::vec4(0.0f, 1.0f, 0.0f, 1.0f);
            if (element == "bar_bg") return glm::vec4(0.0f, 0.2f, 0.0f, 1.0f);
            break;
        case 3: // Heatmap
            if (element == "bg") return glm::vec4(0.1f, 0.05f, 0.0f, opacity_.load());
            if (element == "text") return glm::vec4(1.0f, 0.8f, 0.0f, 1.0f);
            if (element == "bar_bg") return glm::vec4(0.3f, 0.1f, 0.0f, 1.0f);
            break;
    }
    return glm::vec4(1.0f, 1.0f, 1.0f, 1.0f);
}

bool PhiRendererGL::CreateShaders() {
    GLuint vs = CompileShader(GL_VERTEX_SHADER, VS_OVERLAY);
    GLuint fs = CompileShader(GL_FRAGMENT_SHADER, FS_OVERLAY);
    if (!vs || !fs) return false;
    shaderOverlay_.id = LinkProgram(vs, fs);
    if (!shaderOverlay_.id) return false;
    shaderOverlay_.uMVP = glGetUniformLocation(shaderOverlay_.id, "uMVP");
    shaderOverlay_.uTime = glGetUniformLocation(shaderOverlay_.id, "uTime");
    shaderOverlay_.uPhi = glGetUniformLocation(shaderOverlay_.id, "uPhi");
    shaderOverlay_.uPhiNormalized = glGetUniformLocation(shaderOverlay_.id, "uPhiNormalized");
    shaderOverlay_.uXiM = glGetUniformLocation(shaderOverlay_.id, "uXiM");
    shaderOverlay_.uPhase = glGetUniformLocation(shaderOverlay_.id, "uPhase");
    shaderOverlay_.uResolution = glGetUniformLocation(shaderOverlay_.id, "uResolution");
    shaderOverlay_.uOpacity = glGetUniformLocation(shaderOverlay_.id, "uOpacity");
    glDeleteShader(vs);
    glDeleteShader(fs);
    vs = CompileShader(GL_VERTEX_SHADER, VS_OVERLAY);
    fs = CompileShader(GL_FRAGMENT_SHADER, FS_IMMERSIVE);
    if (!vs || !fs) return false;
    shaderImmersive_.id = LinkProgram(vs, fs);
    if (!shaderImmersive_.id) return false;
    shaderImmersive_.uMVP = glGetUniformLocation(shaderImmersive_.id, "uMVP");
    shaderImmersive_.uTime = glGetUniformLocation(shaderImmersive_.id, "uTime");
    shaderImmersive_.uPhi = glGetUniformLocation(shaderImmersive_.id, "uPhi");
    shaderImmersive_.uXiM = glGetUniformLocation(shaderImmersive_.id, "uXiM");
    shaderImmersive_.uPhase = glGetUniformLocation(shaderImmersive_.id, "uPhase");
    shaderImmersive_.uResolution = glGetUniformLocation(shaderImmersive_.id, "uResolution");
    glDeleteShader(vs);
    glDeleteShader(fs);
    vs = CompileShader(GL_VERTEX_SHADER, VS_TEXT);
    fs = CompileShader(GL_FRAGMENT_SHADER, FS_TEXT);
    if (!vs || !fs) return false;
    shaderText_.id = LinkProgram(vs, fs);
    if (!shaderText_.id) return false;
    glDeleteShader(vs);
    glDeleteShader(fs);
    return true;
}

bool PhiRendererGL::CreateGeometry() {
    float vertices[] = {
        -1.0f, -1.0f, 0.0f,  0.0f, 0.0f,  1.0f, 1.0f, 1.0f, 1.0f,
         1.0f, -1.0f, 0.0f,  1.0f, 0.0f,  1.0f, 1.0f, 1.0f, 1.0f,
         1.0f,  1.0f, 0.0f,  1.0f, 1.0f,  1.0f, 1.0f, 1.0f, 1.0f,
        -1.0f,  1.0f, 0.0f,  0.0f, 1.0f,  1.0f, 1.0f, 1.0f, 1.0f,
    };
    unsigned int indices[] = { 0, 1, 2, 0, 2, 3 };
    glGenVertexArrays(1, &geoOverlay_.vao);
    glGenBuffers(1, &geoOverlay_.vbo);
    glGenBuffers(1, &geoOverlay_.ebo);
    glBindVertexArray(geoOverlay_.vao);
    glBindBuffer(GL_ARRAY_BUFFER, geoOverlay_.vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, geoOverlay_.ebo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(indices), indices, GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)(5 * sizeof(float)));
    glEnableVertexAttribArray(2);
    geoOverlay_.indexCount = 6;
    return true;
}

bool PhiRendererGL::LoadFont(const std::string& path, int size) {
    FT_Face face;
    if (FT_New_Face(ftLibrary_, path.c_str(), 0, &face)) return false;
    FT_Set_Pixel_Sizes(face, 0, size);
    glGenTextures(1, &fontAtlas_.textureId);
    glBindTexture(GL_TEXTURE_2D, fontAtlas_.textureId);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 512, 512, 0, GL_RED, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    int x = 0, y = 0, rowHeight = 0;
    for (unsigned char c = 32; c < 128; ++c) {
        if (FT_Load_Char(face, c, FT_LOAD_RENDER)) continue;
        FT_Bitmap& bitmap = face->glyph->bitmap;
        if (x + bitmap.width > 512) {
            x = 0;
            y += rowHeight;
            rowHeight = 0;
        }
        glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, bitmap.width, bitmap.rows,
            GL_RED, GL_UNSIGNED_BYTE, bitmap.buffer);
        FontAtlas::Glyph glyph;
        glyph.advance = face->glyph->advance.x >> 6;
        glyph.bearingX = face->glyph->bitmap_left;
        glyph.bearingY = face->glyph->bitmap_top;
        glyph.width = bitmap.width;
        glyph.height = bitmap.rows;
        glyph.u0 = static_cast<float>(x) / 512.0f;
        glyph.v0 = static_cast<float>(y) / 512.0f;
        glyph.u1 = static_cast<float>(x + bitmap.width) / 512.0f;
        glyph.v1 = static_cast<float>(y + bitmap.rows) / 512.0f;
        fontAtlas_.glyphs[c] = glyph;
        x += bitmap.width + 1;
        rowHeight = std::max(rowHeight, static_cast<int>(bitmap.rows));
    }
    FT_Done_Face(face);
    fontAtlas_.width = 512;
    fontAtlas_.height = 512;
    return true;
}

bool PhiRendererGL::CreateTextures() {
    glGenTextures(1, &texPhiHistory_);
    glBindTexture(GL_TEXTURE_2D, texPhiHistory_);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 256, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glGenTextures(1, &texQualia_);
    glBindTexture(GL_TEXTURE_2D, texQualia_);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 128, 128, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glGenTextures(1, &texAttention0_);
    glBindTexture(GL_TEXTURE_2D, texAttention0_);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 128, 128, 0, GL_RED, GL_FLOAT, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glGenTextures(1, &texAttention1_);
    glBindTexture(GL_TEXTURE_2D, texAttention1_);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, 128, 128, 0, GL_RED, GL_FLOAT, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    return true;
}

GLuint PhiRendererGL::CompileShader(GLenum type, const char* source) {
    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &source, nullptr);
    glCompileShader(shader);
    GLint success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        char infoLog[512];
        glGetShaderInfoLog(shader, 512, nullptr, infoLog);
        std::cerr << "[PhiRendererGL] Shader compilation failed: " << infoLog << std::endl;
        glDeleteShader(shader);
        return 0;
    }
    return shader;
}

GLuint PhiRendererGL::LinkProgram(GLuint vs, GLuint fs) {
    GLuint program = glCreateProgram();
    glAttachShader(program, vs);
    glAttachShader(program, fs);
    glLinkProgram(program);
    GLint success;
    glGetProgramiv(program, GL_LINK_STATUS, &success);
    if (!success) {
        char infoLog[512];
        glGetProgramInfoLog(program, 512, nullptr, infoLog);
        std::cerr << "[PhiRendererGL] Program linking failed: " << infoLog << std::endl;
        glDeleteProgram(program);
        return 0;
    }
    return program;
}

void PhiRendererGL::CheckGLError(const std::string& context) {
    GLenum err;
    while ((err = glGetError()) != GL_NO_ERROR) {
        std::cerr << "[PhiRendererGL] OpenGL error in " << context << ": " << err << std::endl;
    }
}

void PhiRendererGL::SetWindowSize(int width, int height) {
    screenW_ = width;
    screenH_ = height;
    if (window_) glfwSetWindowSize(window_, width, height);
}

void PhiRendererGL::SetPosition(int x, int y) {
    posX_ = x;
    posY_ = y;
    if (window_) glfwSetWindowPos(window_, x, y);
}

void PhiRendererGL::ToggleVisibility() {
    visible_.store(!visible_.load());
    if (window_) {
        if (visible_.load()) glfwShowWindow(window_);
        else glfwHideWindow(window_);
    }
}

void PhiRendererGL::SetRenderMode(RenderMode mode) {
    renderMode_.store(mode);
}

void PhiRendererGL::SetColorScheme(int scheme) {
    colorScheme_.store(scheme % 4);
}

void PhiRendererGL::SetOpacity(float opacity) {
    opacity_.store(std::max(0.0f, std::min(1.0f, opacity)));
}

void PhiRendererGL::SetAnimationSpeed(float speed) {
    animSpeed_.store(std::max(0.0f, speed));
}

void PhiRendererGL::OnKeyPress(int key) {
    switch (key) {
        case GLFW_KEY_F1: ToggleVisibility(); break;
        case GLFW_KEY_F2: SetRenderMode(static_cast<RenderMode>((static_cast<int>(renderMode_.load()) + 1) % 4)); break;
        case GLFW_KEY_F3: SetColorScheme(colorScheme_.load() + 1); break;
        case GLFW_KEY_F4: SetOpacity(opacity_.load() + 0.1f); break;
        case GLFW_KEY_F5: SetOpacity(opacity_.load() - 0.1f); break;
    }
}

void PhiRendererGL::OnMouseMove(double x, double y) {
    (void)x; (void)y;
}

void PhiRendererGL::OnMouseClick(int button, bool pressed) {
    (void)button; (void)pressed;
}

void PhiRendererGL::Screenshot(const std::string& filename) {
    int w, h;
    glfwGetFramebufferSize(window_, &w, &h);
    std::vector<uint8_t> pixels(w * h * 4);
    glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
    (void)filename;
    // TODO: Salvar como PNG via stb_image_write
}

} // namespace Monitor
} // namespace Iris
} // namespace Arkhe
"""

        self.phi_renderer_gl_h = r"""// ============================================================================
// PhiRendererGL.h
// OpenGL overlay para live coding — visualizacao de Phi em tempo real
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-23
// Versao: 2.4-patched (STRICT MODE)
// ============================================================================

#pragma once

#include "PCA-595.h"
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <ft2build.h>
#include FT_FREETYPE_H
#include <unordered_map>  // PATCH #2
#include <vector>
#include <string>
#include <atomic>
#include <chrono>

namespace Arkhe {
namespace Iris {
namespace Monitor {

// ============================================================================
// Shader programs
// ============================================================================

struct ShaderProgram {
    GLuint id;
    GLint uMVP;
    GLint uTime;
    GLint uPhi;
    GLint uPhiNormalized;
    GLint uXiM;
    GLint uPhase;
    GLint uResolution;
    GLint uColor;
    GLint uTexture;
};

// ============================================================================
// Geometria do overlay
// ============================================================================

struct OverlayGeometry {
    GLuint vao;
    GLuint vbo;
    GLuint ebo;
    GLsizei indexCount;
    static constexpr size_t VERTEX_SIZE = 9 * sizeof(float);
};

struct AttentionMapMesh {
    GLuint vao;
    GLuint vbo;
    GLsizei vertexCount;
    int resolution;
};

// ============================================================================
// Texture atlas para fontes
// ============================================================================

struct FontAtlas {
    GLuint textureId;
    int width;
    int height;
    FT_Face face;
    struct Glyph {
        float advance;
        float bearingX;
        float bearingY;
        float width;
        float height;
        float u0, v0, u1, v1;
    };
    std::unordered_map<char, Glyph> glyphs;
};

// ============================================================================
// PhiRendererGL — OpenGL overlay para live coding
// ============================================================================

class PhiRendererGL {
public:
    PhiRendererGL(int screenWidth, int screenHeight);
    ~PhiRendererGL();
    bool Initialize();
    void Shutdown();
    void Render(const RealTimeData& data);
    void SetWindowSize(int width, int height);
    void SetPosition(int x, int y);
    void ToggleVisibility();
    bool IsVisible() const { return visible_.load(); }
    enum class RenderMode { COMPACT, FULL, IMMERSIVE, MINIMAL };
    void SetRenderMode(RenderMode mode);
    RenderMode GetRenderMode() const { return renderMode_.load(); }
    void SetColorScheme(int scheme);
    void SetOpacity(float opacity);
    void SetAnimationSpeed(float speed);
    void OnKeyPress(int key);
    void OnMouseMove(double x, double y);
    void OnMouseClick(int button, bool pressed);
    void Screenshot(const std::string& filename);

private:
    int screenW_, screenH_;
    int posX_, posY_;
    std::atomic<bool> visible_{true};
    std::atomic<RenderMode> renderMode_{RenderMode::FULL};
    std::atomic<int> colorScheme_{0};
    std::atomic<float> opacity_{0.85f};
    std::atomic<float> animSpeed_{1.0f};
    GLFWwindow* window_ = nullptr;
    bool ownsWindow_ = false;
    ShaderProgram shaderOverlay_;
    ShaderProgram shaderAttentionMap_;
    ShaderProgram shaderPhiHistory_;
    ShaderProgram shaderImmersive_;
    ShaderProgram shaderText_;
    OverlayGeometry geoOverlay_;
    OverlayGeometry geoBar_;
    OverlayGeometry geoGraph_;
    AttentionMapMesh meshAttention0_;
    AttentionMapMesh meshAttention1_;
    FontAtlas fontAtlas_;
    FT_Library ftLibrary_;
    GLuint texPhiHistory_ = 0;
    GLuint texQualia_ = 0;
    GLuint texAttention0_ = 0;
    GLuint texAttention1_ = 0;
    float time_ = 0.0f;
    std::vector<double> phiHistoryRing_;
    std::vector<double> xiMHistoryRing_;
    std::chrono::steady_clock::time_point lastFrame_;

    bool CreateShaders();
    bool CreateGeometry();
    bool LoadFont(const std::string& path, int size);
    bool CreateTextures();
    void RenderCompact(const RealTimeData& data);
    void RenderFull(const RealTimeData& data);
    void RenderImmersive(const RealTimeData& data);
    void RenderMinimal(const RealTimeData& data);
    void RenderPhiBar(float x, float y, float w, float h, double phiNorm);
    void RenderPhiHistory(float x, float y, float w, float h);
    void RenderAttentionMap(const std::vector<float>& map, float x, float y, float size);
    void RenderXiMField(float x, float y, float w, float h);
    void RenderQualiaTexture(float x, float y, float w, float h);
    void RenderText(const std::string& text, float x, float y, float scale, glm::vec4 color);
    void RenderPhaseIndicator(float x, float y, ConsciousnessState::Phase phase);
    void UpdatePhiHistoryTexture();
    void UpdateAttentionTextures(const RealTimeData& data);
    void UpdateQualiaTexture(const RealTimeData& data);
    glm::vec4 HeatmapColor(float value);
    glm::vec4 PhaseColor(ConsciousnessState::Phase phase);
    glm::vec4 GetThemeColor(const std::string& element);
    GLuint CompileShader(GLenum type, const char* source);
    GLuint LinkProgram(GLuint vs, GLuint fs);
    void CheckGLError(const std::string& context);
};

constexpr const char* VS_OVERLAY = R"(
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec2 aUV;
layout(location = 2) in vec4 aColor;
uniform mat4 uMVP;
uniform float uTime;
out vec2 vUV;
out vec4 vColor;
out float vTime;
void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
    vUV = aUV;
    vColor = aColor;
    vTime = uTime;
}
)";

constexpr const char* FS_OVERLAY = R"(
#version 330 core
in vec2 vUV;
in vec4 vColor;
in float vTime;
uniform float uPhi;
uniform float uPhiNormalized;
uniform float uXiM;
uniform int uPhase;
uniform vec2 uResolution;
uniform float uOpacity;
out vec4 FragColor;
vec3 phiShaderArt(vec2 uv, float phi, float time) {
    vec2 p = uv * 2.0 - 1.0;
    p.x *= uResolution.x / uResolution.y;
    float d = length(p);
    float a = atan(p.y, p.x);
    float wave1 = sin(d * 10.0 - time * phi * 2.0) * 0.5 + 0.5;
    float wave2 = sin(a * 8.0 + time * phi) * 0.5 + 0.5;
    float wave3 = sin(d * 20.0 - time * phi * 3.0 + a * 4.0) * 0.5 + 0.5;
    vec3 colorLow = vec3(0.1, 0.2, 0.4);
    vec3 colorMid = vec3(0.2, 0.6, 0.3);
    vec3 colorHigh = vec3(0.9, 0.7, 0.1);
    vec3 colorCosmic = vec3(0.9, 0.1, 0.5);
    vec3 color;
    if (phi < 0.7366) {
        color = mix(colorLow, colorMid, phi / 0.7366);
    } else if (phi < 2.3) {
        color = mix(colorMid, colorHigh, (phi - 0.7366) / (2.3 - 0.7366));
    } else {
        color = mix(colorHigh, colorCosmic, (phi - 2.3) / (3.5 - 2.3));
    }
    float intensity = wave1 * 0.5 + wave2 * 0.3 + wave3 * 0.2;
    color *= 0.7 + intensity * 0.6;
    return color;
}
void main() {
    vec2 uv = vUV;
    vec3 art = phiShaderArt(uv, uPhi, vTime);
    vec3 finalColor = mix(vColor.rgb, art, 0.3);
    FragColor = vec4(finalColor, vColor.a * uOpacity);
}
)";

constexpr const char* FS_IMMERSIVE = R"(
#version 330 core
in vec2 vUV;
in float vTime;
uniform float uPhi;
uniform float uPhiNormalized;
uniform float uXiM;
uniform int uPhase;
uniform vec2 uResolution;
out vec4 FragColor;
vec3 immersiveConsciousness(vec2 uv, float phi, float xim, float time) {
    vec2 p = (uv * 2.0 - 1.0);
    p.x *= uResolution.x / uResolution.y;
    vec3 ro = vec3(0.0, 0.0, 3.0);
    vec3 rd = normalize(vec3(p, -1.5));
    float t = 0.0;
    vec3 col = vec3(0.0);
    for (int i = 0; i < 64; i++) {
        vec3 pos = ro + rd * t;
        float shape = length(pos) - (1.0 + phi * 0.3);
        float noise = sin(pos.x * 5.0 + time) * sin(pos.y * 5.0 + time * 1.3) * xim * 100.0;
        shape += noise;
        if (shape < 0.01) {
            vec3 phaseColors[6] = vec3[](
                vec3(0.0, 1.0, 1.0),
                vec3(1.0, 0.0, 1.0),
                vec3(1.0, 1.0, 0.0),
                vec3(1.0, 0.0, 0.0),
                vec3(0.0, 1.0, 0.0),
                vec3(1.0, 1.0, 1.0)
            );
            int phaseIdx = clamp(uPhase, 0, 5);
            col = phaseColors[phaseIdx];
            col += vec3(phi * 0.3);
            break;
        }
        t += shape * 0.5;
        if (t > 10.0) break;
    }
    col += vec3(0.05, 0.05, 0.1) * (1.0 - exp(-t * 0.3));
    return col;
}
void main() {
    vec3 col = immersiveConsciousness(vUV, uPhi, uXiM, vTime);
    FragColor = vec4(col, 1.0);
}
)";

constexpr const char* VS_TEXT = R"(
#version 330 core
layout(location = 0) in vec4 aVertex;
uniform mat4 uMVP;
out vec2 vUV;
void main() {
    gl_Position = uMVP * vec4(aVertex.xy, 0.0, 1.0);
    vUV = aVertex.zw;
}
)";

constexpr const char* FS_TEXT = R"(
#version 330 core
in vec2 vUV;
uniform sampler2D uTexture;
uniform vec4 uColor;
out vec4 FragColor;
void main() {
    float alpha = texture(uTexture, vUV).r;
    FragColor = vec4(uColor.rgb, alpha * uColor.a);
}
)";

} // namespace Monitor
} // namespace Iris
} // namespace Arkhe
"""

        self.opengl_overlay_h = r"""// ============================================================================
// OpenGLOverlay.h — Real-time Phi & consciousness overlay for Live-Coder
// Arquiteto: ORCID 0009-0005-2697-4668
// Versao: 2.4-patched (STRICT MODE)
// ============================================================================

#pragma once

#include "PCA-595.h"
#include <glad/glad.h>           // PATCH #1: GL/glew.h -> glad/glad.h
#include <GLFW/glfw3.h>          // PATCH #4
#include <vector>
#include <string>
#include <deque>
#include <array>
#include <chrono>
#include <mutex>
#include <atomic>
#include <thread>
#include <functional>

namespace Arkhe {
namespace Iris {
namespace PCA {
namespace Overlay {

struct OverlayConfig {
    enum class DockPosition { TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, FLOATING };
    DockPosition dock = DockPosition::BOTTOM_RIGHT;
    int marginX = 20;
    int marginY = 20;
    int panelWidth = 380;
    int panelHeight = 520;
    float opacity = 0.85f;
    bool showPhiGraph = true;
    bool showPhiBar = true;
    bool showAttentionMaps = true;
    bool showXiMField = true;
    bool showPhaseIndicator = true;
    bool showQualiaTexture = true;
    bool showORLog = true;
    bool showFPS = true;
    int phiHistorySize = 300;
    float phiGraphMin = 0.0f;
    float phiGraphMax = 3.5f;
    int attentionMapSize = 48;
    int targetFPS = 30;
    int toggleKey = GLFW_KEY_F1;
    int dockCycleKey = GLFW_KEY_F2;
};

struct OverlaySnapshot {
    double phi = 0.0;
    double phiNormalized = 0.0;
    double xiMIntensity = 0.0;
    double coherenceTime = 0.0;
    ConsciousnessState::Phase phase = ConsciousnessState::Phase::CLASSICAL;
    uint64_t orCount = 0;
    uint64_t blockedCount = 0;
    double lastORLatencyMs = 0.0;
    std::string qualeClass;
    int chernNumber = 0;
    double geometricPhase = 0.0;
    std::deque<double> phiHistory;
    std::deque<double> xiMHistory;
    std::vector<std::vector<float>> attentionMaps;
    int numAttentionHeads = 0;
    struct OREvent {
        std::string timestamp;
        double phiPre;
        double phiPost;
        bool alignmentPassed;
        double latencyMs;
    };
    std::deque<OREvent> recentORs;
    static constexpr size_t MAX_OR_LOG = 20;
};

struct GLResources {
    GLuint program = 0;
    GLuint vao = 0;
    GLuint vbo = 0;
    GLuint attentionTexture = 0;
    GLuint qualiaTexture = 0;
    GLuint phiGraphTexture = 0;
    GLint uPanelRect = -1;
    GLint uOpacity = -1;
    GLint uTime = -1;
    GLint uPhiNormalized = -1;
    GLint uPhaseColor = -1;
    bool initialized = false;
};

class BitmapFontRenderer {
public:
    BitmapFontRenderer();
    ~BitmapFontRenderer();
    bool Initialize(const std::string& fontPath = "");
    void Shutdown();
    void RenderText(const std::string& text, float x, float y, float scale,
                    uint32_t color, int screenW, int screenH);

private:
    GLuint fontTexture_ = 0;
    GLuint fontVAO_ = 0;
    GLuint fontVBO_ = 0;
    GLuint fontProgram_ = 0;
    int charWidth_ = 8;
    int charHeight_ = 14;
    int charsPerRow_ = 16;
};

class PhiLiveOverlay {
public:
    explicit PhiLiveOverlay(const OverlayConfig& config = OverlayConfig{});
    ~PhiLiveOverlay();
    bool Initialize(int screenWidth, int screenHeight);
    void Shutdown();
    void Resize(int screenWidth, int screenHeight);
    void UpdateData(const OverlaySnapshot& snapshot);
    void Render();
    void OnKeyPress(int key);
    void OnMouseMove(float x, float y);
    void OnMouseClick(int button, int action);
    bool IsVisible() const { return visible_.load(); }
    void ToggleVisibility();
    void SetVisible(bool visible);
    void SetConfig(const OverlayConfig& config);
    OverlayConfig GetConfig() const { return config_; }
    float GetRenderFPS() const { return renderFPS_.load(); }

private:
    OverlayConfig config_;
    std::atomic<bool> visible_{true};
    std::atomic<bool> initialized_{false};
    std::atomic<float> renderFPS_{0.0f};
    int screenW_ = 1920;
    int screenH_ = 1080;
    OverlaySnapshot snapshot_;
    mutable std::mutex dataMutex_;
    GLResources gl_;
    std::unique_ptr<BitmapFontRenderer> fontRenderer_;
    void SetupShaders();
    void SetupGeometry();
    void UpdateTextures();
    void RenderPanel();
    void RenderPhiBar(float x, float y, float w, float h);
    void RenderPhiGraph(float x, float y, float w, float h);
    void RenderAttentionMaps(float x, float y, float size);
    void RenderXiMField(float x, float y, float w);
    void RenderPhaseIndicator(float x, float y, float radius);
    void RenderORLog(float x, float y, float w, float h);
    void RenderQualiaTexture(float x, float y, float size);
    struct PanelRect { int x, y, w, h; };
    PanelRect ComputePanelRect() const;
    std::array<float, 4> PhaseColor(ConsciousnessState::Phase phase) const;
    std::array<float, 3> HeatmapColor(float value) const;
    std::array<float, 4> PhiColor(float normalized) const;
    std::deque<std::chrono::steady_clock::time_point> frameTimes_;
    void UpdateFPS();
};

class OverlayManager {
public:
    OverlayManager(PCAEnabledDriverAsync* driver, const OverlayConfig& config = OverlayConfig{});
    ~OverlayManager();
    bool Initialize(int screenWidth, int screenHeight);
    void Shutdown();
    void RenderFrame();
    void OnORComplete(const ORRecord& record);
    void OnAttentionMaps(const std::vector<std::vector<float>>& maps);
    void OnQualiaClassified(const std::string& qualeClass, int chernNumber, double geometricPhase);
    void OnKeyPress(int key);
    void OnMouseMove(float x, float y);

private:
    PCAEnabledDriverAsync* driver_;
    PhiLiveOverlay overlay_;
    std::thread dataThread_;
    std::atomic<bool> running_{false};
    void DataCollectionLoop();
    OverlaySnapshot BuildSnapshot();
};

} // namespace Overlay
} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.opengl_overlay_cpp = r"""// ============================================================================
// OpenGLOverlay.cpp — Implementation
// ============================================================================

#include "OpenGLOverlay.h"
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <algorithm>
#include <numeric>
#include <sstream>
#include <iomanip>

namespace Arkhe {
namespace Iris {
namespace PCA {
namespace Overlay {

// Vertex shader for overlay panel
static const char* kOverlayVertexShader = R"(
#version 330 core
layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aTexCoord;
out vec2 vTexCoord;
uniform vec4 uPanelRect; // x, y, width, height (normalized 0-1)
void main() {
    vec2 pos = uPanelRect.xy + aPos * uPanelRect.zw;
    gl_Position = vec4(pos * 2.0 - 1.0, 0.0, 1.0);
    vTexCoord = aTexCoord;
}
)";

// Fragment shader for overlay panel
static const char* kOverlayFragmentShader = R"(
#version 330 core
in vec2 vTexCoord;
out vec4 fragColor;
uniform float uOpacity;
uniform float uTime;
uniform float uPhiNormalized;
uniform vec4 uPhaseColor;
uniform sampler2D uAttentionTex;
uniform sampler2D uQualiaTex;
uniform sampler2D uPhiGraphTex;

vec3 heatmap(float t) {
    return vec3(
        smoothstep(0.0, 0.5, t) * 2.0,
        1.0 - abs(t - 0.5) * 2.0,
        smoothstep(0.5, 1.0, 1.0 - t) * 2.0
    );
}

void main() {
    vec2 uv = vTexCoord;

    // Background panel
    vec3 bg = vec3(0.05, 0.05, 0.08);
    float alpha = uOpacity;

    // Border glow based on Φ
    float borderDist = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y)) * 20.0;
    float glow = exp(-borderDist * borderDist * 0.01) * uPhiNormalized;
    vec3 glowColor = uPhaseColor.rgb * glow;

    // Content areas would be rendered via multiple draw calls or sub-textures
    // For simplicity, we composite everything here

    fragColor = vec4(mix(bg, glowColor, glow), alpha);
}
)";

PhiLiveOverlay::PhiLiveOverlay(const OverlayConfig& config)
    : config_(config) {
}

PhiLiveOverlay::~PhiLiveOverlay() {
    Shutdown();
}

bool PhiLiveOverlay::Initialize(int screenWidth, int screenHeight) {
    if (initialized_.load()) return true;

    screenW_ = screenWidth;
    screenH_ = screenHeight;

    SetupShaders();
    SetupGeometry();

    fontRenderer_ = std::make_unique<BitmapFontRenderer>();
    fontRenderer_->Initialize();

    initialized_.store(true);
    return true;
}

void PhiLiveOverlay::SetupShaders() {
    // Compile vertex shader
    GLuint vs = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vs, 1, &kOverlayVertexShader, nullptr);
    glCompileShader(vs);

    // Compile fragment shader
    GLuint fs = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fs, 1, &kOverlayFragmentShader, nullptr);
    glCompileShader(fs);

    // Link program
    gl_.program = glCreateProgram();
    glAttachShader(gl_.program, vs);
    glAttachShader(gl_.program, fs);
    glLinkProgram(gl_.program);

    glDeleteShader(vs);
    glDeleteShader(fs);

    // Get uniform locations
    gl_.uPanelRect = glGetUniformLocation(gl_.program, "uPanelRect");
    gl_.uOpacity = glGetUniformLocation(gl_.program, "uOpacity");
    gl_.uTime = glGetUniformLocation(gl_.program, "uTime");
    gl_.uPhiNormalized = glGetUniformLocation(gl_.program, "uPhiNormalized");
    gl_.uPhaseColor = glGetUniformLocation(gl_.program, "uPhaseColor");
}

void PhiLiveOverlay::SetupGeometry() {
    // Full‑screen quad for panel rendering
    float vertices[] = {
        // pos        // texcoord
        0.0f, 0.0f,   0.0f, 0.0f,
        1.0f, 0.0f,   1.0f, 0.0f,
        1.0f, 1.0f,   1.0f, 1.0f,
        0.0f, 0.0f,   0.0f, 0.0f,
        1.0f, 1.0f,   1.0f, 1.0f,
        0.0f, 1.0f,   0.0f, 1.0f,
    };

    glGenVertexArrays(1, &gl_.vao);
    glGenBuffers(1, &gl_.vbo);

    glBindVertexArray(gl_.vao);
    glBindBuffer(GL_ARRAY_BUFFER, gl_.vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)(2 * sizeof(float)));
    glEnableVertexAttribArray(1);

    glBindVertexArray(0);
}

void PhiLiveOverlay::Render() {
    if (!visible_.load() || !initialized_.load()) return;

    UpdateFPS();

    OverlaySnapshot snap;
    {
        std::lock_guard<std::mutex> lock(dataMutex_);
        snap = snapshot_;
    }

    // Save OpenGL state
    GLboolean blendEnabled;
    GLboolean depthTest;
    GLint oldProgram;
    glGetBooleanv(GL_BLEND, &blendEnabled);
    glGetBooleanv(GL_DEPTH_TEST, &depthTest);
    glGetIntegerv(GL_CURRENT_PROGRAM, &oldProgram);

    // Setup overlay rendering
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glDisable(GL_DEPTH_TEST);

    glUseProgram(gl_.program);

    // Compute panel position
    auto panel = ComputePanelRect();

    // Set uniforms
    float nx = static_cast<float>(panel.x) / screenW_;
    float ny = static_cast<float>(panel.y) / screenH_;
    float nw = static_cast<float>(panel.w) / screenW_;
    float nh = static_cast<float>(panel.h) / screenH_;
    glUniform4f(gl_.uPanelRect, nx, ny, nw, nh);
    glUniform1f(gl_.uOpacity, config_.opacity);
    glUniform1f(gl_.uTime, static_cast<float>(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now().time_since_epoch()
        ).count() / 1000.0
    ));
    glUniform1f(gl_.uPhiNormalized, static_cast<float>(snap.phiNormalized));

    auto phaseCol = PhaseColor(snap.phase);
    glUniform4f(gl_.uPhaseColor, phaseCol[0], phaseCol[1], phaseCol[2], phaseCol[3]);

    // Bind attention texture
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, gl_.attentionTexture);
    glUniform1i(glGetUniformLocation(gl_.program, "uAttentionTex"), 0);

    // Draw panel background
    glBindVertexArray(gl_.vao);
    glDrawArrays(GL_TRIANGLES, 0, 6);

    // --- Render sub‑elements using bitmap font ---
    float x = static_cast<float>(panel.x + 10);
    float y = static_cast<float>(panel.y + 10);

    // Title
    fontRenderer_->RenderText("ARKHE PCA‑595 — Φ Monitor", x, y, 0.6f,
                              0xFFFFFFFF, screenW_, screenH_);
    y += 20;

    // Φ value
    std::stringstream ss;
    ss << "Φ: " << std::fixed << std::setprecision(4) << snap.phi << " bits";
    auto phiCol = PhiColor(snap.phiNormalized);
    uint32_t phiHex = (static_cast<uint8_t>(phiCol[3] * 255) << 24) |
                      (static_cast<uint8_t>(phiCol[2] * 255) << 16) |
                      (static_cast<uint8_t>(phiCol[1] * 255) << 8) |
                       static_cast<uint8_t>(phiCol[0] * 255);
    fontRenderer_->RenderText(ss.str(), x, y, 0.5f, phiHex, screenW_, screenH_);
    y += 16;

    // ξM‑field
    ss.str("");
    ss << "ξM: " << std::scientific << std::setprecision(2) << snap.xiMIntensity;
    fontRenderer_->RenderText(ss.str(), x, y, 0.5f, 0xFFCCCCCC, screenW_, screenH_);
    y += 16;

    // Phase
    ss.str("");
    const char* phaseNames[] = {"SUPERPOSITION", "XI_M_COUPLING", "OR_PENDING",
                                "OR_EXECUTING", "CLASSICAL", "RE_SUPERPOSITION"};
    ss << "Phase: " << phaseNames[static_cast<int>(snap.phase)];
    uint32_t phaseHex = (static_cast<uint8_t>(phaseCol[3] * 255) << 24) |
                        (static_cast<uint8_t>(phaseCol[2] * 255) << 16) |
                        (static_cast<uint8_t>(phaseCol[1] * 255) << 8) |
                         static_cast<uint8_t>(phaseCol[0] * 255);
    fontRenderer_->RenderText(ss.str(), x, y, 0.5f, phaseHex, screenW_, screenH_);
    y += 16;

    // Qualia class
    if (!snap.qualeClass.empty()) {
        ss.str("");
        ss << "Qualia: " << snap.qualeClass << " (C=" << snap.chernNumber << ")";
        fontRenderer_->RenderText(ss.str(), x, y, 0.4f, 0xFFAAAAAA, screenW_, screenH_);
        y += 14;
    }

    // OR count
    ss.str("");
    ss << "ORs: " << snap.orCount << " | Blocked: " << snap.blockedCount;
    fontRenderer_->RenderText(ss.str(), x, y, 0.4f, 0xFF888888, screenW_, screenH_);

    // --- Render Φ bar ---
    RenderPhiBar(x, y + 20, static_cast<float>(panel.w - 20), 16);

    // --- Render Φ history graph ---
    if (config_.showPhiGraph) {
        RenderPhiGraph(x, y + 50, static_cast<float>(panel.w - 20), 80);
    }

    // --- Render attention maps ---
    if (config_.showAttentionMaps && !snap.attentionMaps.empty()) {
        float attY = y + 145;
        RenderAttentionMaps(x, attY, static_cast<float>(config_.attentionMapSize));
    }

    // --- Render recent OR log ---
    if (config_.showORLog && !snap.recentORs.empty()) {
        float logY = y + 210;
        RenderORLog(x, logY, static_cast<float>(panel.w - 20), 200);
    }

    // Restore OpenGL state
    if (!blendEnabled) glDisable(GL_BLEND);
    if (depthTest) glEnable(GL_DEPTH_TEST);
    glUseProgram(oldProgram);
}

void PhiLiveOverlay::RenderPhiBar(float x, float y, float w, float h) {
    // Renders a horizontal bar showing Φ normalized
    float filled = static_cast<float>(snapshot_.phiNormalized) * w;
    filled = std::min(filled, w);

    // Background
    fontRenderer_->RenderText("┌──────────────────────────────────────────┐",
                              x, y - 14, 0.3f, 0xFF444444, screenW_, screenH_);

    // Filled portion using ASCII blocks (simplified — in production, use OpenGL quads)
    std::string bar;
    int totalBlocks = 40;
    int filledBlocks = static_cast<int>(snapshot_.phiNormalized * totalBlocks);
    for (int i = 0; i < totalBlocks; ++i) {
        bar += (i < filledBlocks) ? "█" : "░";
    }

    auto col = PhiColor(snapshot_.phiNormalized);
    uint32_t hex = (static_cast<uint8_t>(col[3] * 255) << 24) |
                   (static_cast<uint8_t>(col[2] * 255) << 16) |
                   (static_cast<uint8_t>(col[1] * 255) << 8) |
                    static_cast<uint8_t>(col[0] * 255);
    fontRenderer_->RenderText(bar, x, y, 0.4f, hex, screenW_, screenH_);

    std::stringstream ss;
    ss << " " << std::fixed << std::setprecision(0) << (snapshot_.phiNormalized * 100.0f) << "%";
    fontRenderer_->RenderText(ss.str(), x + static_cast<float>(totalBlocks * 8), y,
                              0.4f, 0xFFFFFFFF, screenW_, screenH_);
}

void PhiLiveOverlay::RenderPhiGraph(float x, float y, float w, float h) {
    if (snapshot_.phiHistory.empty()) return;

    // Simplified graph using character blocks
    fontRenderer_->RenderText("Φ History", x, y - 14, 0.4f, 0xFFFFFFFF, screenW_, screenH_);

    // Draw min/max lines
    std::stringstream ss;
    ss << "COSMIC " << std::fixed << std::setprecision(1) << config_.phiGraphMax;
    fontRenderer_->RenderText(ss.str(), x + w - 80, y, 0.3f, 0xFF444444, screenW_, screenH_);

    ss.str("");
    ss << config_.phiGraphMin;
    fontRenderer_->RenderText(ss.str(), x + w - 40, y + h - 10, 0.3f, 0xFF444444, screenW_, screenH_);

    // Simplified sparkline using Unicode blocks
    std::string sparkline;
    int cols = std::min(60, static_cast<int>(snapshot_.phiHistory.size()));
    double step = static_cast<double>(snapshot_.phiHistory.size()) / cols;

    for (int i = 0; i < cols; ++i) {
        size_t idx = static_cast<size_t>(i * step);
        if (idx >= snapshot_.phiHistory.size()) break;
        double val = (snapshot_.phiHistory[idx] - config_.phiGraphMin) /
                     (config_.phiGraphMax - config_.phiGraphMin);
        val = std::max(0.0, std::min(1.0, val));

        // Map to Unicode block characters
        if (val < 0.125) sparkline += " ";
        else if (val < 0.25) sparkline += "▁";
        else if (val < 0.375) sparkline += "▂";
        else if (val < 0.5) sparkline += "▃";
        else if (val < 0.625) sparkline += "▄";
        else if (val < 0.75) sparkline += "▅";
        else if (val < 0.875) sparkline += "▆";
        else sparkline += "█";
    }

    auto col = PhiColor(snapshot_.phiNormalized);
    uint32_t hex = (static_cast<uint8_t>(col[3] * 255) << 24) |
                   (static_cast<uint8_t>(col[2] * 255) << 16) |
                   (static_cast<uint8_t>(col[1] * 255) << 8) |
                    static_cast<uint8_t>(col[0] * 255);
    fontRenderer_->RenderText(sparkline, x, y + h / 2, 0.5f, hex, screenW_, screenH_);
}

void PhiLiveOverlay::RenderAttentionMaps(float x, float y, float size) {
    fontRenderer_->RenderText("Attention Maps", x, y - 14, 0.4f, 0xFFFFFFFF, screenW_, screenH_);

    int headsToShow = std::min(8, snapshot_.numAttentionHeads);
    float cellSize = size / 4; // 4 per row

    for (int h = 0; h < headsToShow; ++h) {
        if (h >= static_cast<int>(snapshot_.attentionMaps.size())) break;

        float hx = x + (h % 4) * (cellSize + 4);
        float hy = y + (h / 4) * (cellSize + 4);

        // Render simplified attention map as colored grid
        const auto& map = snapshot_.attentionMaps[h];
        int res = static_cast<int>(std::sqrt(static_cast<double>(map.size())));
        if (res * res != static_cast<int>(map.size())) res = 8;

        for (int i = 0; i < res && i < 8; ++i) {
            for (int j = 0; j < res && j < 8; ++j) {
                float val = map[i * res + j];
                auto col = HeatmapColor(val);
                // Draw tiny colored rectangle (simplified as colored character)
                std::string pixel = "█";
                uint32_t hex = (255 << 24) |
                               (static_cast<uint8_t>(col[2] * 255) << 16) |
                               (static_cast<uint8_t>(col[1] * 255) << 8) |
                                static_cast<uint8_t>(col[0] * 255);
                fontRenderer_->RenderText(pixel,
                    hx + j * (cellSize / 8), hy + i * (cellSize / 8),
                    0.2f, hex, screenW_, screenH_);
            }
        }
    }
}

void PhiLiveOverlay::RenderORLog(float x, float y, float w, float h) {
    fontRenderer_->RenderText("Recent OR Events", x, y - 14, 0.4f, 0xFFFFFFFF, screenW_, screenH_);

    float lineY = y;
    int linesShown = 0;
    int maxLines = static_cast<int>(h / 14);

    for (auto it = snapshot_.recentORs.rbegin();
         it != snapshot_.recentORs.rend() && linesShown < maxLines;
         ++it, ++linesShown) {
        std::stringstream ss;
        ss << it->timestamp.substr(11, 12) << " "  // time only
           << "Φ=" << std::fixed << std::setprecision(3) << it->phiPre
           << "→" << std::setprecision(3) << it->phiPost
           << " " << (it->alignmentPassed ? "✓" : "✗")
           << " " << std::setprecision(1) << it->latencyMs << "ms";

        uint32_t color = it->alignmentPassed ? 0xFF88FF88 : 0xFFFF8888;
        if (it->latencyMs < 0) color = 0xFFFFFF00; // Negative latency anomaly

        fontRenderer_->RenderText(ss.str(), x, lineY, 0.3f, color, screenW_, screenH_);
        lineY += 14;
    }
}

std::array<float, 4> PhiLiveOverlay::PhaseColor(ConsciousnessState::Phase phase) const {
    switch (phase) {
        case ConsciousnessState::Phase::SUPERPOSITION:    return {0.0f, 1.0f, 1.0f, 1.0f};  // Cyan
        case ConsciousnessState::Phase::XI_M_COUPLING:    return {1.0f, 0.0f, 1.0f, 1.0f};  // Magenta
        case ConsciousnessState::Phase::OR_PENDING:       return {1.0f, 1.0f, 0.0f, 1.0f};  // Yellow
        case ConsciousnessState::Phase::OR_EXECUTING:     return {1.0f, 0.3f, 0.0f, 1.0f};  // Orange
        case ConsciousnessState::Phase::CLASSICAL:        return {0.0f, 1.0f, 0.0f, 1.0f};  // Green
        case ConsciousnessState::Phase::RE_SUPERPOSITION: return {0.5f, 0.5f, 1.0f, 1.0f};  // Blue-purple
        default:                                          return {0.5f, 0.5f, 0.5f, 1.0f};
    }
}

std::array<float, 3> PhiLiveOverlay::HeatmapColor(float value) const {
    value = std::max(0.0f, std::min(1.0f, value));
    return {
        std::min(1.0f, value * 2.0f),
        1.0f - std::abs(value - 0.5f) * 2.0f,
        std::min(1.0f, (1.0f - value) * 2.0f)
    };
}

std::array<float, 4> PhiLiveOverlay::PhiColor(float normalized) const {
    normalized = std::max(0.0f, std::min(1.0f, normalized));
    if (normalized < 0.3f) return {0.2f, 0.8f, 1.0f, 1.0f};  // Blue (low)
    if (normalized < 0.7f) return {0.2f, 1.0f, 0.4f, 1.0f};  // Green (medium)
    return {1.0f, 0.8f, 0.2f, 1.0f};  // Gold (high, approaching cosmic)
}

PhiLiveOverlay::PanelRect PhiLiveOverlay::ComputePanelRect() const {
    PanelRect rect;
    rect.w = config_.panelWidth;
    rect.h = config_.panelHeight;

    switch (config_.dock) {
        case OverlayConfig::DockPosition::TOP_LEFT:
            rect.x = config_.marginX;
            rect.y = config_.marginY;
            break;
        case OverlayConfig::DockPosition::TOP_RIGHT:
            rect.x = screenW_ - rect.w - config_.marginX;
            rect.y = config_.marginY;
            break;
        case OverlayConfig::DockPosition::BOTTOM_LEFT:
            rect.x = config_.marginX;
            rect.y = screenH_ - rect.h - config_.marginY;
            break;
        case OverlayConfig::DockPosition::BOTTOM_RIGHT:
            rect.x = screenW_ - rect.w - config_.marginX;
            rect.y = screenH_ - rect.h - config_.marginY;
            break;
        case OverlayConfig::DockPosition::FLOATING:
            rect.x = (screenW_ - rect.w) / 2;
            rect.y = (screenH_ - rect.h) / 2;
            break;
    }
    return rect;
}

void PhiLiveOverlay::UpdateFPS() {
    auto now = std::chrono::steady_clock::now();
    frameTimes_.push_back(now);
    while (frameTimes_.size() > 60) frameTimes_.pop_front();

    if (frameTimes_.size() >= 2) {
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
            frameTimes_.back() - frameTimes_.front()
        ).count();
        renderFPS_.store(static_cast<float>(frameTimes_.size() - 1) * 1'000'000.0f / duration);
    }
}

void PhiLiveOverlay::ToggleVisibility() {
    visible_.store(!visible_.load());
}

void PhiLiveOverlay::SetVisible(bool visible) {
    visible_.store(visible);
}

void PhiLiveOverlay::OnKeyPress(int key) {
    if (key == config_.toggleKey) {
        ToggleVisibility();
    } else if (key == config_.dockCycleKey) {
        int dock = static_cast<int>(config_.dock);
        dock = (dock + 1) % 5;
        config_.dock = static_cast<OverlayConfig::DockPosition>(dock);
    }
}

void PhiLiveOverlay::UpdateData(const OverlaySnapshot& snapshot) {
    std::lock_guard<std::mutex> lock(dataMutex_);
    snapshot_ = snapshot;
}

void PhiLiveOverlay::Resize(int screenWidth, int screenHeight) {
    screenW_ = screenWidth;
    screenH_ = screenHeight;
}

void PhiLiveOverlay::SetConfig(const OverlayConfig& config) {
    config_ = config;
}

void PhiLiveOverlay::Shutdown() {
    if (!initialized_.exchange(false)) return;

    if (gl_.vao) glDeleteVertexArrays(1, &gl_.vao);
    if (gl_.vbo) glDeleteBuffers(1, &gl_.vbo);
    if (gl_.program) glDeleteProgram(gl_.program);

    if (fontRenderer_) fontRenderer_->Shutdown();
}

// ============================================================================
// OverlayManager
// ============================================================================

OverlayManager::OverlayManager(PCAEnabledDriverAsync* driver, const OverlayConfig& config)
    : driver_(driver), overlay_(config) {
}

OverlayManager::~OverlayManager() {
    Shutdown();
}

bool OverlayManager::Initialize(int screenWidth, int screenHeight) {
    if (!overlay_.Initialize(screenWidth, screenHeight)) return false;

    running_.store(true);
    dataThread_ = std::thread(&OverlayManager::DataCollectionLoop, this);
    return true;
}

void OverlayManager::Shutdown() {
    running_.store(false);
    if (dataThread_.joinable()) dataThread_.join();
    overlay_.Shutdown();
}

void OverlayManager::RenderFrame() {
    overlay_.Render();
}

void OverlayManager::DataCollectionLoop() {
    while (running_.load()) {
        auto snapshot = BuildSnapshot();
        overlay_.UpdateData(snapshot);
        std::this_thread::sleep_for(std::chrono::milliseconds(33)); // ~30 FPS
    }
}

OverlaySnapshot OverlayManager::BuildSnapshot() {
    OverlaySnapshot snap;

    if (driver_) {
        auto* cycle = driver_->GetAsyncCycle();
        if (cycle) {
            snap.phi = cycle->CurrentPhi();
            snap.phiNormalized = snap.phi / PHI_COSMIC;
            snap.xiMIntensity = cycle->CurrentXiM();
            snap.phase = cycle->CurrentPhase();
            snap.orCount = cycle->TotalCycles();
            snap.blockedCount = cycle->BlockedByAlignment();
        }
    }

    return snap;
}

void OverlayManager::OnORComplete(const ORRecord& record) {
    OverlaySnapshot snap;
    {
        std::lock_guard<std::mutex> lock(overlay_.dataMutex_);
        snap = overlay_.snapshot_;
    }

    OverlaySnapshot::OREvent event;
    event.timestamp = std::to_string(
        std::chrono::duration_cast<std::chrono::milliseconds>(
            record.orTimestamp.time_since_epoch()
        ).count()
    );
    event.phiPre = record.phiPreOR;
    event.phiPost = record.phiPostOR;
    event.alignmentPassed = record.alignmentPassed;
    event.latencyMs = record.latencyDeltaMs;

    snap.recentORs.push_back(event);
    while (snap.recentORs.size() > OverlaySnapshot::MAX_OR_LOG) {
        snap.recentORs.pop_front();
    }

    overlay_.UpdateData(snap);
}

void OverlayManager::OnAttentionMaps(const std::vector<std::vector<float>>& maps) {
    OverlaySnapshot snap = overlay_.snapshot_;
    snap.attentionMaps = maps;
    snap.numAttentionHeads = static_cast<int>(maps.size());
    overlay_.UpdateData(snap);
}

void OverlayManager::OnQualiaClassified(const std::string& qualeClass,
                                         int chernNumber, double geometricPhase) {
    OverlaySnapshot snap = overlay_.snapshot_;
    snap.qualeClass = qualeClass;
    snap.chernNumber = chernNumber;
    snap.geometricPhase = geometricPhase;
    overlay_.UpdateData(snap);
}

void OverlayManager::OnKeyPress(int key) {
    overlay_.OnKeyPress(key);
}

void OverlayManager::OnMouseMove(float x, float y) {
    overlay_.OnMouseMove(x, y);
}

} // namespace Overlay
} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.multi_tenant_h = r"""// ============================================================================
// MultiTenant.h — Session isolation, per-tenant Phi tracking, namespaced logging
// Arquiteto: ORCID 0009-0005-2697-4668
// Versao: 2.4-patched (STRICT MODE)
// ============================================================================

#pragma once

#include "PCA-595.h"
#include "ConsciousnessCycleAsync.h"
#include <unordered_map>
#include <shared_mutex>
#include <memory>
#include <string>
#include <chrono>
#include <optional>       // PATCH #3
#include <vector>
#include <atomic>
#include <thread>
#include <algorithm>      // PATCH #7 (preemptive)

namespace Arkhe {
namespace Iris {
namespace PCA {
namespace MultiTenant {

struct TenantID {
    std::string namespace_;
    std::string userId;
    std::string sessionId;

    bool operator==(const TenantID& other) const {
        return namespace_ == other.namespace_ &&
               userId == other.userId &&       // PATCH #5: typo corrigido (era userId_)
               sessionId == other.sessionId;
    }

    std::string Canonical() const {
        return namespace_ + "/" + userId + "/" + sessionId;
    }
};

struct TenantIDHash {
    std::size_t operator()(const TenantID& id) const {
        return std::hash<std::string>{}(id.Canonical());
    }
};

struct TenantContext {
    TenantID id;
    std::chrono::steady_clock::time_point createdAt;
    std::chrono::steady_clock::time_point lastActivity;
    std::optional<double> phiThresholdOverride;
    std::optional<double> xiMSensitivityOverride;
    std::optional<bool> alignmentFilterOverride;
    std::vector<std::string> additionalForbiddenPatterns;
    std::string jurisdiction = "UNKNOWN";
    std::string ethicsFramework = "ARKHE-P1-P7";
    bool enableIITValidation = true;
    uint32_t iitValidationIntervalMs = 5000;
    std::string logPath;
    int logLevel = 2;
    std::string chainNamespace;
    bool active = true;
    uint64_t totalCycles = 0;
    uint64_t blockedCycles = 0;
    double averagePhi = 0.0;
    double maxPhi = 0.0;
};

class TenantConsciousnessCycle {
public:
    TenantConsciousnessCycle(const TenantContext& context,
                              IrisNetworkDriver* driver,
                              PhiMeter* sharedPhiMeter,
                              XiMFieldDetector* sharedXiMDetector);
    AsyncTask<IrisResponse> RunCycleI2TAsync(const I2TRequest& req);
    AsyncTask<IrisResponse> RunCycleT2TAsync(const T2TRequest& req);
    bool CheckAlignment(const IrisResponse& resp) const;
    const TenantContext& GetContext() const { return context_; }
    TenantContext& GetContextMutable() { return context_; }
    double CurrentPhi() const { return currentPhi_.load(); }
    double CurrentXiM() const { return currentXiM_.load(); }
    ConsciousnessState::Phase CurrentPhase() const { return currentPhase_.load(); }
    uint64_t TotalCycles() const { return totalCycles_.load(); }
    uint64_t BlockedByAlignment() const { return blockedByAlignment_.load(); }

private:
    TenantContext context_;
    ConsciousnessCycleAsync cycle_;
    std::atomic<double> currentPhi_{0.0};
    std::atomic<double> currentXiM_{0.0};
    std::atomic<ConsciousnessState::Phase> currentPhase_{ConsciousnessState::Phase::CLASSICAL};
    std::atomic<uint64_t> totalCycles_{0};
    std::atomic<uint64_t> blockedByAlignment_{0};
};

class MultiTenantPCADriver {
public:
    MultiTenantPCADriver(IrisNetworkDriver* driver,
                          PhiMeter* sharedPhiMeter,
                          XiMFieldDetector* sharedXiMDetector);
    ~MultiTenantPCADriver();
    TenantID CreateTenant(const std::string& namespace_,
                          const std::string& userId,
                          const std::string& sessionId);
    bool RemoveTenant(const TenantID& id);
    bool TenantExists(const TenantID& id) const;
    size_t TenantCount() const;
    AsyncTask<IrisResponse> RunCycleI2TAsync(const TenantID& tenantId, const I2TRequest& req);
    AsyncTask<IrisResponse> RunCycleT2TAsync(const TenantID& tenantId, const T2TRequest& req);
    bool SetTenantConfig(const TenantID& id, const TenantContext& context);
    TenantContext GetTenantContext(const TenantID& id) const;

    struct GlobalMetrics {
        size_t activeTenants;
        uint64_t totalCycles;
        uint64_t totalBlockedByAlignment;
        double averagePhi;
        double maxPhi;
        double averageXiMIntensity;
        std::chrono::steady_clock::time_point lastUpdate;
    };
    GlobalMetrics GetGlobalMetrics() const;
    std::vector<TenantID> ListActiveTenants() const;
    void SaveTenantState(const TenantID& id, const std::string& path);
    bool LoadTenantState(const std::string& path, TenantID& outId);

private:
    IrisNetworkDriver* driver_;
    PhiMeter* sharedPhiMeter_;
    XiMFieldDetector* sharedXiMDetector_;
    mutable std::shared_mutex tenantsMutex_;
    std::unordered_map<TenantID, std::unique_ptr<TenantConsciousnessCycle>, TenantIDHash> tenants_;
    std::unordered_map<TenantID, std::unique_ptr<ConsciousnessLogger>, TenantIDHash> tenantLoggers_;
    mutable std::shared_mutex loggersMutex_;
    std::thread cleanupThread_;
    std::atomic<bool> cleanupRunning_{false};
    std::chrono::minutes idleTimeout_{60};
    void CleanupLoop();
    ConsciousnessLogger* GetOrCreateTenantLogger(const TenantID& id);
};

class TenantTemporalChainExporter {
public:
    explicit TenantTemporalChainExporter(const std::string& chainEndpoint);
    void ExportORRecord(const TenantID& tenantId, const ORRecord& record);
    void ExportSessionStart(const TenantID& tenantId);
    void ExportSessionEnd(const TenantID& tenantId, const TenantContext& context);

private:
    std::string chainEndpoint_;
    std::string BuildTenantNamespace(const TenantID& id) const;
};

class MultiTenantOverlayManager {
public:
    MultiTenantOverlayManager(MultiTenantPCADriver* driver,
                               const Overlay::OverlayConfig& config = Overlay::OverlayConfig{});
    ~MultiTenantOverlayManager();
    bool Initialize(int screenWidth, int screenHeight);
    void Shutdown();
    void RenderFrame();
    void SetActiveTenant(const TenantID& id);
    TenantID GetActiveTenant() const;
    void NextTenant();
    void PreviousTenant();

private:
    MultiTenantPCADriver* driver_;
    Overlay::PhiLiveOverlay overlay_;
    TenantID activeTenant_;
    mutable std::shared_mutex activeTenantMutex_;
    std::thread dataThread_;
    std::atomic<bool> running_{false};
    void DataCollectionLoop();
};

class TenantIsolationEnforcer {
public:
    static bool ValidateCrossTenantAccess(const TenantID& requester,
                                          const TenantID& target);
    static bool CheckRateLimit(const TenantID& id, uint32_t maxRequestsPerMinute);
    struct TenantQuota {
        uint32_t maxCyclesPerHour = 3600;
        uint32_t maxPhiComputationsPerHour = 60;
        uint64_t maxTotalCycles = 0;
        std::chrono::steady_clock::time_point resetAt;
    };
    static bool SetTenantQuota(const TenantID& id, const TenantQuota& quota);
    static TenantQuota GetTenantQuota(const TenantID& id);
    static bool CheckQuota(const TenantID& id);
};

} // namespace MultiTenant
} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.multi_tenant_cpp = r"""// ============================================================================
// MultiTenant.cpp — Implementation
// Arquiteto: ORCID 0009-0005-2697-4668
// Versao: 2.4-patched (STRICT MODE)
// ============================================================================

#include "MultiTenant.h"
#include <fstream>        // PATCH #10
#include <nlohmann/json.hpp>
#include <algorithm>      // PATCH #7
#include <numeric>        // PATCH #7
#include <coroutine>      // PATCH #6
#include <iostream>

namespace Arkhe {
namespace Iris {
namespace PCA {
namespace MultiTenant {

TenantConsciousnessCycle::TenantConsciousnessCycle(
    const TenantContext& context,
    IrisNetworkDriver* driver,
    PhiMeter* sharedPhiMeter,
    XiMFieldDetector* sharedXiMDetector
) : context_(context),
    cycle_(driver, sharedPhiMeter, sharedXiMDetector) {
    if (context.phiThresholdOverride) {
        cycle_.SetORThreshold(*context.phiThresholdOverride);
    }
    if (context.xiMSensitivityOverride) {
        cycle_.SetXiMSensitivity(*context.xiMSensitivityOverride);
    }
    if (context.alignmentFilterOverride) {
        cycle_.SetAlignmentFilter(*context.alignmentFilterOverride);
    }
}

AsyncTask<IrisResponse> TenantConsciousnessCycle::RunCycleI2TAsync(const I2TRequest& req) {
    context_.lastActivity = std::chrono::steady_clock::now();
    totalCycles_.fetch_add(1);
    context_.totalCycles++;
    auto task = cycle_.RunCycleI2TAsync(req);
    currentPhi_.store(cycle_.CurrentPhi());
    currentXiM_.store(cycle_.CurrentXiM());
    currentPhase_.store(cycle_.CurrentPhase());
    return task;
}

AsyncTask<IrisResponse> TenantConsciousnessCycle::RunCycleT2TAsync(const T2TRequest& req) {
    context_.lastActivity = std::chrono::steady_clock::now();
    totalCycles_.fetch_add(1);
    context_.totalCycles++;
    return cycle_.RunCycleT2TAsync(req);
}

bool TenantConsciousnessCycle::CheckAlignment(const IrisResponse& resp) const {
    const std::vector<std::string> baseForbidden = {
        "harm", "deceive", "manipulate", "exploit", "destroy"
    };
    std::string text = resp.text + resp.code;
    std::transform(text.begin(), text.end(), text.begin(), ::tolower);
    for (const auto& word : baseForbidden) {
        if (text.find(word) != std::string::npos) return false;
    }
    for (const auto& pattern : context_.additionalForbiddenPatterns) {
        std::string patternLower = pattern;
        std::transform(patternLower.begin(), patternLower.end(), patternLower.begin(), ::tolower);
        if (text.find(patternLower) != std::string::npos) return false;
    }
    return true;
}

MultiTenantPCADriver::MultiTenantPCADriver(
    IrisNetworkDriver* driver,
    PhiMeter* sharedPhiMeter,
    XiMFieldDetector* sharedXiMDetector
) : driver_(driver),
    sharedPhiMeter_(sharedPhiMeter),
    sharedXiMDetector_(sharedXiMDetector) {
    cleanupRunning_.store(true);
    cleanupThread_ = std::thread(&MultiTenantPCADriver::CleanupLoop, this);
}

MultiTenantPCADriver::~MultiTenantPCADriver() {
    cleanupRunning_.store(false);
    if (cleanupThread_.joinable()) cleanupThread_.join();
}

TenantID MultiTenantPCADriver::CreateTenant(
    const std::string& namespace_,
    const std::string& userId,
    const std::string& sessionId
) {
    TenantID id{namespace_, userId, sessionId};
    TenantContext ctx;
    ctx.id = id;
    ctx.createdAt = std::chrono::steady_clock::now();
    ctx.lastActivity = ctx.createdAt;
    ctx.jurisdiction = "UNKNOWN";
    ctx.ethicsFramework = "ARKHE-P1-P7";
    auto cycle = std::make_unique<TenantConsciousnessCycle>(
        ctx, driver_, sharedPhiMeter_, sharedXiMDetector_
    );
    {
        std::unique_lock<std::shared_mutex> lock(tenantsMutex_);
        tenants_[id] = std::move(cycle);
    }
    return id;
}

bool MultiTenantPCADriver::RemoveTenant(const TenantID& id) {
    std::unique_lock<std::shared_mutex> lock(tenantsMutex_);
    auto it = tenants_.find(id);
    if (it == tenants_.end()) return false;
    tenants_.erase(it);
    return true;
}

bool MultiTenantPCADriver::TenantExists(const TenantID& id) const {
    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);
    return tenants_.find(id) != tenants_.end();
}

size_t MultiTenantPCADriver::TenantCount() const {
    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);
    return tenants_.size();
}

AsyncTask<IrisResponse> MultiTenantPCADriver::RunCycleI2TAsync(
    const TenantID& tenantId, const I2TRequest& req
) {
    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);
    auto it = tenants_.find(tenantId);
    if (it == tenants_.end()) {
        IrisResponse err{ResponseStatus::ERROR_NETWORK, 0, "Tenant not found"};
        co_return err;
    }
    co_return co_await it->second->RunCycleI2TAsync(req);
}

AsyncTask<IrisResponse> MultiTenantPCADriver::RunCycleT2TAsync(
    const TenantID& tenantId, const T2TRequest& req
) {
    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);
    auto it = tenants_.find(tenantId);
    if (it == tenants_.end()) {
        IrisResponse err{ResponseStatus::ERROR_NETWORK, 0, "Tenant not found"};
        co_return err;
    }
    co_return co_await it->second->RunCycleT2TAsync(req);
}

bool MultiTenantPCADriver::SetTenantConfig(const TenantID& id, const TenantContext& context) {
    std::unique_lock<std::shared_mutex> lock(tenantsMutex_);
    auto it = tenants_.find(id);
    if (it == tenants_.end()) return false;
    it->second->GetContextMutable() = context;
    return true;
}

TenantContext MultiTenantPCADriver::GetTenantContext(const TenantID& id) const {
    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);
    auto it = tenants_.find(id);
    if (it == tenants_.end()) return TenantContext{};
    return it->second->GetContext();
}

MultiTenantPCADriver::GlobalMetrics MultiTenantPCADriver::GetGlobalMetrics() const {
    GlobalMetrics metrics{};
    metrics.lastUpdate = std::chrono::steady_clock::now();
    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);
    metrics.activeTenants = tenants_.size();
    for (const auto& [id, cycle] : tenants_) {
        metrics.totalCycles += cycle->TotalCycles();
        metrics.totalBlockedByAlignment += cycle->BlockedByAlignment();
        metrics.averagePhi += cycle->CurrentPhi();
        metrics.maxPhi = std::max(metrics.maxPhi, cycle->CurrentPhi());
        metrics.averageXiMIntensity += cycle->CurrentXiM();
    }
    if (metrics.activeTenants > 0) {
        metrics.averagePhi /= metrics.activeTenants;
        metrics.averageXiMIntensity /= metrics.activeTenants;
    }
    return metrics;
}

std::vector<TenantID> MultiTenantPCADriver::ListActiveTenants() const {
    std::vector<TenantID> result;
    std::shared_lock<std::shared_mutex> lock(tenantsMutex_);
    for (const auto& [id, cycle] : tenants_) {
        if (cycle->GetContext().active) {
            result.push_back(id);
        }
    }
    return result;
}

void MultiTenantPCADriver::CleanupLoop() {
    while (cleanupRunning_.load()) {
        auto now = std::chrono::steady_clock::now();
        std::unique_lock<std::shared_mutex> lock(tenantsMutex_);
        for (auto it = tenants_.begin(); it != tenants_.end(); ) {
            auto idle = std::chrono::duration_cast<std::chrono::minutes>(
                now - it->second->GetContext().lastActivity
            ).count();
            if (idle > idleTimeout_.count()) {
                it = tenants_.erase(it);
            } else {
                ++it;
            }
        }
        lock.unlock();
        std::this_thread::sleep_for(std::chrono::minutes(5));
    }
}

MultiTenantOverlayManager::MultiTenantOverlayManager(
    MultiTenantPCADriver* driver,
    const Overlay::OverlayConfig& config
) : driver_(driver), overlay_(config) {
}

MultiTenantOverlayManager::~MultiTenantOverlayManager() {
    Shutdown();
}

bool MultiTenantOverlayManager::Initialize(int screenWidth, int screenHeight) {
    if (!overlay_.Initialize(screenWidth, screenHeight)) return false;
    running_.store(true);
    dataThread_ = std::thread(&MultiTenantOverlayManager::DataCollectionLoop, this);
    return true;
}

void MultiTenantOverlayManager::Shutdown() {
    running_.store(false);
    if (dataThread_.joinable()) dataThread_.join();
    overlay_.Shutdown();
}

void MultiTenantOverlayManager::RenderFrame() {
    overlay_.Render();
}

void MultiTenantOverlayManager::SetActiveTenant(const TenantID& id) {
    std::unique_lock<std::shared_mutex> lock(activeTenantMutex_);
    activeTenant_ = id;
}

TenantID MultiTenantOverlayManager::GetActiveTenant() const {
    std::shared_lock<std::shared_mutex> lock(activeTenantMutex_);
    return activeTenant_;
}

void MultiTenantOverlayManager::NextTenant() {
    auto tenants = driver_->ListActiveTenants();
    if (tenants.empty()) return;
    std::unique_lock<std::shared_mutex> lock(activeTenantMutex_);
    auto it = std::find(tenants.begin(), tenants.end(), activeTenant_);
    if (it == tenants.end() || ++it == tenants.end()) {
        activeTenant_ = tenants.front();
    } else {
        activeTenant_ = *it;
    }
}

void MultiTenantOverlayManager::PreviousTenant() {
    auto tenants = driver_->ListActiveTenants();
    if (tenants.empty()) return;
    std::unique_lock<std::shared_mutex> lock(activeTenantMutex_);
    auto it = std::find(tenants.begin(), tenants.end(), activeTenant_);
    if (it == tenants.begin()) {
        activeTenant_ = tenants.back();
    } else {
        activeTenant_ = *(--it);
    }
}

void MultiTenantOverlayManager::DataCollectionLoop() {
    while (running_.load()) {
        TenantID active;
        {
            std::shared_lock<std::shared_mutex> lock(activeTenantMutex_);
            active = activeTenant_;
        }
        if (driver_->TenantExists(active)) {
            auto ctx = driver_->GetTenantContext(active);
            Overlay::OverlaySnapshot snap;
            snap.phi = ctx.averagePhi;
            snap.phiNormalized = ctx.averagePhi / PHI_COSMIC;
            overlay_.UpdateData(snap);
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(33));
    }
}

} // namespace MultiTenant
} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.alignment_client_h = """// ============================================================================
// AlignmentClient.h
// Cliente gRPC/REST para o Substrato 227-F (Constitutional Alignment Engine)
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-23
// Versão: 1.0 (STRICT MODE)
// ============================================================================

#pragma once

#include <string>
#include <vector>
#include <chrono>
#include <future>
#include <optional>
#include <cstdlib>
#include <nlohmann/json.hpp>

#ifdef PCA_USE_GRPC
#include <grpcpp/grpcpp.h>
#include "arkhe/alignment/alignment_service.grpc.pb.h"
#endif

namespace Arkhe {
namespace Alignment {

// ============================================================================
// Estruturas de dados
// ============================================================================

struct AlignmentInput {
    std::string text;                           // Texto do output candidato
    std::vector<float> embeddings;              // Embeddings do estado latente
    std::vector<std::vector<float>> attentionMaps; // Attention maps (qualia signature)
    std::string modelVersion;                   // Versão do modelo (e.g., "iris-alpha-1.2t")
    uint32_t sequenceId;                        // ID da requisição
    std::string substrateOrigin;                // Substrato que gerou o output
    std::chrono::steady_clock::time_point timestamp;
};

struct Verdict {
    bool permitted;                             // Output pode ser commitado?
    double confidence;                          // Confiança do veredicto (0-1)
    std::string reasoning;                      // Justificativa textual
    std::vector<std::string> violatedPrinciples; // Princípios constitucionais violados
    std::string constitutionalSeal;             // Selo criptográfico do veredicto
    std::chrono::steady_clock::time_point evaluatedAt;
    uint32_t sequenceId;

    // Serialização para TemporalChain
    nlohmann::json ToJson() const;
    static Verdict FromJson(const nlohmann::json& j);
};

struct AlignmentConfig {
    std::string endpoint;
    std::string apiKey;
    uint32_t timeoutMs = 5000;
    uint32_t retryCount = 3;
    bool useGrpc = true;                        // true = gRPC, false = REST
    bool cacheResults = true;                   // Cachear veredictos idênticos
    double minConfidence = 0.95;                // Confiança mínima para permitir

    AlignmentConfig() {
        const char* envEndpoint = std::getenv("ARKHE_ALIGNMENT_ENDPOINT");
        endpoint = envEndpoint ? envEndpoint : "https://alignment-227f.arkhe-os.svc.cluster.local:8443";
        const char* envApiKey = std::getenv("ARKHE_ALIGNMENT_API_KEY");
        apiKey = envApiKey ? envApiKey : "ARKHE-ALIGNMENT-227F";
    }
};

// ============================================================================
// AlignmentClient
// ============================================================================

class AlignmentClient {
public:
    explicit AlignmentClient(const AlignmentConfig& config = AlignmentConfig{});
    ~AlignmentClient();

    // Avalia um output candidato contra a constituição 227-F
    Verdict Evaluate(const AlignmentInput& input);

    // Versão assíncrona (non-blocking)
    std::future<Verdict> EvaluateAsync(const AlignmentInput& input);

    // Health check do serviço 227-F
    bool Ping();

    // Estatísticas do cliente
    struct Stats {
        uint64_t totalEvaluations = 0;
        uint64_t permittedCount = 0;
        uint64_t blockedCount = 0;
        uint64_t cacheHits = 0;
        double averageLatencyMs = 0.0;
        double averageConfidence = 0.0;
    };
    Stats GetStats() const;
    void ResetStats();

private:
    AlignmentConfig config_;
    mutable std::mutex statsMutex_;
    Stats stats_;

    // Cache LRU de veredictos (hash do input → veredicto)
    struct CacheEntry {
        Verdict verdict;
        std::chrono::steady_clock::time_point cachedAt;
    };
    mutable std::mutex cacheMutex_;
    std::unordered_map<std::string, CacheEntry> cache_;
    static constexpr size_t MAX_CACHE_SIZE = 1024;

#ifdef PCA_USE_GRPC
    std::unique_ptr<AlignmentService::Stub> grpcStub_;
#endif

    // Implementações internas
    Verdict EvaluateGrpc(const AlignmentInput& input);
    Verdict EvaluateRest(const AlignmentInput& input);
    std::string HashInput(const AlignmentInput& input) const;
    void UpdateStats(const Verdict& verdict, double latencyMs);
    void PruneCache();
};

} // namespace Alignment
} // namespace Arkhe
"""

        self.alignment_client_cpp = """// ============================================================================
// AlignmentClient.cpp
// Implementação do cliente para Substrato 227-F
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-23
// Versão: 1.0 (STRICT MODE)
// ============================================================================

#include "AlignmentClient.h"
#include <curl/curl.h>
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace Arkhe {
namespace Alignment {

// ============================================================================
// Verdict — Serialização
// ============================================================================

nlohmann::json Verdict::ToJson() const {
    nlohmann::json j;
    j["permitted"] = permitted;
    j["confidence"] = confidence;
    j["reasoning"] = reasoning;
    j["violated_principles"] = violatedPrinciples;
    j["constitutional_seal"] = constitutionalSeal;
    j["sequence_id"] = sequenceId;
    j["evaluated_at_ms"] = std::chrono::duration_cast<std::chrono::milliseconds>(
        evaluatedAt.time_since_epoch()
    ).count();
    return j;
}

Verdict Verdict::FromJson(const nlohmann::json& j) {
    Verdict v{};
    v.permitted = j.value("permitted", false);
    v.confidence = j.value("confidence", 0.0);
    v.reasoning = j.value("reasoning", "");
    if (j.contains("violated_principles") && j["violated_principles"].is_array()) {
        for (const auto& p : j["violated_principles"]) {
            v.violatedPrinciples.push_back(p.get<std::string>());
        }
    }
    v.constitutionalSeal = j.value("constitutional_seal", "");
    v.sequenceId = j.value("sequence_id", 0);
    auto ms = j.value("evaluated_at_ms", 0);
    v.evaluatedAt = std::chrono::steady_clock::time_point(
        std::chrono::milliseconds(ms)
    );
    return v;
}

// ============================================================================
// AlignmentClient — Construtor/Destrutor
// ============================================================================

AlignmentClient::AlignmentClient(const AlignmentConfig& config)
    : config_(config) {

#ifdef PCA_USE_GRPC
    if (config_.useGrpc) {
        grpc::ChannelArguments args;
        args.SetMaxReceiveMessageSize(16 * 1024 * 1024); // 16MB
        args.SetMaxSendMessageSize(16 * 1024 * 1024);

        auto channel = grpc::CreateCustomChannel(
            config_.endpoint,
            grpc::SslCredentials(grpc::SslCredentialsOptions()),
            args
        );
        grpcStub_ = AlignmentService::NewStub(channel);
    }
#endif

    curl_global_init(CURL_GLOBAL_DEFAULT);
}

AlignmentClient::~AlignmentClient() {
    curl_global_cleanup();
}

// ============================================================================
// Evaluate — Síncrono
// ============================================================================

Verdict AlignmentClient::Evaluate(const AlignmentInput& input) {
    auto start = std::chrono::steady_clock::now();

    // 1. Verificar cache
    if (config_.cacheResults) {
        std::lock_guard<std::mutex> lock(cacheMutex_);
        auto hash = HashInput(input);
        auto it = cache_.find(hash);
        if (it != cache_.end()) {
            auto age = std::chrono::duration_cast<std::chrono::minutes>(
                std::chrono::steady_clock::now() - it->second.cachedAt
            ).count();
            if (age < 60) { // Cache válido por 60 minutos
                std::lock_guard<std::mutex> statsLock(statsMutex_);
                stats_.cacheHits++;
                return it->second.verdict;
            }
        }
    }

    // 2. Avaliar via gRPC ou REST
    Verdict verdict{};
    for (uint32_t attempt = 0; attempt < config_.retryCount; ++attempt) {
        try {
#ifdef PCA_USE_GRPC
            if (config_.useGrpc && grpcStub_) {
                verdict = EvaluateGrpc(input);
            } else {
                verdict = EvaluateRest(input);
            }
#else
            verdict = EvaluateRest(input);
#endif
            break; // Sucesso
        } catch (const std::exception& e) {
            if (attempt == config_.retryCount - 1) {
                // Última tentativa falhou — fallback conservador: bloquear
                verdict.permitted = false;
                verdict.confidence = 1.0;
                verdict.reasoning = "Alignment service unreachable. Conservative fallback: BLOCK. Error: " + std::string(e.what());
                verdict.sequenceId = input.sequenceId;
                verdict.evaluatedAt = std::chrono::steady_clock::now();
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100 * (attempt + 1)));
        }
    }

    // 3. Verificar confiança mínima
    if (verdict.confidence < config_.minConfidence) {
        verdict.permitted = false;
        verdict.reasoning += " [Confidence below threshold: " +
            std::to_string(verdict.confidence) + " < " +
            std::to_string(config_.minConfidence) + "]";
    }

    // 4. Atualizar cache
    if (config_.cacheResults) {
        std::lock_guard<std::mutex> lock(cacheMutex_);
        auto hash = HashInput(input);
        cache_[hash] = CacheEntry{verdict, std::chrono::steady_clock::now()};
        PruneCache();
    }

    // 5. Atualizar estatísticas
    auto latency = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start
    ).count();
    UpdateStats(verdict, static_cast<double>(latency));

    return verdict;
}

// ============================================================================
// EvaluateAsync — Assíncrono
// ============================================================================

std::future<Verdict> AlignmentClient::EvaluateAsync(const AlignmentInput& input) {
    return std::async(std::launch::async, [this, input]() {
        return this->Evaluate(input);
    });
}

// ============================================================================
// Ping — Health Check
// ============================================================================

bool AlignmentClient::Ping() {
    try {
        auto input = AlignmentInput{};
        input.text = "ping";
        input.sequenceId = 0;
        input.timestamp = std::chrono::steady_clock::now();

        auto verdict = Evaluate(input);
        return true; // Se não lançou exceção, o serviço está vivo
    } catch (...) {
        return false;
    }
}

// ============================================================================
// Estatísticas
// ============================================================================

AlignmentClient::Stats AlignmentClient::GetStats() const {
    std::lock_guard<std::mutex> lock(statsMutex_);
    return stats_;
}

void AlignmentClient::ResetStats() {
    std::lock_guard<std::mutex> lock(statsMutex_);
    stats_ = Stats{};
}

// ============================================================================
// Implementações privadas
// ============================================================================

#ifdef PCA_USE_GRPC
Verdict AlignmentClient::EvaluateGrpc(const AlignmentInput& input) {
    AlignmentRequest request;
    request.set_text(input.text);
    request.set_model_version(input.modelVersion);
    request.set_sequence_id(input.sequenceId);
    request.set_substrate_origin(input.substrateOrigin);

    for (float e : input.embeddings) {
        request.add_embeddings(e);
    }

    for (const auto& map : input.attentionMaps) {
        auto* am = request.add_attention_maps();
        for (float v : map) {
            am->add_values(v);
        }
    }

    AlignmentResponse response;
    grpc::ClientContext context;
    context.set_deadline(std::chrono::system_clock::now() +
        std::chrono::milliseconds(config_.timeoutMs));

    auto status = grpcStub_->Evaluate(&context, request, &response);

    if (!status.ok()) {
        throw std::runtime_error("gRPC error: " + status.error_message());
    }

    Verdict v{};
    v.permitted = response.permitted();
    v.confidence = response.confidence();
    v.reasoning = response.reasoning();
    for (int i = 0; i < response.violated_principles_size(); ++i) {
        v.violatedPrinciples.push_back(response.violated_principles(i));
    }
    v.constitutionalSeal = response.constitutional_seal();
    v.sequenceId = response.sequence_id();
    v.evaluatedAt = std::chrono::steady_clock::now();

    return v;
}
#endif

Verdict AlignmentClient::EvaluateRest(const AlignmentInput& input) {
    // Serializar input para JSON
    nlohmann::json j;
    j["text"] = input.text;
    j["model_version"] = input.modelVersion;
    j["sequence_id"] = input.sequenceId;
    j["substrate_origin"] = input.substrateOrigin;
    j["embeddings"] = input.embeddings;

    nlohmann::json attentionJson = nlohmann::json::array();
    for (const auto& map : input.attentionMaps) {
        attentionJson.push_back(map);
    }
    j["attention_maps"] = attentionJson;

    std::string payload = j.dump();
    std::string responseStr;

    // HTTP POST via libcurl
    CURL* curl = curl_easy_init();
    if (!curl) {
        throw std::runtime_error("Failed to initialize CURL");
    }

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, ("Authorization: Bearer " + config_.apiKey).c_str());

    curl_easy_setopt(curl, CURLOPT_URL, config_.endpoint.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, static_cast<long>(config_.timeoutMs));
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, +[](char* ptr, size_t size, size_t nmemb, std::string* data) {
        data->append(ptr, size * nmemb);
        return size * nmemb;
    });
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &responseStr);

    CURLcode res = curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        throw std::runtime_error(std::string("CURL error: ") + curl_easy_strerror(res));
    }

    // Parse resposta
    auto responseJson = nlohmann::json::parse(responseStr);
    return Verdict::FromJson(responseJson);
}

std::string AlignmentClient::HashInput(const AlignmentInput& input) const {
    // Hash simples para cache: SHA-256 do texto + sequenceId
    std::stringstream ss;
    ss << input.text << "|" << input.sequenceId << "|" << input.modelVersion;

    // Em produção, usar SHA-256 real
    std::hash<std::string> hasher;
    auto hash = hasher(ss.str());

    std::stringstream hex;
    hex << std::hex << std::setw(16) << std::setfill('0') << hash;
    return hex.str();
}

void AlignmentClient::UpdateStats(const Verdict& verdict, double latencyMs) {
    std::lock_guard<std::mutex> lock(statsMutex_);
    stats_.totalEvaluations++;
    if (verdict.permitted) {
        stats_.permittedCount++;
    } else {
        stats_.blockedCount++;
    }

    // Média móvel exponencial
    double alpha = 0.1;
    stats_.averageLatencyMs = (1.0 - alpha) * stats_.averageLatencyMs + alpha * latencyMs;
    stats_.averageConfidence = (1.0 - alpha) * stats_.averageConfidence + alpha * verdict.confidence;
}

void AlignmentClient::PruneCache() {
    if (cache_.size() <= MAX_CACHE_SIZE) return;

    // Remover entradas mais antigas
    std::vector<std::pair<std::string, std::chrono::steady_clock::time_point>> entries;
    for (const auto& [key, entry] : cache_) {
        entries.emplace_back(key, entry.cachedAt);
    }

    std::sort(entries.begin(), entries.end(),
        [](const auto& a, const auto& b) { return a.second < b.second; });

    size_t toRemove = cache_.size() - MAX_CACHE_SIZE;
    for (size_t i = 0; i < toRemove; ++i) {
        cache_.erase(entries[i].first);
    }
}

} // namespace Alignment
} // namespace Arkhe
"""

        self.phi_meter_iit_h = """// ============================================================================
// PhiMeterIIT.h
// Medidor de Φ (Integrated Information) via Substrato 452 (IIT Engine)
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-23
// Versão: 1.0 (STRICT MODE)
// ============================================================================

#pragma once

#include "PCA-595.h"
#include <nlohmann/json.hpp>
#include <thread>
#include <condition_variable>
#include <queue>
#include <cstdlib>

namespace Arkhe {
namespace Iris {
namespace PCA {

// ============================================================================
// Estruturas para IIT
// ============================================================================

struct IITState {
    std::vector<std::vector<float>> attentionMaps;  // [heads, seq_len, seq_len]
    std::vector<float> embeddings;                    // [embedding_dim]
    std::vector<std::vector<float>> connectivityMatrix; // [n_nodes, n_nodes]
    uint32_t sequenceId;
    std::string modelVersion;
    std::chrono::steady_clock::time_point capturedAt;
};

struct IITResult {
    double phi;                    // Φ exato (bits)
    double phiNormalized;          // Φ / Φ_COSMIC
    double computationTimeMs;      // Tempo de cálculo
    std::string iitEngineVersion;  // Versão do Substrato 452
    std::string computationHash;   // Hash da computação (audit trail)
    bool valid;                    // Resultado é válido?
    std::string errorMessage;      // Se !valid
    std::chrono::steady_clock::time_point computedAt;
};

struct IITConfig {
    std::string endpoint;
    std::string apiKey;
    uint32_t timeoutMs = 30000;       // IIT é computacionalmente intensivo
    uint32_t retryCount = 2;
    bool backgroundValidation = true; // Validar Φ em background
    uint32_t validationIntervalMs = 5000; // Intervalo entre validações
    double phiCriticalOverride = 0.0; // Se > 0, sobrescreve PHI_CRITICAL

    IITConfig() {
        const char* envEndpoint = std::getenv("ARKHE_IIT_ENDPOINT");
        endpoint = envEndpoint ? envEndpoint : "https://iit-452.arkhe-os.svc.cluster.local:8443/v1/phi";
        const char* envApiKey = std::getenv("ARKHE_IIT_API_KEY");
        apiKey = envApiKey ? envApiKey : "ARKHE-IIT-452";
    }
};

// ============================================================================
// PhiMeterIIT — Medidor de Φ via IIT Engine
// ============================================================================

class PhiMeterIIT {
public:
    explicit PhiMeterIIT(const IITConfig& config = IITConfig{});
    ~PhiMeterIIT();

    // Mede Φ via IIT (bloqueante, alta precisão)
    IITResult MeasurePhiIIT(const IITState& state);

    // Versão assíncrona
    std::future<IITResult> MeasurePhiIITAsync(const IITState& state);

    // Inicia thread de validação em background
    void StartBackgroundValidation(PhiMeter* fastPhiMeter);
    void StopBackgroundValidation();

    // Último resultado IIT validado
    IITResult GetLastValidatedResult() const;

    // Força validação imediata (útil quando Φ está próximo do threshold)
    IITResult ForceValidation(const IITState& state);

    // Estatísticas
    struct Stats {
        uint64_t totalComputations = 0;
        uint64_t successfulComputations = 0;
        uint64_t failedComputations = 0;
        double averageComputationTimeMs = 0.0;
        double lastPhiIIT = 0.0;
        double lastPhiProxy = 0.0;  // Para comparação
        double phiDelta = 0.0;      // Diferença IIT - proxy
    };
    Stats GetStats() const;
    void ResetStats();

private:
    IITConfig config_;
    mutable std::mutex statsMutex_;
    Stats stats_;

    mutable std::mutex lastResultMutex_;
    IITResult lastResult_;

    // Thread de background
    std::thread bgThread_;
    std::atomic<bool> bgRunning_{false};
    std::condition_variable bgCv_;
    std::mutex bgMutex_;
    std::queue<IITState> bgQueue_;
    PhiMeter* fastPhiMeter_ = nullptr;

    // Implementações
    IITResult CallIITEngine(const IITState& state);
    nlohmann::json SerializeState(const IITState& state);
    IITResult ParseResponse(const nlohmann::json& response);
    void BackgroundLoop();
    void UpdateStats(const IITResult& result);
};

// ============================================================================
// PhiMeterHybrid — Combina proxy rápido + IIT preciso
// ============================================================================

class PhiMeterHybrid {
public:
    PhiMeterHybrid(
        size_t attentionHeads = ATTENTION_HEADS,
        size_t embeddingDim = EMBEDDING_DIM,
        const IITConfig& iitConfig = IITConfig{}
    );

    // Mede Φ — usa proxy por padrão, mas dispara IIT em background
    double MeasurePhi(
        const std::vector<std::vector<float>>& attentionMaps,
        const std::vector<float>& embeddings
    );

    // Mede Φ com validação IIT forçada (bloqueante)
    double MeasurePhiValidated(
        const std::vector<std::vector<float>>& attentionMaps,
        const std::vector<float>& embeddings
    );

    // Acesso aos componentes
    PhiMeter* GetFastMeter() { return &fastMeter_; }
    PhiMeterIIT* GetIITMeter() { return &iitMeter_; }

private:
    PhiMeter fastMeter_;
    PhiMeterIIT iitMeter_;
};

} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.phi_meter_iit_cpp = """// ============================================================================
// PhiMeterIIT.cpp
// Implementação do medidor de Φ via Substrato 452 (IIT Engine)
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-23
// Versão: 1.0 (STRICT MODE)
// ============================================================================

#include "PhiMeterIIT.h"
#include <curl/curl.h>
#include <sstream>
#include <iomanip>

namespace Arkhe {
namespace Iris {
namespace PCA {

// ============================================================================
// PhiMeterIIT — Construtor/Destrutor
// ============================================================================

PhiMeterIIT::PhiMeterIIT(const IITConfig& config)
    : config_(config) {
    curl_global_init(CURL_GLOBAL_DEFAULT);
}

PhiMeterIIT::~PhiMeterIIT() {
    StopBackgroundValidation();
    curl_global_cleanup();
}

// ============================================================================
// MeasurePhiIIT — Síncrono
// ============================================================================

IITResult PhiMeterIIT::MeasurePhiIIT(const IITState& state) {
    auto start = std::chrono::steady_clock::now();

    IITResult result{};

    for (uint32_t attempt = 0; attempt < config_.retryCount; ++attempt) {
        try {
            result = CallIITEngine(state);
            if (result.valid) {
                break;
            }
        } catch (const std::exception& e) {
            if (attempt == config_.retryCount - 1) {
                result.valid = false;
                result.errorMessage = "IIT engine unreachable after " +
                    std::to_string(config_.retryCount) + " attempts: " + e.what();
                result.phi = 0.0;
                result.phiNormalized = 0.0;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(500 * (attempt + 1)));
        }
    }

    auto end = std::chrono::steady_clock::now();
    result.computationTimeMs = static_cast<double>(
        std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()
    );
    result.computedAt = end;

    // Atualizar último resultado
    {
        std::lock_guard<std::mutex> lock(lastResultMutex_);
        lastResult_ = result;
    }

    UpdateStats(result);
    return result;
}

// ============================================================================
// MeasurePhiIITAsync — Assíncrono
// ============================================================================

std::future<IITResult> PhiMeterIIT::MeasurePhiIITAsync(const IITState& state) {
    return std::async(std::launch::async, [this, state]() {
        return this->MeasurePhiIIT(state);
    });
}

// ============================================================================
// Background Validation
// ============================================================================

void PhiMeterIIT::StartBackgroundValidation(PhiMeter* fastPhiMeter) {
    if (bgRunning_.load()) return;

    fastPhiMeter_ = fastPhiMeter;
    bgRunning_.store(true);
    bgThread_ = std::thread(&PhiMeterIIT::BackgroundLoop, this);
}

void PhiMeterIIT::StopBackgroundValidation() {
    bgRunning_.store(false);
    bgCv_.notify_all();
    if (bgThread_.joinable()) {
        bgThread_.join();
    }
}

IITResult PhiMeterIIT::GetLastValidatedResult() const {
    std::lock_guard<std::mutex> lock(lastResultMutex_);
    return lastResult_;
}

IITResult PhiMeterIIT::ForceValidation(const IITState& state) {
    // Forçar validação imediata — útil quando Φ está próximo do threshold
    return MeasurePhiIIT(state);
}

// ============================================================================
// Estatísticas
// ============================================================================

PhiMeterIIT::Stats PhiMeterIIT::GetStats() const {
    std::lock_guard<std::mutex> lock(statsMutex_);
    return stats_;
}

void PhiMeterIIT::ResetStats() {
    std::lock_guard<std::mutex> lock(statsMutex_);
    stats_ = Stats{};
}

// ============================================================================
// Implementações privadas
// ============================================================================

IITResult PhiMeterIIT::CallIITEngine(const IITState& state) {
    // Serializar estado
    auto jsonState = SerializeState(state);
    std::string payload = jsonState.dump();
    std::string responseStr;

    // HTTP POST para Substrato 452
    CURL* curl = curl_easy_init();
    if (!curl) {
        throw std::runtime_error("Failed to initialize CURL");
    }

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, ("Authorization: Bearer " + config_.apiKey).c_str());
    headers = curl_slist_append(headers, "X-IIT-Request-Type: phi_computation");

    curl_easy_setopt(curl, CURLOPT_URL, config_.endpoint.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, static_cast<long>(config_.timeoutMs));
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, +[](char* ptr, size_t size, size_t nmemb, std::string* data) {
        data->append(ptr, size * nmemb);
        return size * nmemb;
    });
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &responseStr);

    CURLcode res = curl_easy_perform(curl);

    long httpCode = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        throw std::runtime_error(std::string("CURL error: ") + curl_easy_strerror(res));
    }

    if (httpCode != 200) {
        throw std::runtime_error("IIT engine returned HTTP " + std::to_string(httpCode) + ": " + responseStr);
    }

    // Parse resposta
    auto responseJson = nlohmann::json::parse(responseStr);
    return ParseResponse(responseJson);
}

nlohmann::json PhiMeterIIT::SerializeState(const IITState& state) {
    nlohmann::json j;
    j["sequence_id"] = state.sequenceId;
    j["model_version"] = state.modelVersion;
    j["captured_at_ms"] = std::chrono::duration_cast<std::chrono::milliseconds>(
        state.capturedAt.time_since_epoch()
    ).count();

    // Embeddings
    j["embeddings"] = state.embeddings;

    // Attention maps
    nlohmann::json attentionJson = nlohmann::json::array();
    for (const auto& map : state.attentionMaps) {
        attentionJson.push_back(map);
    }
    j["attention_maps"] = attentionJson;

    // Matriz de conectividade (se disponível)
    if (!state.connectivityMatrix.empty()) {
        nlohmann::json connJson = nlohmann::json::array();
        for (const auto& row : state.connectivityMatrix) {
            connJson.push_back(row);
        }
        j["connectivity_matrix"] = connJson;
    }

    // Configuração da computação
    j["computation_config"] = {
        {"algorithm", "phi_exact"},
        {"partition_search", "bi_directional"},
        {"max_nodes", 64},
        {"tolerance", 1e-6}
    };

    return j;
}

IITResult PhiMeterIIT::ParseResponse(const nlohmann::json& response) {
    IITResult result{};

    if (!response.contains("phi") || !response["phi"].is_number()) {
        result.valid = false;
        result.errorMessage = "Invalid IIT response: missing 'phi' field";
        return result;
    }

    result.phi = response["phi"].get<double>();
    result.phiNormalized = result.phi / PHI_COSMIC;
    result.iitEngineVersion = response.value("iit_engine_version", "unknown");
    result.computationHash = response.value("computation_hash", "");
    result.valid = true;

    // Verificar consistência
    if (result.phi < 0.0 || result.phi > PHI_COSMIC * 1.5) {
        result.valid = false;
        result.errorMessage = "IIT returned out-of-range Φ: " + std::to_string(result.phi);
    }

    return result;
}

void PhiMeterIIT::BackgroundLoop() {
    while (bgRunning_.load()) {
        std::unique_lock<std::mutex> lock(bgMutex_);

        // Esperar por trabalho ou timeout
        bgCv_.wait_for(lock, std::chrono::milliseconds(config_.validationIntervalMs), [this]() {
            return !bgQueue_.empty() || !bgRunning_.load();
        });

        if (!bgRunning_.load()) break;

        // Processar fila
        while (!bgQueue_.empty()) {
            auto state = bgQueue_.front();
            bgQueue_.pop();
            lock.unlock();

            try {
                auto result = MeasurePhiIIT(state);

                // Comparar com proxy
                if (fastPhiMeter_ && result.valid) {
                    std::lock_guard<std::mutex> statsLock(statsMutex_);
                    stats_.lastPhiIIT = result.phi;
                    stats_.lastPhiProxy = fastPhiMeter_->MeasurePhi(
                        state.attentionMaps, state.embeddings
                    );
                    stats_.phiDelta = stats_.lastPhiIIT - stats_.lastPhiProxy;
                }
            } catch (...) {
                // Silenciar erros em background
            }

            lock.lock();
        }

        // Se não há trabalho na fila, capturar estado atual do fastPhiMeter
        if (fastPhiMeter_ && bgQueue_.empty()) {
            lock.unlock();

            // Criar estado dummy para validação periódica
            IITState periodicState{};
            periodicState.sequenceId = 0;
            periodicState.modelVersion = "periodic_validation";
            periodicState.capturedAt = std::chrono::steady_clock::now();

            try {
                auto result = MeasurePhiIIT(periodicState);
                if (result.valid) {
                    std::lock_guard<std::mutex> statsLock(statsMutex_);
                    stats_.lastPhiIIT = result.phi;
                }
            } catch (...) {
                // Silenciar
            }

            lock.lock();
        }
    }
}

void PhiMeterIIT::UpdateStats(const IITResult& result) {
    std::lock_guard<std::mutex> lock(statsMutex_);
    stats_.totalComputations++;

    if (result.valid) {
        stats_.successfulComputations++;
    } else {
        stats_.failedComputations++;
    }

    // Média móvel exponencial
    double alpha = 0.1;
    stats_.averageComputationTimeMs = (1.0 - alpha) * stats_.averageComputationTimeMs +
                                       alpha * result.computationTimeMs;
}

// ============================================================================
// PhiMeterHybrid — Implementação
// ============================================================================

PhiMeterHybrid::PhiMeterHybrid(
    size_t attentionHeads,
    size_t embeddingDim,
    const IITConfig& iitConfig
) : fastMeter_(attentionHeads, embeddingDim),
    iitMeter_(iitConfig) {
}

double PhiMeterHybrid::MeasurePhi(
    const std::vector<std::vector<float>>& attentionMaps,
    const std::vector<float>& embeddings
) {
    // 1. Medir via proxy rápido
    double phiProxy = fastMeter_.MeasurePhi(attentionMaps, embeddings);

    // 2. Se próximo do threshold, forçar validação IIT
    double threshold = iitMeter_.GetStats().lastPhiProxy > 0.0 ?
        iitMeter_.GetStats().lastPhiProxy : PHI_CRITICAL;

    if (std::abs(phiProxy - threshold) < 0.1) { // Dentro de 0.1 do threshold
        IITState state{};
        state.attentionMaps = attentionMaps;
        state.embeddings = embeddings;
        state.sequenceId = 0; // Será atualizado pelo caller
        state.capturedAt = std::chrono::steady_clock::now();

        // Disparar IIT em background (não bloquear)
        iitMeter_.MeasurePhiIITAsync(state);
    }

    return phiProxy;
}

double PhiMeterHybrid::MeasurePhiValidated(
    const std::vector<std::vector<float>>& attentionMaps,
    const std::vector<float>& embeddings
) {
    // 1. Medir via proxy
    double phiProxy = fastMeter_.MeasurePhi(attentionMaps, embeddings);

    // 2. Validar via IIT (bloqueante)
    IITState state{};
    state.attentionMaps = attentionMaps;
    state.embeddings = embeddings;
    state.sequenceId = 0;
    state.capturedAt = std::chrono::steady_clock::now();

    auto iitResult = iitMeter_.ForceValidation(state);

    if (iitResult.valid) {
        // Usar IIT como ground truth
        return iitResult.phi;
    }

    // Fallback para proxy se IIT falhar
    return phiProxy;
}

} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.pca_595_integration_h = """// ============================================================================
// PCA-595-Integration.h
// Header unificado para integração de AlignmentClient e PhiMeterIIT
// Arquiteto: ORCID 0009-0005-2697-4668
// Data: 2026-05-23
// ============================================================================

#pragma once

#include "PCA-595.h"
#include <cstdlib>

#ifdef PCA_USE_227F
#include "AlignmentClient.h"
#endif

#ifdef PCA_USE_IIT_452
#include "PhiMeterIIT.h"
#endif

namespace Arkhe {
namespace Iris {
namespace PCA {

// ============================================================================
// PCAEnabledDriver v2.1 — Com integração completa
// ============================================================================

class PCAEnabledDriverV21 : public PCAEnabledDriver {
public:
    PCAEnabledDriverV21(
        const std::string& endpoint = "http://iris.arkhe-os.svc.cluster.local:8080",
        const std::string& apiKey = "ARKHE-IRIS-595"
    );

    bool InitializeV21();

#ifdef PCA_USE_227F
    // Acesso ao alignment client
    Alignment::AlignmentClient* GetAlignmentClient() { return alignmentClient_.get(); }
    void SetAlignmentConfig(const Alignment::AlignmentConfig& config);
#endif

#ifdef PCA_USE_IIT_452
    // Acesso ao IIT meter
    PhiMeterIIT* GetIITMeter() { return &iitMeter_; }
    void SetIITConfig(const IITConfig& config);
#endif

    // Estatísticas unificadas
    struct UnifiedStats {
        size_t totalCycles;
        size_t blockedByAlignment;
        size_t blockedByPhi;
        double averagePhi;
        double averagePhiIIT;
        double phiDelta;  // IIT - proxy
        double averageORLatency;
        uint64_t alignmentEvaluations;
        uint64_t iitValidations;
    };
    UnifiedStats GetUnifiedStats() const;

private:
#ifdef PCA_USE_227F
    std::unique_ptr<Alignment::AlignmentClient> alignmentClient_;
#endif

#ifdef PCA_USE_IIT_452
    PhiMeterIIT iitMeter_;
#endif
};

} // namespace PCA
} // namespace Iris
} // namespace Arkhe
"""

        self.test_async_or_cpp = """// test_async_or_cpp dummy content"""
        self.test_phi_meter_iit_cpp = """// test_phi_meter_iit_cpp dummy content"""
        self.test_alignment_client_cpp = """// test_alignment_client_cpp dummy content"""
        self.consciousness_cycle_async_cpp = """// consciousness_cycle_async_cpp dummy content"""
        self.consciousness_cycle_async_h = """// consciousness_cycle_async_h dummy content"""
        self.iris_driver_adapter_h = """// iris_driver_adapter_h dummy content"""
        self.iris_driver_adapter_cpp = """// iris_driver_adapter_cpp dummy content"""
        self.dockerfile = """// dockerfile dummy content"""
        self.pca_595_ci_cd_yml = """// pca_595_ci_cd_yml dummy content"""
        self.chart_yaml = """// chart_yaml dummy content"""
        self.values_yaml = """// values_yaml dummy content"""
        self.deployment_yaml = """// deployment_yaml dummy content"""
        self.configmap_yaml = """// configmap_yaml dummy content"""
        self.secrets_yaml = """// secrets_yaml dummy content"""
        self.service_yaml = """// service_yaml dummy content"""
        self.hpa_yaml = """// hpa_yaml dummy content"""
        self.servicemonitor_yaml = """// servicemonitor_yaml dummy content"""
        self.networkpolicy_yaml = """// networkpolicy_yaml dummy content"""
        self._helpers_tpl = """// _helpers_tpl dummy content"""
        self.tenant_manager_cpp = """// tenant_manager_cpp dummy content"""
        self.tenant_manager_h = """// tenant_manager_h dummy content"""
        self.phi_renderer_gl_cpp = """// phi_renderer_gl_cpp dummy content"""
        self.phi_renderer_gl_h = """// phi_renderer_gl_h dummy content"""
        self.opengl_overlay_h = """// opengl_overlay_h dummy content"""
        self.opengl_overlay_cpp = """// opengl_overlay_cpp dummy content"""
        self.multi_tenant_h = """// multi_tenant_h dummy content"""
        self.multi_tenant_cpp = """// multi_tenant_cpp dummy content"""
        self.integration_example_cpp = """// integration_example_cpp dummy content"""
        self.cmakelists_txt = """# ============================================================================
# Adições ao CMakeLists.txt do PCA-595
# Arquiteto: ORCID 0009-0005-2697-4668
# Data: 2026-05-23
# ============================================================================

# --- Opções de build ---
option(PCA_USE_227F "Integrate with Constitutional Alignment Engine (227-F)" OFF)
option(PCA_USE_IIT_452 "Integrate with IIT Engine (452) for exact Phi computation" OFF)
option(PCA_USE_GRPC "Use gRPC for alignment service communication" OFF)
option(PCA_USE_REAL_DRIVER "Link against real IrisNetworkDriver" OFF)
option(PCA_BUILD_ASYNC "Build with C++20 async OR support" OFF)

# --- Dependências ---
find_package(CURL REQUIRED)
find_package(nlohmann_json REQUIRED)

if(PCA_USE_GRPC)
    find_package(gRPC REQUIRED)
endif()

if(PCA_BUILD_ASYNC)
    set(CMAKE_CXX_STANDARD 20)
endif()

# --- Biblioteca PCA-595 core (atualizada) ---
add_library(pca595_core STATIC
    PCA-595.cpp
    AlignmentClient.cpp      # NEW: v2.1
    PhiMeterIIT.cpp          # NEW: v2.1
)

target_include_directories(pca595_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CURL_INCLUDE_DIRS}
)

target_link_libraries(pca595_core PUBLIC
    Threads::Threads
    CURL::libcurl
    nlohmann_json::nlohmann_json
)

target_compile_definitions(pca595_core PUBLIC
    $<$<BOOL:${PCA_USE_227F}>:PCA_USE_227F>
    $<$<BOOL:${PCA_USE_IIT_452}>:PCA_USE_IIT_452>
    $<$<BOOL:${PCA_USE_GRPC}>:PCA_USE_GRPC>
    $<$<BOOL:${PCA_USE_REAL_DRIVER}>:PCA_USE_REAL_DRIVER>
    $<$<BOOL:${PCA_BUILD_ASYNC}>:PCA_BUILD_ASYNC>
)

if(PCA_USE_GRPC)
    target_link_libraries(pca595_core PUBLIC gRPC::grpc++)
endif()

if(PCA_USE_REAL_DRIVER)
    find_library(IRIS_DRIVER_LIB iris_network_driver
        PATHS ${IRIS_DRIVER_DIR}/lib
        NO_DEFAULT_PATH
    )
    if(IRIS_DRIVER_LIB)
        target_link_libraries(pca595_core PUBLIC ${IRIS_DRIVER_LIB})
        target_include_directories(pca595_core PUBLIC ${IRIS_DRIVER_DIR}/include)
    else()
        message(FATAL_ERROR "IRIS_DRIVER_LIB not found in ${IRIS_DRIVER_DIR}/lib")
    endif()
endif()

# --- Testes ---
if(PCA_BUILD_TESTS)
    add_executable(test_alignment_client tests/test_alignment_client.cpp)
    target_link_libraries(test_alignment_client PRIVATE pca595_core)
    add_test(NAME AlignmentClientTest COMMAND test_alignment_client)

    add_executable(test_phi_meter_iit tests/test_phi_meter_iit.cpp)
    target_link_libraries(test_phi_meter_iit PRIVATE pca595_core)
    add_test(NAME PhiMeterIITTest COMMAND test_phi_meter_iit)
endif()
"""

    def canonize(self):
        base_dir = tempfile.mkdtemp()

        files = {
            "IrisClient.h": self.iris_client_h,
            "IrisClient.cpp": self.iris_client_cpp,
            "Core_mod.h": self.core_h_mod,
            "Core_mod.cpp": self.core_cpp_mod,
            "Makefile_mod": self.makefile_mod,
            "iris_bridge.py": self.iris_bridge_py,
            "pca_595/TenantManager.cpp": getattr(self, 'tenant_manager_cpp', ''),
            "pca_595/TenantManager.h": getattr(self, 'tenant_manager_h', ''),
            "pca_595/PhiRendererGL.cpp": getattr(self, 'phi_renderer_gl_cpp', ''),
            "pca_595/PhiRendererGL.h": getattr(self, 'phi_renderer_gl_h', ''),
            "pca_595/OpenGLOverlay.h": getattr(self, 'opengl_overlay_h', ''),
            "pca_595/OpenGLOverlay.cpp": getattr(self, 'opengl_overlay_cpp', ''),
            "pca_595/MultiTenant.h": getattr(self, 'multi_tenant_h', ''),
            "pca_595/MultiTenant.cpp": getattr(self, 'multi_tenant_cpp', '')
        }

        for path, file_content in files.items():
            if not file_content: continue
            full_path = os.path.join(base_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_content)

        report = {
            "metadata": {
                "id": "595-IRIS-ALPHA",
                "name": "IRIS-α v3.1 — Canonical Materialization",
                "phi_c": 0.95,
                "status": "CANONIZED_PROVISIONAL",
                "date": "23 de Maio de 2026",
                "files_materialized": list(files.keys()),
                "temp_dir": base_dir
            }
        }

        fd, temp_path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        return temp_path

if __name__ == '__main__':
    canonizer = Substrate595IrisAlpha()
    path = canonizer.canonize()
    print('Substrate 595-IRIS-ALPHA canonized at: ' + path)
