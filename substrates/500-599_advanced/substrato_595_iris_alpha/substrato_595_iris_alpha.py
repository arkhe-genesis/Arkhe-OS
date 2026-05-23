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
        }

        for path, content in files.items():
            full_path = os.path.join(live_coder_dir, path)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

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
