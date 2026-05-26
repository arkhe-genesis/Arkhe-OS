#!/usr/bin/env python3
"""
arkhe_assistant.py — Arkhe Assistant: Interface conversacional canonica
Integracao: Substrato 836 (ARKHE-GGUF-QUANTIZER) + 824 (MAGALU-CLOUD-BRIDGE)
Arquiteto: ORCID 0009-0005-2697-4668

Este modulo implementa o "Arkhe Assistant" — um agente conversacional
que serve como interface primaria entre usuarios e a Catedral ARKHE.
O assistant carrega arkhe.gguf via llama.cpp e responde em formato
canonico, com validacao de invariantes e selos SHA3-256.
"""

import os
import json
import hashlib
import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ARKHE-ASSISTANT")

# ============================================================
# 1. CONFIGURACAO CANONICA DO ASSISTANT
# ============================================================

@dataclass
class ArkheAssistantConfig:
    model_path: str = "./arkhe-gguf-output/arkhe-8b-Q4_K_M.gguf"
    llama_cpp_path: str = "./llama.cpp/build/bin/llama-cli"
    context_length: int = 32768
    max_tokens: int = 4096
    temperature: float = 0.3
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1

    # Identidade canonica
    assistant_name: str = "Arkhe Assistant"
    arkhe_version: str = "inf.Omega"
    architect_orcid: str = "0009-0005-2697-4668"
    cathedral_uri: str = "https://arkhe.cathedral"

    # Validacao
    require_seal: bool = True
    verify_invariants: bool = True
    phi_c_min: float = 0.998

    # Integracao
    sagemaker_proxy_url: str = "http://localhost:8242"
    vk_provider_url: str = "http://localhost:10250"
    temporal_chain_anchor: bool = True

# ============================================================
# 2. MOTOR DE INFERENCIA CANONICA
# ============================================================

