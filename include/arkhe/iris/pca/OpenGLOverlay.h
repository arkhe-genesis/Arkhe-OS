// ============================================================================
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
