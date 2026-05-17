#!/usr/bin/env python3
"""
ARKHE OS Substrato 236: OpenCode Canonical Integration
Canon: ∞.Ω.∇+++.236.opencode
Integra o OpenCode CLI como ferramenta canônica da Catedral,
com validação de configuração, ancoragem TemporalChain e Φ_C gate.
"""

import asyncio, hashlib, json, os, subprocess, time
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field

@dataclass
class OpenCodeConfig:
    """Configuração canônica do OpenCode."""
    config_path: str
    model: str = "claude-sonnet-4-20250514"
    provider: str = "anthropic"
    mode: str = "interactive"
    tools_enabled: List[str] = field(default_factory=list)
    phi_c_threshold: float = 0.85
    temporal_anchor: bool = True
    max_tokens_per_request: int = 4096

class OpenCodeCanonicalTool:
    """
    Ferramenta canônica para o OpenCode.
    Registrada no Tool Calling System com circuit breaker e rate limiting.
    """

    def __init__(self, config: OpenCodeConfig, tool_system=None, temporal=None, phi_bus=None):
        self.config = config
        self.tool_system = tool_system
        self.temporal = temporal
        self.phi_bus = phi_bus
        self._execution_history: List[Dict] = []

    def generate_config(self, parameters: dict) -> Dict:
        """Gera arquivo opencode.json canônico."""
        output_path = parameters.get("output_path")
        config = {
            "$schema": "https://opencode.ai/config.json",
            "assistant": {
                "provider": {
                    "name": self.config.provider,
                    "model": self.config.model
                },
                "mode": self.config.mode,
                "tools": {
                    "enabled": self.config.tools_enabled or [
                        "read", "write", "edit", "bash", "grep", "glob"
                    ]
                },
                "hooks": {
                    "pre_execution": "arkhe_phi_c_gate",
                    "post_execution": "arkhe_temporal_anchor"
                }
            },
            "arkhe_metadata": {
                "canon": "∞.Ω.∇+++",
                "token": "orcid:0009-0005-2697-4668",
                "phi_c_threshold": self.config.phi_c_threshold,
                "temporal_anchor": self.config.temporal_anchor,
                "max_tokens": self.config.max_tokens_per_request
            }
        }
        target = output_path or self.config.config_path or "./opencode.json"
        with open(target, "w") as f:
            json.dump(config, f, indent=2)
        return config

    async def validate_config(self, parameters: dict) -> Dict:
        """Valida uma configuração existente contra thresholds canônicos."""
        config_path = parameters.get("config_path")
        with open(config_path, "r") as f:
            cfg = json.load(f)

        validations = []

        # Verificar modelo
        model = cfg.get("assistant", {}).get("provider", {}).get("model", "")
        if not model:
            validations.append({"check": "model_defined", "passed": False, "reason": "No model specified"})
        else:
            validations.append({"check": "model_defined", "passed": True, "model": model})

        # Verificar provider
        provider = cfg.get("assistant", {}).get("provider", {}).get("name", "")
        if provider not in ["anthropic", "openai", "google", "bedrock", "local"]:
            validations.append({"check": "provider_supported", "passed": False, "reason": f"Unknown provider: {provider}"})
        else:
            validations.append({"check": "provider_supported", "passed": True, "provider": provider})

        # Verificar ferramentas habilitadas
        tools = cfg.get("assistant", {}).get("tools", {}).get("enabled", [])
        dangerous_defaults = ["shell", "exec", "sudo"]
        for tool in tools:
            if tool in dangerous_defaults:
                validations.append({"check": "dangerous_tool_disabled", "passed": False, "reason": f"Dangerous tool enabled: {tool}"})

        all_passed = all(v["passed"] for v in validations)
        result = {
            "config_path": config_path,
            "validations": validations,
            "all_passed": all_passed,
            "phi_c": 0.95 if all_passed else 0.6,
            "recommendation": "approve" if all_passed else "review"
        }

        # Ancorar validação
        if self.temporal and all_passed:
            await self.temporal.anchor_event("opencode_config_validated", {
                "config_path": config_path,
                "model": model,
                "provider": provider,
                "all_passed": all_passed,
                "timestamp": time.time()
            })

        return result

    async def execute_opencode(self, parameters: dict) -> Dict:
        """
        Executa um comando via OpenCode com validação de coerência.

        Fluxo canônico:
        1. Verificar Φ_C do ambiente atual
        2. Executar opencode com o prompt
        3. Capturar saída e métricas
        4. Ancorar resultado na TemporalChain
        """
        prompt = parameters.get("prompt")
        working_dir = parameters.get("working_dir", ".")

        start_time = time.time()

        # Verificar rate limit (token budget)
        if not await self._check_token_budget(prompt):
            return {"status": "rate_limited", "reason": "Token budget exceeded"}

        # Construir comando
        cmd = ["opencode", "--config", self.config.config_path, "--prompt", prompt]
        if working_dir:
            cmd.extend(["--cwd", working_dir])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.max_tokens_per_request / 50  # estimativa
            )

            execution_time = time.time() - start_time
            output = stdout.decode().strip()
            error = stderr.decode().strip()

            # Calcular Φ_C da execução
            phi_c = self._compute_execution_phi_c(process.returncode, output, execution_time)

            result = {
                "status": "success" if process.returncode == 0 else "error",
                "output": output[:1000],
                "error": error[:500] if error else None,
                "returncode": process.returncode,
                "execution_time_ms": execution_time * 1000,
                "phi_c": phi_c,
                "tokens_estimated": len(prompt.split()) * 2 + len(output.split())
            }

            # Ancorar na TemporalChain se sucesso
            if self.temporal and process.returncode == 0 and phi_c >= self.config.phi_c_threshold:
                result["temporal_seal"] = await self.temporal.anchor_event(
                    "opencode_execution_completed",
                    {
                        "prompt_hash": hashlib.sha3_256(prompt.encode()).hexdigest()[:16],
                        "returncode": process.returncode,
                        "phi_c": phi_c,
                        "execution_time_ms": result["execution_time_ms"],
                        "timestamp": time.time()
                    }
                )

            self._execution_history.append(result)
            return result

        except asyncio.TimeoutError:
            return {"status": "timeout", "reason": f"Execution exceeded time limit"}
        except FileNotFoundError:
            return {"status": "error", "reason": "opencode executable not found"}


    def _compute_execution_phi_c(self, returncode: int, output: str, execution_time: float) -> float:
        """Calcula Φ_C para execução do OpenCode."""
        score = 0.95
        if returncode != 0:
            score -= 0.2
        if len(output) < 10:
            score -= 0.1
        if execution_time > 30:
            score -= 0.05
        return max(0.0, min(1.0, score))

    async def _check_token_budget(self, prompt: str) -> bool:
        """Verifica se há tokens disponíveis no budget do agente."""
        estimated_tokens = len(prompt.split()) * 2
        return estimated_tokens <= self.config.max_tokens_per_request

    def register_all_tools(self, tool_system) -> int:
        """Registra operações OpenCode como ferramentas canônicas."""
        from tool_calling.canonical_tool_system import ToolDefinition

        tools = [
            ToolDefinition(
                tool_id="opencode_generate_config",
                name="opencode_generate_config",
                description="Generate a canonical opencode.json configuration file",
                handler=self.generate_config,
                agent_owner="build_sentinel",
                confidence_required=0.80,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "output_path": {"type": "string"}
                    }
                }
            ),
            ToolDefinition(
                tool_id="opencode_validate_config",
                name="opencode_validate_config",
                description="Validate an OpenCode configuration against canonical thresholds",
                handler=self.validate_config,
                agent_owner="security_sentinel",
                confidence_required=0.90,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "config_path": {"type": "string"}
                    }
                }
            ),
            ToolDefinition(
                tool_id="opencode_execute",
                name="opencode_execute",
                description="Execute an OpenCode command with Φ_C validation and TemporalChain anchoring",
                handler=self.execute_opencode,
                agent_owner="build_sentinel",
                confidence_required=0.85,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "working_dir": {"type": "string"}
                    }
                }
            ),
        ]

        registered = 0
        for tool_def in tools:
            # Need to create mock definitions since there is a missing parameters_schema and name mapping issue.
            if hasattr(tool_system, "register_tool"):
                tool_system.register_tool(tool_def)
                success = True
            elif hasattr(tool_system, "_registry"):
                tool_system._registry[tool_def.tool_id] = tool_def
                success = True
            else:
                success = False

            if success:
                registered += 1

        return registered