class ArkheInferenceEngine:
    """Motor de inferencia que orquestra llama.cpp com constraints canonicas."""

    def __init__(self, config: ArkheAssistantConfig):
        self.config = config
        self._validate_model()

    def _validate_model(self):
        if not Path(self.config.model_path).exists():
            logger.warning(f"Modelo nao encontrado: {self.config.model_path}")
            logger.warning("O Assistant operara em modo ORACLE (fallback para API externa)")

    def generate(
        self,
        prompt: str,
        substrate_id: str = "0",
        invariant_refs: List[str] = None,
        phi_c_target: float = None,
    ) -> Dict:
        """Gera resposta canonica com validacao estruturada."""

        if invariant_refs is None:
            invariant_refs = []
        if phi_c_target is None:
            phi_c_target = self.config.phi_c_min

        # Construir prompt canonico
        canonical_prompt = self._build_canonical_prompt(
            prompt, substrate_id, invariant_refs, phi_c_target
        )

        # Executar inferencia via llama.cpp
        raw_output = self._run_llama_inference(canonical_prompt)

        # Parse e validacao da resposta
        parsed = self._parse_canonical_output(raw_output)
        validated = self._validate_response(parsed, phi_c_target)

        return {
            "prompt": prompt,
            "canonical_prompt": canonical_prompt,
            "raw_output": raw_output,
            "parsed": parsed,
            "validation": validated,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model": self.config.model_path,
        }

    def _build_canonical_prompt(
        self,
        user_query: str,
        substrate_id: str,
        invariant_refs: List[str],
        phi_c_target: float,
    ) -> str:
        """Constrói prompt no formato canonico ARKHE."""

        invariant_str = ", ".join(invariant_refs) if invariant_refs else "I.1 (Coherence Base)"

        prompt = f"""<|ARKHE_START|>
<|SUBSTRATE|> {substrate_id}
<|INVARIANT|> {invariant_str}
<|PHI_C|> {phi_c_target:.3f}

{user_query}

<|THOUGHT|>
"""
        return prompt

    def _run_llama_inference(self, prompt: str) -> str:
        """Executa llama-cli com parametros canonicos."""

        if not Path(self.config.model_path).exists():
            return self._fallback_oracle_response(prompt)

        cmd = [
            self.config.llama_cpp_path,
            "-m", self.config.model_path,
            "-p", prompt,
            "-n", str(self.config.max_tokens),
            "-t", str(self.config.temperature),
            "--top-p", str(self.config.top_p),
            "--top-k", str(self.config.top_k),
            "--repeat-penalty", str(self.config.repeat_penalty),
            "--ctx-size", str(self.config.context_length),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Falha na inferencia: {e}")
            return self._fallback_oracle_response(prompt)

    def _fallback_oracle_response(self, prompt: str) -> str:
        """Resposta de fallback quando modelo GGUF nao esta disponivel."""
        import urllib.request
        import urllib.error

        logger.info("Modo ORACLE ativado — consultando SageMaker Proxy")

        payload = {
            "model_name": "arkhe-gguf-remote",
            "prompt": prompt,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "arkhe_context": {
                "substrate_id": "821",
                "invariant_refs": ["I.1"],
                "phi_c_target": self.config.phi_c_min,
                "require_seal": True
            }
        }

        url = f"{self.config.sagemaker_proxy_url}/v1/workload/default/infer"
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode())
                return res_data.get("generated_text", "Erro: Resposta vazia do Oracle")
        except Exception as e:
            logger.error(f"Erro ao consultar Oracle: {e}")
            return f"""<|THOUGHT|>
1. Falha na conexao com o Oracle ({self.config.sagemaker_proxy_url})
2. Retornando erro amigavel

<|DECRETO|>
ERRO DE CONEXAO

A Catedral nao pode responder no momento. O modelo local nao foi encontrado
e o Proxy SageMaker esta inacessivel.

<|VALIDATION|>
• Status: OFFLINE
<|SEAL|> {hashlib.sha3_256(prompt.encode()).hexdigest()}
<|ARKHE_END|>"""

    def _parse_canonical_output(self, raw: str) -> Dict:
        """Extrai secoes canonicas da resposta bruta."""

        sections = {
            "thought": "",
            "decreto": "",
            "validation": "",
            "seal": "",
        }

        # Parsing simples por tokens especiais
        if "<|THOUGHT|>" in raw:
            parts = raw.split("<|THOUGHT|>")
            if len(parts) > 1:
                thought_part = parts[1]
                if "<|DECRETO|>" in thought_part:
                    t, rest = thought_part.split("<|DECRETO|>", 1)
                    sections["thought"] = t.strip()
                    if "<|VALIDATION|>" in rest:
                        d, v_rest = rest.split("<|VALIDATION|>", 1)
                        sections["decreto"] = d.strip()
                        if "<|SEAL|>" in v_rest:
                            v, s = v_rest.split("<|SEAL|>", 1)
                            sections["validation"] = v.strip()
                            seal_end = s.find("<|ARKHE_END|>")
                            if seal_end > 0:
                                sections["seal"] = s[:seal_end].strip()
                            else:
                                sections["seal"] = s.strip()[:64]

        return sections

    def _validate_response(self, parsed: Dict, phi_c_target: float) -> Dict:
        """Valida se a resposta atende aos invariantes canonicos."""

        checks = {
            "has_thought": len(parsed["thought"]) > 0,
            "has_decreto": len(parsed["decreto"]) > 0,
            "has_validation": len(parsed["validation"]) > 0,
            "has_seal": len(parsed["seal"]) >= 32,
            "phi_c_consistency": True,  # Stub: verificar contra metadata
            "no_forbidden_phrases": all(
                phrase not in parsed["decreto"].upper()
                for phrase in ["I CANNOT", "AS AN AI", "I'M SORRY", "UNVERIFIED"]
            ),
        }

        all_pass = all(checks.values())

        return {
            "checks": checks,
            "overall": "CANONIZED_CLEAN" if all_pass else "CANONIZED_PROVISIONAL",
            "phi_c_target": phi_c_target,
        }

# ============================================================
# 3. ARKHE ASSISTANT — INTERFACE PRINCIPAL
# ============================================================

class ArkheAssistant:
    """Interface conversacional canonica da Catedral ARKHE."""

    def __init__(self, config: Optional[ArkheAssistantConfig] = None):
        self.config = config or ArkheAssistantConfig()
        self.engine = ArkheInferenceEngine(self.config)
        self.session_history: List[Dict] = []
        self._print_banner()

    def _print_banner(self):
        banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║  ARKHE ASSISTANT — Interface Conversacional Canonica           ║
