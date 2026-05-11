package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
)

// Minimal valid JSON-RPC 2.0 MCP server for Arkhe Go Agent

type Request struct {
	Jsonrpc string          `json:"jsonrpc"`
	Id      interface{}     `json:"id"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

type Response struct {
	Jsonrpc string      `json:"jsonrpc"`
	Id      interface{} `json:"id"`
	Result  interface{} `json:"result,omitempty"`
	Error   *Error      `json:"error,omitempty"`
}

type Error struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		line := scanner.Text()
		var req Request
		if err := json.Unmarshal([]byte(line), &req); err != nil {
			continue // Ignore parsing errors to stay minimal
		}

		// Handle notifications (no ID)
		if req.Id == nil {
			continue
		}

		var result interface{}

		if req.Method == "initialize" {
			result = map[string]interface{}{
				"protocolVersion": "2024-11-05",
				"capabilities":    map[string]interface{}{"tools": map[string]interface{}{}},
				"serverInfo":      map[string]interface{}{"name": "arkhe_agent_go", "version": "1.0.0"},
			}
		} else if req.Method == "tools/list" {
			result = map[string]interface{}{
				"tools": []map[string]interface{}{
					{
						"name": "read_problem",
						"description": "Reads problem statement.",
						"inputSchema": map[string]interface{}{
							"type": "object", "properties": map[string]interface{}{"url": map[string]interface{}{"type": "string"}}, "required": []string{"url"},
						},
					},
					{
						"name": "generate_solution",
						"description": "Generates solution.",
						"inputSchema": map[string]interface{}{
							"type": "object", "properties": map[string]interface{}{"language": map[string]interface{}{"type": "string"}, "constraints": map[string]interface{}{"type": "string"}}, "required": []string{"language", "constraints"},
						},
					},
					{
						"name": "validate_against_examples",
						"description": "Validates code against examples.",
						"inputSchema": map[string]interface{}{
							"type": "object", "properties": map[string]interface{}{"input": map[string]interface{}{"type": "string"}, "expected": map[string]interface{}{"type": "string"}}, "required": []string{"input", "expected"},
						},
					},
					{
						"name": "submit_to_codeforces",
						"description": "Submits code to Codeforces.",
						"inputSchema": map[string]interface{}{
							"type": "object", "properties": map[string]interface{}{"code": map[string]interface{}{"type": "string"}}, "required": []string{"code"},
						},
					},
				},
			}
		} else if req.Method == "tools/call" {
			result = map[string]interface{}{
				"content": []map[string]interface{}{
					{"type": "text", "text": "Action executed successfully in Go Agent"},
				},
				"isError": false,
			}
		} else {
			resp := Response{
				Jsonrpc: "2.0",
				Id:      req.Id,
				Error:   &Error{Code: -32601, Message: "Method not found"},
			}
			jsonResp, _ := json.Marshal(resp)
			fmt.Println(string(jsonResp))
			continue
		}

		resp := Response{
			Jsonrpc: "2.0",
			Id:      req.Id,
			Result:  result,
		}
		jsonResp, _ := json.Marshal(resp)
		fmt.Println(string(jsonResp))
	}
}
