#!/usr/bin/env python3
"""
Canonizer for ARKHE OS Substrate 595 PCA Patches & CI/CD.
"""

import os
import json
import hashlib
import tempfile
import sys

def get_phi_renderer_gl_h():
    return r'''// ============================================================================
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
'''

def get_multi_tenant_h():
    return r'''// ============================================================================
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
'''

def get_opengl_overlay_h():
    return r'''// ============================================================================
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
'''

def get_multi_tenant_cpp():
    return r'''// ============================================================================
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
'''

def get_phi_renderer_gl_cpp():
    return r'''// ============================================================================
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
'''

def get_ci_cd_yml():
    return """name: Build PCA-595

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build_cmake:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        build_type: [Release, Debug]
        sanitizer: [none, asan, tsan]
    steps:
    - uses: actions/checkout@v4
    - name: Configure CMake
      run: >
        cmake -B build
        -DCMAKE_BUILD_TYPE=${{ matrix.build_type }}
        -DARKHE_USE_ASAN=${{ matrix.sanitizer == 'asan' && 'ON' || 'OFF' }}
        -DARKHE_USE_TSAN=${{ matrix.sanitizer == 'tsan' && 'ON' || 'OFF' }}
    - name: Build
      run: cmake --build build --parallel 4

  build_bazel:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        config: [opt, dbg, asan, tsan]
    steps:
    - uses: actions/checkout@v4
    - name: Build with Bazel
      run: bazel build //... -c ${{ matrix.config }}
"""

def canonize():
    work_dir = tempfile.mkdtemp()

    files = {
        "include/arkhe/iris/pca/PhiRendererGL.h": get_phi_renderer_gl_h(),
        "include/arkhe/iris/pca/MultiTenant.h": get_multi_tenant_h(),
        "include/arkhe/iris/pca/OpenGLOverlay.h": get_opengl_overlay_h(),
        "src_patched/MultiTenant.cpp": get_multi_tenant_cpp(),
        "src_patched/PhiRendererGL.cpp": get_phi_renderer_gl_cpp(),
        ".github/workflows/ci-cd.yml": get_ci_cd_yml()
    }

    canonical_string = ""

    for filename, content in sorted(files.items()):
        file_path = os.path.join(work_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        canonical_string += content

    seal = hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()

    report = {
        "substrate_id": "595-PCA-PATCHES",
        "description": "PCA-595 Patches & CI/CD Pipeline Canonical Integration",
        "work_dir": work_dir,
        "files_generated": list(files.keys()),
        "canonical_seal": seal,
        "status": "CANONIZED"
    }

    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report

if __name__ == "__main__":
    canonize()
