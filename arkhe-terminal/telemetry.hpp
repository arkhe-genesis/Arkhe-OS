#ifndef TELEMETRY_HPP
#define TELEMETRY_HPP

#include <string>
#include <curl/curl.h>
#include "json.hpp"

using json = nlohmann::json;

class Telemetry {
public:
    Telemetry(const std::string& endpoint);
    ~Telemetry();

    // Envia um evento de jogo (action_type, monster_type, position)
    // Retorna true se obteve 202 Accepted, false caso contrário.
    bool sendEvent(const std::string& action,
                   const std::string& monsterType,
                   int x, int y);

private:
    std::string endpoint;
    CURL* curl;
    static size_t writeCallback(void* contents, size_t size, size_t nmemb, void* userp);
};

#endif
