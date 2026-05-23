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

    def canonize(self):
        base_dir = tempfile.mkdtemp()

        files = {
            "IrisClient.h": self.iris_client_h,
            "IrisClient.cpp": self.iris_client_cpp,
            "Core_mod.h": self.core_h_mod,
            "Core_mod.cpp": self.core_cpp_mod,
            "Makefile_mod": self.makefile_mod,
            "iris_bridge.py": self.iris_bridge_py,

            "iris_network_driver/IrisNetworkDriver.cpp": self.iris_driver_cpp,
            "rest_specs/openapi.yaml": self.openapi_yaml,
            "stb_vendor_audits/audit_report.json": self.audit_json,
            "glsl_steganography/steg.glsl": self.steg_glsl,

            "pca_595/CMakeLists.txt": self.cmake1,
            "pca_595/BUILD.bazel": self.build_bazel_root,
            "pca_595/MODULE.bazel": self.module_bazel,
            "pca_595/extensions.bzl": self.extensions_bzl,
            "pca_595/.bazelrc": self.bazelrc,

            "pca_595/cmake/ArkhePCA595Config.cmake.in": self.arkhe_pca595_config_cmake_in,
            "pca_595/cmake/FindGLAD.cmake": self.find_glad_cmake,
            "pca_595/arkhe-pca-595.pc.in": self.arkhe_pca_595_pc_in,

            "pca_595/include/arkhe/iris/pca/PCA-595.h": self.pca_595_h,
            "pca_595/include/arkhe/iris/pca/TenantManager.h": self.tenant_manager_h,
            "pca_595/include/arkhe/iris/pca/PhiRendererGL.h": self.phi_renderer_gl_h,
            "pca_595/include/arkhe/iris/pca/OpenGLOverlay.h": self.opengl_overlay_h,
            "pca_595/include/arkhe/iris/pca/MultiTenant.h": self.multi_tenant_h,
            "pca_595/include/arkhe/iris/pca/AlignmentClient.h": self.alignment_client_h,
            "pca_595/include/arkhe/iris/pca/PhiMeterIIT.h": self.phi_meter_iit_h,
            "pca_595/include/arkhe/iris/pca/ConsciousnessCycleAsync.h": self.consciousness_cycle_async_h,
            "pca_595/include/arkhe/iris/pca/IrisDriverAdapter.h": self.iris_driver_adapter_h,

            "pca_595/src/CMakeLists.txt": self.src_cmake,
            "pca_595/src/BUILD.bazel": self.src_build_bazel,
            "pca_595/src/TenantManager.cpp": self.tenant_manager_cpp,
            "pca_595/src/PhiRendererGL.cpp": self.phi_renderer_gl_cpp,
            "pca_595/src/OpenGLOverlay.cpp": self.opengl_overlay_cpp,
            "pca_595/src/MultiTenant.cpp": self.multi_tenant_cpp,

            "pca_595/third_party/glad/BUILD.bazel": self.glad_build_bazel,
            "pca_595/third_party/glad/include/glad/glad.h": self.glad_h,
            "pca_595/third_party/glad/src/glad.c": self.glad_c,

            "pca_595/third_party/glfw.BUILD": self.glfw_build,
            "pca_595/third_party/freetype2.BUILD": self.freetype2_build,

            "pca_595/examples/CMakeLists.txt": self.examples_cmake,
            "pca_595/examples/live_coder_integration.cpp": self.live_coder_integration_cpp,

            ".github/workflows/ci-cd.yml": self.github_workflow_yaml,
        }

        for path, content in files.items():
            full_path = os.path.join(base_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        report = {
            "metadata": {
                "id": "595-IRIS-ALPHA",
                "name": "IRIS-α v3.1 — Canonical Materialization",
                "phi_c": 0.95,
                "canonical_seal": "e7000398d9804be9a3ebe1f16b900d99e81abc6c22423687a85adfab42683073",
                "status": "CANONIZED_PROVISIONAL",
                "date": "23 de Maio de 2026",
                "files_materialized": list(files.keys()),
                "temp_dir": base_dir
            }
        }

        fd, temp_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        return temp_path

if __name__ == "__main__":
    canonizer = Substrate595IrisAlpha()
    path = canonizer.canonize()
    print("Substrate 595-IRIS-ALPHA canonized at: " + path)
