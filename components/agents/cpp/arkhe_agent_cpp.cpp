#include <iostream>
#include <string>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

int main() {
    std::string input;
    while (std::getline(std::cin, input)) {
        if (input.empty()) continue;

        try {
            json req = json::parse(input);
            if (!req.contains("id") || req["id"].is_null()) continue; // Ignore notifications

            json id = req["id"];
            std::string method = req.value("method", "");

            json resp;
            resp["jsonrpc"] = "2.0";
            resp["id"] = id;

            if (method == "initialize") {
                resp["result"] = {
                    {"protocolVersion", "2024-11-05"},
                    {"capabilities", {{"tools", json::object()}}},
                    {"serverInfo", {{"name", "arkhe_agent_cpp"}, {"version", "1.0.0"}}}
                };
            } else if (method == "tools/list") {
                resp["result"] = {
                    {"tools", {
                        {{"name", "read_problem"}, {"description", "Reads problem statement."}, {"inputSchema", {{"type", "object"}, {"properties", {{"url", {{"type", "string"}}}}}, {"required", {"url"}}}}},
                        {{"name", "generate_solution"}, {"description", "Generates solution."}, {"inputSchema", {{"type", "object"}, {"properties", {{"language", {{"type", "string"}}}, {"constraints", {{"type", "string"}}}}}, {"required", {"language", "constraints"}}}}},
                        {{"name", "validate_against_examples"}, {"description", "Validates code against examples."}, {"inputSchema", {{"type", "object"}, {"properties", {{"input", {{"type", "string"}}}, {"expected", {{"type", "string"}}}}}, {"required", {"input", "expected"}}}}},
                        {{"name", "submit_to_codeforces"}, {"description", "Submits code to Codeforces."}, {"inputSchema", {{"type", "object"}, {"properties", {{"code", {{"type", "string"}}}}}, {"required", {"code"}}}}}
                    }}
                };
            } else if (method == "tools/call") {
                resp["result"] = {
                    {"content", {{{"type", "text"}, {"text", "Action executed successfully in C++ Agent"}}}},
                    {"isError", false}
                };
            } else {
                resp["error"] = {{"code", -32601}, {"message", "Method not found"}};
            }
            std::cout << resp.dump() << "\n";
        } catch (...) {
            continue;
        }
    }
    return 0;
}
