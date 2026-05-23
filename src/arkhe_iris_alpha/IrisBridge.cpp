#include "IrisBridge.h"
#include <vector>
#include <sstream>
#include <future>

// Stub implementation for C++ compilation check
namespace LiveCoder {

IrisBridge::IrisBridge(const std::string& ep) : endpoint(ep), apiKey("ARKHE-IRIS-595") {
}

IrisBridge::~IrisBridge() {
}

std::future<IrisResponse> IrisBridge::AnalyzeScreenshot(const std::vector<uint8_t>& pngData,
                                                           const std::string& prompt) {
    return std::async(std::launch::async, [this]() {
        return IrisResponse{true, IrisMode::I2T_VISUAL_ANALYSIS, "Analysis complete", "", "", 0.9f};
    });
}

std::future<IrisResponse> IrisBridge::GenerateGLSL(const std::string& description,
                                                    const std::string& context) {
    return std::async(std::launch::async, [this]() {
        return IrisResponse{true, IrisMode::T2T_GLSL_GENERATE, "Generated", "void main(){}", "", 0.9f};
    });
}

} // namespace LiveCoder
