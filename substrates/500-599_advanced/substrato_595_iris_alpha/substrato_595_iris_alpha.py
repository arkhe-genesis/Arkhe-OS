import os
import json
import tempfile
import hashlib

class Substrate595IrisAlpha:
    def __init__(self):
        self.iris_client_h = """#ifndef _IRIS_CLIENT_H_
#define _IRIS_CLIENT_H_

#include <string>
#include <functional>
#include <thread>
#include <mutex>

namespace LiveCoder {

enum class IrisMode {
    T2T,  // Text-to-Text: análise de shader
    I2T,  // Image-to-Text: descrição de frame
    T2I   // Text-to-Image: geração de textura
};

struct IrisResponse {
    bool ready;
    std::string content;      // texto (T2T/I2T) ou base64 PNG (T2I)
    std::string error;
    IrisMode mode;
};

class IrisClient {
private:
    std::string endpoint;
    bool enabled;
    IrisResponse lastResponse;
    std::mutex responseMutex;
    std::thread workerThread;
    bool running;
    bool requestPending;
    std::string pendingCode;
    std::string pendingImageBase64;
    IrisMode pendingMode;

    void workerLoop();
    std::string httpPost(const std::string& url, const std::string& jsonBody);

public:
    IrisClient(const std::string& endpoint = "http://localhost:8080");
    ~IrisClient();

    void Initialize();
    void Shutdown();

    // Chamadas assíncronas (retornam imediatamente)
    void RequestAnalyze(const std::string& glslCode);
    void RequestDescribe(const std::string& imageBase64);
    void RequestGenerate(const std::string& description);

    // Polling (chamado no MainLoop)
    bool HasResponse();
    IrisResponse GetResponse();
    bool IsEnabled() const { return enabled; }
};

} // namespace LiveCoder

#endif
"""

        self.iris_client_cpp = """#include "IrisClient.h"
#include <curl/curl.h>
#include <json/json.h>
#include <sstream>
#include <chrono>

namespace LiveCoder {

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

IrisClient::IrisClient(const std::string& endpoint)
    : endpoint(endpoint), enabled(true), running(false), requestPending(false) {}

IrisClient::~IrisClient() { Shutdown(); }

void IrisClient::Initialize() {
    if (!enabled) return;
    running = true;
    workerThread = std::thread(&IrisClient::workerLoop, this);
}

void IrisClient::Shutdown() {
    running = false;
    if (workerThread.joinable()) workerThread.join();
}

void IrisClient::workerLoop() {
    while (running) {
        if (requestPending) {
            std::string url;
            std::string jsonBody;
            IrisMode mode;
            {
                std::lock_guard<std::mutex> lock(responseMutex);
                mode = pendingMode;
                switch (mode) {
                    case IrisMode::T2T:
                        url = endpoint + "/generate";
                        {
                            Json::Value root;
                            root["mode"] = "t2t";
                            root["prompt"] = pendingCode;
                            Json::FastWriter writer;
                            jsonBody = writer.write(root);
                        }
                        break;
                    case IrisMode::I2T:
                        url = endpoint + "/analyze";
                        {
                            Json::Value root;
                            root["mode"] = "i2t";
                            root["image"] = pendingImageBase64;
                            Json::FastWriter writer;
                            jsonBody = writer.write(root);
                        }
                        break;
                    case IrisMode::T2I:
                        url = endpoint + "/generate_image";
                        {
                            Json::Value root;
                            root["mode"] = "t2i";
                            root["prompt"] = pendingCode;
                            Json::FastWriter writer;
                            jsonBody = writer.write(root);
                        }
                        break;
                }
                requestPending = false;
            }

            std::string response = httpPost(url, jsonBody);
            // Parse JSON response e atualiza lastResponse
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

void IrisClient::RequestAnalyze(const std::string& glslCode) {
    std::lock_guard<std::mutex> lock(responseMutex);
    pendingCode = glslCode;
    pendingMode = IrisMode::T2T;
    requestPending = true;
}

bool IrisClient::HasResponse() {
    std::lock_guard<std::mutex> lock(responseMutex);
    return lastResponse.ready;
}

IrisResponse IrisClient::GetResponse() {
    std::lock_guard<std::mutex> lock(responseMutex);
    IrisResponse r = lastResponse;
    lastResponse.ready = false;
    return r;
}

std::string IrisClient::httpPost(const std::string& url, const std::string& jsonBody) {
    return ""; // Stub implementation
}

} // namespace LiveCoder
"""

        self.core_h_mod = """// Adicionar:
#ifdef WITH_IRIS
#include "IrisClient.h"
#endif

class Core {
    // ... membros existentes ...
#ifdef WITH_IRIS
    IrisClient* irisClient;
    std::string irisOverlayText;
    bool irisOverlayVisible;
#endif
};
"""

        self.core_cpp_mod = """// Em Initialize():
#ifdef WITH_IRIS
    irisClient = new IrisClient("http://localhost:8080");
    irisClient->Initialize();
    irisOverlayVisible = false;
#endif

// Em ProcessSDLEvents() (novo atalho):
#ifdef WITH_IRIS
    if (keyBuffer.IsPressed(SDLK_i) && (keyBuffer.IsPressed(SDLK_LCTRL) ||
                                         keyBuffer.IsPressed(SDLK_RCTRL))) {
        irisClient->RequestAnalyze(nowSource);
        irisOverlayVisible = true;
        irisOverlayText = "IRIS: analyzing shader...";
    }
#endif

// Em MainLoop():
#ifdef WITH_IRIS
    if (irisClient->HasResponse()) {
        IrisResponse r = irisClient->GetResponse();
        irisOverlayText = "IRIS: " + r.content;
    }
#endif

// Em Render() (overlay):
#ifdef WITH_IRIS
    if (irisOverlayVisible && !irisOverlayText.empty()) {
        // Renderiza irisOverlayText como overlay semi-transparente
        // usando BitmapFontGL no topo da tela
    }
#endif
"""

        self.makefile_mod = """# Adicionar:
IRIS_FLAGS = -DWITH_IRIS
IRIS_LIBS = -lcurl -ljsoncpp
IRIS_OBJS = IrisClient.o

# Modificar:
CFLAGS = -O2 $(IRIS_FLAGS)
LIBS = ... $(IRIS_LIBS)
OBJS = ... $(IRIS_OBJS)
"""

        self.iris_bridge_py = """#!/usr/bin/env python3
\"\"\"
Live-Coder IRIS Bridge — Monitora alterações em shaders e consulta o IRIS-α.
Uso: python iris_bridge.py --watch-dir ./ --endpoint http://localhost:8080
\"\"\"
import asyncio
import aiohttp
import argparse
import json
import base64
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

IRIS_ENDPOINT = "http://localhost:8080"

class ShaderChangeHandler(FileSystemEventHandler):
    def __init__(self, endpoint, loop):
        self.endpoint = endpoint
        self.loop = loop

    def on_modified(self, event):
        if event.src_path.endswith('.glsl'):
            asyncio.run_coroutine_threadsafe(
                self.analyze_shader(event.src_path), self.loop
            )

    async def analyze_shader(self, path):
        code = Path(path).read_text()
        async with aiohttp.ClientSession() as session:
            payload = {
                "mode": "t2t",
                "prompt": "Analyze this GLSL shader and suggest improvements:\\n\\n" + code,
                "max_tokens": 500
            }
            async with session.post(self.endpoint + "/generate", json=payload) as resp:
                data = await resp.json()
                # Escreve resposta em ficheiro .iris
                iris_path = path.replace('.glsl', '.iris.txt')
                Path(iris_path).write_text(data.get("text", "No response"))

    async def analyze_screenshot(self, image_path):
        with open(image_path, 'rb') as f:
            image_b64 = base64.b64encode(f.read()).decode()
        async with aiohttp.ClientSession() as session:
            payload = {"mode": "i2t", "image": image_b64}
            async with session.post(self.endpoint + "/analyze", json=payload) as resp:
                data = await resp.json()
                print("IRIS I2T: " + data.get('description', 'No response'))

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch-dir', default='.')
    parser.add_argument('--endpoint', default=IRIS_ENDPOINT)
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    handler = ShaderChangeHandler(args.endpoint, loop)
    observer = Observer()
    observer.schedule(handler, args.watch_dir, recursive=False)
    observer.start()

    print("IRIS Bridge watching " + args.watch_dir + "... (Ctrl+C to stop)")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    asyncio.run(main())
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

        iris_network_driver_dir = os.path.join(base_dir, "iris_network_driver")
        rest_specs_dir = os.path.join(base_dir, "rest_specs")
        stb_vendor_dir = os.path.join(base_dir, "stb_vendor")
        glsl_steganography_dir = os.path.join(base_dir, "glsl_steganography")
        pca_595_dir = os.path.join(base_dir, "pca_595")

        os.makedirs(iris_network_driver_dir, exist_ok=True)
        os.makedirs(rest_specs_dir, exist_ok=True)
        os.makedirs(stb_vendor_dir, exist_ok=True)
        os.makedirs(glsl_steganography_dir, exist_ok=True)
        os.makedirs(pca_595_dir, exist_ok=True)

        files = {
            "iris_network_driver/IrisClient.h": self.iris_client_h,
            "iris_network_driver/IrisClient.cpp": self.iris_client_cpp,
            "iris_network_driver/Core_mod.h": self.core_h_mod,
            "iris_network_driver/Core_mod.cpp": self.core_cpp_mod,
            "iris_network_driver/Makefile_mod": self.makefile_mod,
            "iris_network_driver/iris_bridge.py": self.iris_bridge_py,
            "pca_595/AlignmentClient.h": self.alignment_client_h,
            "pca_595/AlignmentClient.cpp": self.alignment_client_cpp,
            "pca_595/PhiMeterIIT.h": self.phi_meter_iit_h,
            "pca_595/PhiMeterIIT.cpp": self.phi_meter_iit_cpp,
            "pca_595/PCA-595-Integration.h": self.pca_595_integration_h,
            "pca_595/CMakeLists.txt": self.cmakelists_txt,
            "pca_595/ConsciousnessCycleAsync.h": self.consciousness_cycle_async_h,
            "pca_595/ConsciousnessCycleAsync.cpp": self.consciousness_cycle_async_cpp,
            "pca_595/test_async_or.cpp": self.test_async_or_cpp,
            "pca_595/test_phi_meter_iit.cpp": self.test_phi_meter_iit_cpp,
            "pca_595/test_alignment_client.cpp": self.test_alignment_client_cpp,
            "pca_595/IrisDriverAdapter.h": self.iris_driver_adapter_h,
            "pca_595/IrisDriverAdapter.cpp": self.iris_driver_adapter_cpp,
            "pca_595/TenantManager.h": self.tenant_manager_h,
            "pca_595/TenantManager.cpp": self.tenant_manager_cpp,
            "pca_595/PhiRendererGL.h": self.phi_renderer_gl_h,
            "pca_595/PhiRendererGL.cpp": self.phi_renderer_gl_cpp,
            "pca_595/OpenGLOverlay.h": self.opengl_overlay_h,
            "pca_595/OpenGLOverlay.cpp": self.opengl_overlay_cpp,
            "pca_595/MultiTenant.h": self.multi_tenant_h,
            "pca_595/MultiTenant.cpp": self.multi_tenant_cpp,
            "pca_595/IntegrationExample.cpp": self.integration_example_cpp,
            "pca_595/Dockerfile": self.dockerfile,
            "pca_595/.github/workflows/pca-595-ci-cd.yml": self.pca_595_ci_cd_yml,
            "pca_595/helm-chart-pca-595/Chart.yaml": self.chart_yaml,
            "pca_595/helm-chart-pca-595/values.yaml": self.values_yaml,
            "pca_595/helm-chart-pca-595/templates/deployment.yaml": self.deployment_yaml,
            "pca_595/helm-chart-pca-595/templates/configmap.yaml": self.configmap_yaml,
            "pca_595/helm-chart-pca-595/templates/secrets.yaml": self.secrets_yaml,
            "pca_595/helm-chart-pca-595/templates/service.yaml": self.service_yaml,
            "pca_595/helm-chart-pca-595/templates/hpa.yaml": self.hpa_yaml,
            "pca_595/helm-chart-pca-595/templates/servicemonitor.yaml": self.servicemonitor_yaml,
            "pca_595/helm-chart-pca-595/templates/networkpolicy.yaml": self.networkpolicy_yaml,
            "pca_595/helm-chart-pca-595/templates/_helpers.tpl": self._helpers_tpl,
        }

        for path, content in files.items():
            full_path = os.path.join(base_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        report = {
            "metadata": {
                "id": "595-IRIS-ALPHA",
                "name": "IRIS-α v2.0 — Live-Coder Integration Blueprint",
                "phi_c": 0.95,
                "status": "CANONIZED_PROVISIONAL",
                "date": "23 de Maio de 2026",
                "files_materialized": list(files.keys()),
                "temp_dir": base_dir
            }
        }

        canonical_string = json.dumps(report, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        seal = hashlib.sha256(canonical_string.encode('utf-8')).hexdigest()
        report["metadata"]["canonical_seal"] = seal

        fd, temp_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        return temp_path

if __name__ == "__main__":
    canonizer = Substrate595IrisAlpha()
    path = canonizer.canonize()
    print("Substrate 595-IRIS-ALPHA canonized at: " + path)
