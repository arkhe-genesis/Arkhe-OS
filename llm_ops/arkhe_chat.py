#!/usr/bin/env python3
"""
ARKHE-OS Chat CLI
Conecta-se ao servidor llama-server local e fornece uma interface conversacional.
"""

import argparse
import json
import urllib.request
import urllib.error

def chat(prompt, host="http://localhost:8080"):
    url = f"{host}/completion"

    data = {
        "prompt": prompt,
        "n_predict": 128,
        "temperature": 0.3,
        "top_k": 40,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "stop": ["<|ARKHE_END|>", "User:", "\n\n"]
    }

    headers = {
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("content", "").strip()
    except urllib.error.URLError as e:
        return f"[Erro] Não foi possível conectar ao servidor ARKHE-OS em {host}: {e}"

def main():
    parser = argparse.ArgumentParser(description="ARKHE-OS Chat CLI")
    parser.add_argument("--host", default="http://localhost:8080", help="URL do servidor ARKHE-OS")
    args = parser.parse_args()

    print("============================================================")
    print("  ARKHE-OS Chat CLI")
    print("  Digite 'sair' ou 'exit' para encerrar.")
    print("============================================================")

    while True:
        try:
            user_input = input("\nUser> ")
            if user_input.strip().lower() in ['sair', 'exit', 'quit']:
                break

            if not user_input.strip():
                continue

            prompt = f"<|ARKHE_START|>\nUser: {user_input}\nARKHE-OS:"

            print("ARKHE-OS> ", end="", flush=True)
            response = chat(prompt, host=args.host)
            print(response)

        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando...")
            break

if __name__ == "__main__":
    main()
