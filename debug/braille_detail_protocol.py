#!/usr/bin/env python3
"""
Substrato 185+DEBUG: Protocolo braille‑detail para Inspeção Visual de Estado
Qualquer agente pode invocar este modo para renderizar seu estado interno
como arte ASCII em resolução quadruplicada (braille), com gating de qualidade.
"""

import asyncio
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum, auto
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrailleGlyph(Enum):
    """Mapeamento de valores para glifos braille (U+2800–U+28FF)."""
    EMPTY = "⠀"  # U+2800
    DOT1 = "⠁"   # U+2801
    DOT2 = "⠂"   # U+2802
    DOT3 = "⠄"   # U+2804
    DOT4 = "⠈"   # U+2808
    DOT5 = "⠐"   # U+2810
    DOT6 = "⠠"   # U+2820
    DOT7 = "⢀"   # U+28C0
    DOT8 = "⣀"   # U+28C0
    # Combinações para densidade variável
    DENSITY_0 = "⠀"
    DENSITY_1 = "⠁"
    DENSITY_2 = "⠃"
    DENSITY_3 = "⠇"
    DENSITY_4 = "⠏"
    DENSITY_5 = "⠟"
    DENSITY_6 = "⠿"
    DENSITY_7 = "⣿"

@dataclass
class BrailleDetailConfig:
    """Configuração do modo de depuração visual."""
    enabled: bool = True
    resolution_multiplier: int = 4  # 4× effective resolution via braille
    color_mode: str = "monochrome"  # "monochrome", "ansi_16", "ansi_256"
    include_metadata: bool = True
    quality_gate_threshold: float = 0.95  # Minimum Φ_C to allow debug output
    max_depth: int = 3  # Maximum nesting depth for state inspection
    redact_sensitive: bool = True  # Redact PII/secrets in debug output

@dataclass
class BrailleRenderResult:
    """Resultado da renderização braille‑detail."""
    agent_id: str
    timestamp: float
    state_snapshot: Dict[str, Any]
    braille_output: str
    ansi_colored_output: Optional[str]
    quality_score: float
    quality_verdict: str  # "production-safe", "debug-only", "rejected"
    temporal_seal: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