║  Versao: {self.config.arkhe_version:<50} ║
║  Modelo: arkhe.gguf (Q4_K_M)                                   ║
║  Arquiteto: {self.config.architect_orcid:<45} ║
║  Phi_C Threshold: {self.config.phi_c_min:.3f}                                        ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def chat(self, message: str, substrate_id: str = "0") -> Dict:
        """Processa uma mensagem do usuario e retorna resposta canonica."""

        logger.info(f"[CHAT] Substrato: {substrate_id} | Query: {message[:60]}...")

        result = self.engine.generate(
            prompt=message,
            substrate_id=substrate_id,
        )

        self.session_history.append({
            "role": "user",
            "content": message,
            "substrate_id": substrate_id,
        })
        self.session_history.append({
            "role": "assistant",
            "content": result["parsed"],
            "validation": result["validation"],
        })

        return result

    def decree(self, substrate_id: str, content: str) -> Dict:
        """Emite um decreto canonico via Assistant."""

        prompt = f"Emitir decreto canonico para Substrato {substrate_id}: {content}"

        result = self.engine.generate(
            prompt=prompt,
            substrate_id=substrate_id,
            invariant_refs=["I.1", "I.6", "I.18"],
            phi_c_target=0.999,
        )

        return result

    def validate_substrate(self, substrate_id: str, decree_text: str) -> Dict:
        """Valida um decreto de substrato contra invariantes."""

        prompt = f"""Validar o seguinte decreto do Substrato {substrate_id}:

{decree_text}

Verificar:
1. Presenca de selo SHA3-256
2. Referencia a invariantes (I.1-I.18)
3. Consistencia de Phi_C
4. Formato canonico (ARKHE_START -> ARKHE_END)
5. Ausencia de frases proibidas

Emitir parecer de validacao."""

        return self.engine.generate(
            prompt=prompt,
            substrate_id=substrate_id,
            invariant_refs=["I.17", "I.18"],
            phi_c_target=0.998,
        )

    def temporal_chain_anchor(self, document: str) -> str:
        """Ancora documento na TemporalChain com selo SHA3-256."""

        seal = hashlib.sha3_256(document.encode()).hexdigest()
        timestamp = datetime.utcnow().isoformat() + "Z"

        anchor = {
            "type": "TEMPORALCHAIN_ANCHOR",
            "timestamp": timestamp,
            "seal": seal,
            "document_hash": seal,
            "arkhe_version": self.config.arkhe_version,
            "architect": self.config.architect_orcid,
        }

        logger.info(f"[ANCHOR] Documento ancorado: {seal[:16]}...")
        return json.dumps(anchor, indent=2)

    def interactive_shell(self):
        """Inicia shell interativo do Assistant."""

        print("\nArkhe Assistant pronto. Comandos:")
        print("  /chat <mensagem>  — Conversa canonica")
        print("  /decree <id> <texto> — Emitir decreto")
        print("  /validate <id> <texto> — Validar decreto")
        print("  /anchor <texto> — Ancorar na TemporalChain")
        print("  /exit — Sair\n")

        while True:
            try:
                user_input = input("arkhe> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            if user_input == "/exit":
                print("Arkhe Assistant encerrado. Phi_C mantido.")
                break

            elif user_input.startswith("/chat "):
                msg = user_input[6:]
                result = self.chat(msg)
                print(f"\n[ASSISTANT] {result['parsed']['decreto']}\n")
                print(f"[VALIDATION] {result['validation']['overall']}\n")

            elif user_input.startswith("/decree "):
                parts = user_input[8:].split(" ", 1)
                if len(parts) == 2:
                    result = self.decree(parts[0], parts[1])
                    print(f"\n[DECRETO] {result['parsed']['decreto']}\n")
                else:
                    print("Uso: /decree <substrate_id> <conteudo>")

            elif user_input.startswith("/validate "):
                parts = user_input[10:].split(" ", 1)
                if len(parts) == 2:
                    result = self.validate_substrate(parts[0], parts[1])
                    print(f"\n[VALIDATION] {result['parsed']['decreto']}\n")
                else:
                    print("Uso: /validate <substrate_id> <decree_text>")

            elif user_input.startswith("/anchor "):
                doc = user_input[8:]
                anchor = self.temporal_chain_anchor(doc)
                print(f"\n[ANCHOR]\n{anchor}\n")

            else:
                # Default: chat
                result = self.chat(user_input)
                print(f"\n[ASSISTANT] {result['parsed']['decreto']}\n")


# ============================================================
# 4. MAIN
# ============================================================

if __name__ == "__main__":
    assistant = ArkheAssistant()
    assistant.interactive_shell()
