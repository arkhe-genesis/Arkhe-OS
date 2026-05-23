import os
import json
import tempfile

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

    def canonize(self):
        base_dir = tempfile.mkdtemp()
        live_coder_dir = os.path.join(base_dir, "Live-Coder-IRIS")
        os.makedirs(live_coder_dir, exist_ok=True)

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
            full_path = os.path.join(live_coder_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_content)

        report = {
            "metadata": {
                "id": "595-IRIS-ALPHA",
                "name": "IRIS-α v2.0 — Live-Coder Integration Blueprint",
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
