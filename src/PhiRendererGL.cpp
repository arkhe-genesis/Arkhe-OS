// ============================================================================
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
    if (geoText_.vao) glDeleteVertexArrays(1, &geoText_.vao);
    if (geoText_.vbo) glDeleteBuffers(1, &geoText_.vbo);
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

    glBindVertexArray(geoText_.vao);

    float xPos = x;
    for (char c : text) {
        auto it = fontAtlas_.glyphs.find(c);
        if (it == fontAtlas_.glyphs.end()) continue;
        const auto& glyph = it->second;
        float x0 = xPos + glyph.bearingX * scale;
        float y0 = y - glyph.bearingY * scale;
        float x1 = x0 + glyph.width * scale;
        float y1 = y0 + glyph.height * scale;

        float vertices[6][4] = {
            { x0, y1,   glyph.u0, glyph.v1 },
            { x0, y0,   glyph.u0, glyph.v0 },
            { x1, y0,   glyph.u1, glyph.v0 },

            { x0, y1,   glyph.u0, glyph.v1 },
            { x1, y0,   glyph.u1, glyph.v0 },
            { x1, y1,   glyph.u1, glyph.v1 }
        };

        glBindBuffer(GL_ARRAY_BUFFER, geoText_.vbo);
        glBufferSubData(GL_ARRAY_BUFFER, 0, sizeof(vertices), vertices);
        glBindBuffer(GL_ARRAY_BUFFER, 0);
        glDrawArrays(GL_TRIANGLES, 0, 6);

        xPos += glyph.advance * scale;
    }
    glBindVertexArray(0);
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

    // Text geometry setup
    glGenVertexArrays(1, &geoText_.vao);
    glGenBuffers(1, &geoText_.vbo);
    glBindVertexArray(geoText_.vao);
    glBindBuffer(GL_ARRAY_BUFFER, geoText_.vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(float) * 6 * 4, NULL, GL_DYNAMIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 4 * sizeof(float), 0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindVertexArray(0);

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