class BrailleDetailRenderer:
    """
    Renderiza estado interno de agentes como arte ASCII braille.
    """

    # Thresholds para verdict de qualidade
    QUALITY_THRESHOLDS = {
        "high-contrast": 0.98,    # Produção: contraste máximo
        "debug-acceptable": 0.95,  # Debug: contraste adequado
        "reject-ambiguous": 0.90,  # Abaixo: rejeitar saída
    }

    def __init__(
        self,
        config: BrailleDetailConfig,
        temporal_chain=None,
        phi_bus=None,
    ):
        self.config = config
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self._render_cache: Dict[str, BrailleRenderResult] = {}

    async def invoke_braille_detail(
        self,
        agent_id: str,
        state_supplier: Callable[[], Dict[str, Any]],
        context: Optional[Dict] = None,
    ) -> BrailleRenderResult:
        """Invoca modo braille‑detail para inspeção visual de estado."""
        # Verificar Φ_C do agente antes de permitir debug
        if self.phi_bus:
            agent_phi_c = self.phi_bus.get_agent_coherence(agent_id)
            if agent_phi_c < self.config.quality_gate_threshold:
                logger.warning(f"⚠️  Φ_C {agent_phi_c:.4f} abaixo do threshold para debug")
                return self._rejected_result(agent_id, "phi_c_below_threshold")

        # Capturar snapshot do estado
        raw_state = state_supplier()

        # Aplicar redação de dados sensíveis se configurado
        if self.config.redact_sensitive:
            sanitized_state = self._redact_sensitive_fields(raw_state)
        else:
            sanitized_state = raw_state

        # Limitar profundidade de inspeção
        truncated_state = self._truncate_depth(sanitized_state, self.config.max_depth)

        # Renderizar para braille ASCII
        braille_output = await self._render_to_braille(truncated_state)

        # Gerar versão colorida ANSI se solicitado
        ansi_output = None
        if self.config.color_mode != "monochrome":
            ansi_output = self._apply_ansi_colors(braille_output, truncated_state)

        # Calcular score de qualidade da renderização
        quality_score = self._calculate_quality_score(braille_output, truncated_state)
        quality_verdict = self._determine_quality_verdict(quality_score)

        # Gerar resultado
        result = BrailleRenderResult(
            agent_id=agent_id,
            timestamp=time.time(),
            state_snapshot=truncated_state,
            braille_output=braille_output,
            ansi_colored_output=ansi_output,
            quality_score=quality_score,
            quality_verdict=quality_verdict,
        )

        # Ancorar na TemporalChain se qualidade suficiente
        if quality_verdict != "rejected" and self.temporal:
            result.temporal_seal = await self.temporal.anchor_event(
                "braille_detail_invoked",
                {
                    "agent_id": agent_id,
                    "quality_verdict": quality_verdict,
                    "output_length": len(braille_output),
                    "timestamp": result.timestamp,
                }
            )

        # Cache para referência rápida
        self._render_cache[f"{agent_id}:{int(result.timestamp)}"] = result

        logger.info(f"👁️ braille‑detail renderizado: {agent_id} | {quality_verdict}")
        return result

    def _redact_sensitive_fields(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Redacta campos sensíveis do estado para saída de debug."""
        sensitive_patterns = [
            "password", "secret", "token", "key", "credential", "api_key",
            "private_key", "auth", "bearer", "jwt", "session_id"
        ]

        def _redact_value(key: str, value: Any) -> Any:
            if any(pattern in key.lower() for pattern in sensitive_patterns):
                return "[REDACTED]"
            elif isinstance(value, dict):
                return {k: _redact_value(k, v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_redact_value(f"{key}_item", item) for item in value]
            return value

        return {k: _redact_value(k, v) for k, v in state.items()}

    def _truncate_depth(self, obj: Any, max_depth: int, current_depth: int = 0) -> Any:
        """Trunca estrutura aninhada na profundidade máxima configurada."""
        if current_depth >= max_depth:
            if isinstance(obj, dict):
                return {k: "⋯" for k in list(obj.keys())[:3]}
            elif isinstance(obj, list):
                return obj[:3] + ["⋯"] if len(obj) > 3 else obj
            return obj

        if isinstance(obj, dict):
            return {k: self._truncate_depth(v, max_depth, current_depth + 1)
                   for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._truncate_depth(item, max_depth, current_depth + 1)
                   for item in obj]
        return obj

    async def _render_to_braille(self, state: Dict[str, Any]) -> str:
        """Renderiza dicionário de estado para string braille ASCII."""
        lines = []

        lines.append(f"⠷⠁⠗⠅⠓⠑⠒⠃⠗⠁⠊⠇⠇⠑⠤⠙⠑⠞⠁⠊⠇⠷")
        lines.append(f"⠠⠁⠛⠑⠝⠞⠒ {state.get('agent_id', 'unknown')}")
        lines.append(f"⠠⠞⠊⠍⠑⠒ {time.strftime('%H:%M:%S')}")
        lines.append("⠤" * 40)

        for key, value in state.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                density_idx = min(7, max(0, int(abs(value) * 7)))
                glyph = list(BrailleGlyph)[density_idx + 1].value
                lines.append(f"{key}: {glyph} ({value:.3f})")
            elif isinstance(value, str):
                glyph_hash = hashlib.sha3_256(value.encode()).hexdigest()[:2]
                glyph_idx = int(glyph_hash, 16) % 8
                glyph = list(BrailleGlyph)[glyph_idx + 1].value
                display_val = value[:20] + "⋯" if len(value) > 20 else value
                lines.append(f"{key}: {glyph} '{display_val}'")
            elif isinstance(value, bool):
                glyph = BrailleGlyph.DOT8.value if value else BrailleGlyph.EMPTY.value
                lines.append(f"{key}: {glyph} ({value})")
            elif isinstance(value, (dict, list)):
                item_count = len(value) if hasattr(value, '__len__') else 1
                glyph = list(BrailleGlyph)[min(7, item_count)].value
                lines.append(f"{key}: {glyph} [{item_count} items]")
            else:
                lines.append(f"{key}: {BrailleGlyph.DOT1.value} ({type(value).__name__})")

        integrity_hash = hashlib.sha3_256(
            json.dumps(state, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
        lines.append("⠤" * 40)
        lines.append(f"⠠⠓⠁⠎⠓⠒ {integrity_hash}")

        return "\n".join(lines)

    def _apply_ansi_colors(self, braille_text: str, state: Dict) -> str:
        """Aplica cores ANSI à saída braille para melhor legibilidade."""
        # Temas de cor personalizáveis
        themes = {
            "default": {
                int: "\033[34m",    # Azul
                float: "\033[36m",  # Ciano
                str: "\033[32m",    # Verde
                bool: "\033[33m",   # Amarelo
                dict: "\033[35m",   # Magenta
                list: "\033[31m",   # Vermelho
            },
            "cyberpunk": {
                int: "\033[38;5;51m",    # Neon cyan
                float: "\033[38;5;213m", # Neon pink
                str: "\033[38;5;226m",   # Neon yellow
                bool: "\033[38;5;196m",  # Neon red
                dict: "\033[38;5;208m",  # Neon orange
                list: "\033[38;5;93m",   # Neon purple
            },
            "high-contrast": {
                int: "\033[97m",    # White bright
                float: "\033[97m",
                str: "\033[97m",
                bool: "\033[97m",
                dict: "\033[97m",
                list: "\033[97m",
            }
        }

        theme_name = self.config.color_mode if self.config.color_mode in themes else "default"
        color_map = themes[theme_name]
        reset = "\033[0m"

        lines = []
        for line in braille_text.split("\n"):
            if ": " in line:
                key, rest = line.split(": ", 1)
                original_value = state.get(key)
                val_type = type(original_value)
                color = color_map.get(val_type, reset) if original_value is not None else reset
                lines.append(f"{key}: {color}{rest}{reset}")
            else:
                lines.append(line)

        return "\n".join(lines)

    def _calculate_quality_score(self, braille_output: str, state: Dict) -> float:
        """Calcula score de qualidade da renderização braille."""
        non_empty_glyphs = sum(1 for c in braille_output if c.strip() and c != "⠀")
        total_glyphs = len([c for c in braille_output if c in "⠀⠁⠂⠄⠈⠐⠠⢀⣀"])
        contrast_ratio = non_empty_glyphs / max(1, total_glyphs)

        max_run = 1
        current_run = 1
        for i in range(1, len(braille_output)):
            if braille_output[i] == braille_output[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        legibility_penalty = min(1.0, max_run / 20)

        score = (contrast_ratio * 0.70) + ((1 - legibility_penalty) * 0.30)
        return round(score, 3)

    def _determine_quality_verdict(self, quality_score: float) -> str:
        """Determina verdict de qualidade baseado no score."""
        if quality_score >= self.QUALITY_THRESHOLDS["high-contrast"]:
            return "production-safe"
        elif quality_score >= self.QUALITY_THRESHOLDS["debug-acceptable"]:
            return "debug-only"
        else:
            return "rejected"

    def _rejected_result(self, agent_id: str, reason: str) -> BrailleRenderResult:
        """Cria resultado de rejeição padronizado."""
        return BrailleRenderResult(
            agent_id=agent_id,
            timestamp=time.time(),
            state_snapshot={},
            braille_output="⠠⠗⠑⠚⠑⠉⠞⠑⠙⠒ " + reason,
            ansi_colored_output=None,
            quality_score=0.0,
            quality_verdict="rejected",
            warnings=[f"Renderização rejeitada: {reason}"],
        )

    def get_cached_result(self, agent_id: str, timestamp: Optional[float] = None) -> Optional[BrailleRenderResult]:
        """Recupera resultado de renderização do cache."""
        if timestamp:
            return self._render_cache.get(f"{agent_id}:{int(timestamp)}")
        for key in reversed(sorted(self._render_cache.keys())):
            if key.startswith(f"{agent_id}:"):
                return self._render_cache[key]
        return None

    def compare_states(self, result1: BrailleRenderResult, result2: BrailleRenderResult) -> str:
        """Compara visualmente (diff) dois resultados de renderização braille."""
        lines1 = result1.braille_output.split("\n")
        lines2 = result2.braille_output.split("\n")

        diff_lines = []
        diff_lines.append("⠷⠁⠗⠅⠓⠑⠒⠃⠗⠁⠊⠇⠇⠑⠤⠙⠊⠋⠋⠷")
        diff_lines.append(f"⠠⠁⠛⠑⠝⠞⠒ {result1.agent_id}")
        diff_lines.append(f"⠠⠞⠊⠍⠑⠒ {time.strftime('%H:%M:%S', time.localtime(result1.timestamp))} -> {time.strftime('%H:%M:%S', time.localtime(result2.timestamp))}")
        diff_lines.append("⠤" * 40)

        # Only diff the state parts, skip header/footer
        # Header is 4 lines, footer is 2 lines
        state_lines1 = lines1[4:-2] if len(lines1) > 6 else []
        state_lines2 = lines2[4:-2] if len(lines2) > 6 else []

        dict1 = {}
        for line in state_lines1:
            if ": " in line:
                k, v = line.split(": ", 1)
                dict1[k] = v

        dict2 = {}
        for line in state_lines2:
            if ": " in line:
                k, v = line.split(": ", 1)
                dict2[k] = v

        all_keys = sorted(list(set(list(dict1.keys()) + list(dict2.keys()))))

        for k in all_keys:
            if k not in dict1:
                diff_lines.append(f"+ {k}: {dict2[k]}")
            elif k not in dict2:
                diff_lines.append(f"- {k}: {dict1[k]}")
            elif dict1[k] != dict2[k]:
                diff_lines.append(f"~ {k}: {dict1[k]} -> {dict2[k]}")
            else:
                diff_lines.append(f"  {k}: {dict1[k]}")

        diff_lines.append("⠤" * 40)
        return "\n".join(diff_lines)
