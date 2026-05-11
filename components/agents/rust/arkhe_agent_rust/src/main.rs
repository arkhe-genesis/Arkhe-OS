use std::io::{self, BufRead};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

#[derive(Deserialize)]
struct Request {
    jsonrpc: String,
    id: Option<Value>,
    method: String,
    #[serde(default)]
    params: Value,
}

#[derive(Serialize)]
struct Response {
    jsonrpc: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    id: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<Error>,
}

#[derive(Serialize)]
struct Error {
    code: i32,
    message: String,
}

fn main() {
    let stdin = io::stdin();
    for line in stdin.lock().lines() {
        let input = line.unwrap_or_default();
        if input.is_empty() { continue; }

        let req: Request = match serde_json::from_str(&input) {
            Ok(r) => r,
            Err(_) => continue,
        };

        if req.id.is_none() {
            continue;
        }

        let id = req.id.clone();

        if req.method == "initialize" {
            let res = json!({
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "arkhe_agent_rust", "version": "1.0.0"}
            });
            println!("{}", serde_json::to_string(&Response { jsonrpc: "2.0".to_string(), id, result: Some(res), error: None }).unwrap());
        } else if req.method == "tools/list" {
            let res = json!({
                "tools": [
                    {"name": "read_problem", "description": "Reads problem statement.", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
                    {"name": "generate_solution", "description": "Generates solution.", "inputSchema": {"type": "object", "properties": {"language": {"type": "string"}, "constraints": {"type": "string"}}, "required": ["language", "constraints"]}},
                    {"name": "validate_against_examples", "description": "Validates code against examples.", "inputSchema": {"type": "object", "properties": {"input": {"type": "string"}, "expected": {"type": "string"}}, "required": ["input", "expected"]}},
                    {"name": "submit_to_codeforces", "description": "Submits code to Codeforces.", "inputSchema": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}}
                ]
            });
            println!("{}", serde_json::to_string(&Response { jsonrpc: "2.0".to_string(), id, result: Some(res), error: None }).unwrap());
        } else if req.method == "tools/call" {
            let res = json!({
                "content": [{"type": "text", "text": "Action executed successfully in Rust Agent"}],
                "isError": false
            });
            println!("{}", serde_json::to_string(&Response { jsonrpc: "2.0".to_string(), id, result: Some(res), error: None }).unwrap());
        } else {
            let err = Error { code: -32601, message: "Method not found".to_string() };
            println!("{}", serde_json::to_string(&Response { jsonrpc: "2.0".to_string(), id, result: None, error: Some(err) }).unwrap());
        }
    }
}
