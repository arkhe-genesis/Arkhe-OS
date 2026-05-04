#include "telemetry.hpp"
#include <iostream>
#include <sstream>
#include <chrono>
#include <random>

static std::string generateUUID() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<> dis(0, 15);
    static const char* digits = "0123456789abcdef";
    std::string uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx";
    for (char& c : uuid) {
        if (c == 'x') c = digits[dis(gen)];
        else if (c == 'y') c = digits[(dis(gen) & 0x3) | 0x8];
    }
    return uuid;
}

Telemetry::Telemetry(const std::string& ep) : endpoint(ep) {
    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();
}

Telemetry::~Telemetry() {
    if (curl) curl_easy_cleanup(curl);
    curl_global_cleanup();
}

size_t Telemetry::writeCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    // Ignora a resposta, mas precisa consumir os dados
    return size * nmemb;
}

bool Telemetry::sendEvent(const std::string& action,
                          const std::string& monsterType,
                          int x, int y) {
    if (!curl) return false;

    json event;
    event["event_id"] = generateUUID();
    event["action_type"] = action;
    if (!monsterType.empty()) {
        event["monster_type"] = monsterType;
    }
    event["target"]["entity_type"] = "MONSTER";
    event["target"]["entity_id"] = "terminal_entity_" + std::to_string(x) + "_" + std::to_string(y);
    event["position"]["x"] = x;
    event["position"]["y"] = y;
    event["position"]["z"] = 0;

    std::string payload = event.dump();

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "Authorization: Bearer mock_terminal_token");

    curl_easy_setopt(curl, CURLOPT_URL, endpoint.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);

    CURLcode res = curl_easy_perform(curl);
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);

    // Sucesso se 2xx (especialmente 202)
    return (res == CURLE_OK && http_code >= 200 && http_code < 300);
}
