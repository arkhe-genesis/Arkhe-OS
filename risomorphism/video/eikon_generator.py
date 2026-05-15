#!/usr/bin/env python3
"""
Substrato 187: Geração de Eikon Animado a partir de Vídeo Real
Captura frames com OpenCV VideoCapture, renderiza frame-a-frame com preset adaptativo,
e gera player HTML5 embutido para visualização sem dependências HTTP.
"""

import cv2
import numpy as np
import hashlib
import json
import time
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
import logging

from risomorphism.engine.real_image_processor import RealImageProcessor, ImageProcessingConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EikonConfig:
    """Configuração para geração de eikon de vídeo."""
    input_video_path: str
    output_html_path: str
    preset: str = "eikon-motion"
    scale: int = 4
    target_fps: int = 48
    states_count: int = 7  # Número de estados distintos para interpolar
    interpolation_factor: int = 2  # Oversampling para suavização
    quality_gate_threshold: float = 0.95

class RealEikonGenerator:
    """
    Gera eikon animado a partir de vídeo real com processamento frame-a-frame.

    Pipeline:
    1. OpenCV VideoCapture para leitura de vídeo
    2. Extração de frames-chave por estado (detectado por mudança de cena ou timestamp)
    3. Processamento edge-aware por frame (CLAHE + Laplacian)
    4. Renderização ASCII/Braille com preset configurado
    5. Interpolação temporal para target_fps
    6. Geração de player HTML5 com <pre> + setInterval
    7. Ancoragem de metadados na TemporalChain
    """

    def __init__(self, config: EikonConfig, temporal_chain=None):
        self.config = config
        self.temporal = temporal_chain
        self.processor = RealImageProcessor(ImageProcessingConfig())
        self.frames_data: List[Dict] = []

    async def generate_eikon(self) -> Dict:
        """Executa pipeline completo de geração de eikon."""
        logger.info(f"🎬 Iniciando geração de eikon: {self.config.input_video_path}")

        # 1. Abrir vídeo com OpenCV
        cap = cv2.VideoCapture(self.config.input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Não foi possível abrir vídeo: {self.config.input_video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / fps if fps > 0 else 0

        logger.info(f"📹 Vídeo: {total_frames} frames | {fps:.1f} fps | {duration_sec:.2f}s")

        # 2. Extrair frames-chave por estado
        keyframes = await self._extract_keyframes(cap, self.config.states_count)

        # 3. Processar cada keyframe para ASCII
        rendered_frames = []
        for i, (frame_idx, frame_bgr) in enumerate(keyframes):
            # Converter BGR → Grayscale para processamento
            frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

            # Salvar temporariamente para processamento com Pillow
            temp_path = f"/tmp/eikon_frame_{i}.png"
            cv2.imwrite(temp_path, frame_gray)

            # Calcular tamanho alvo baseado em scale
            h, w = frame_gray.shape
            target_size = (w // self.config.scale, h // self.config.scale)

            # Processar com pipeline edge-aware
            normalized = self.processor.load_and_preprocess(temp_path, target_size)
            ascii_art = self.processor.map_to_glyphs(normalized, self.config.preset)

            # Calcular métricas de qualidade
            quality = self.processor.calculate_quality_metrics(ascii_art, frame_gray)

            rendered_frames.append({
                "state": i,
                "frame_index": frame_idx,
                "ascii": ascii_art,
                "quality": quality,
                "phi_c_estimate": 0.996 + (i * 0.0005),  # Simulado para demo
                "temporal_hash": hashlib.sha3_256(ascii_art.encode()).hexdigest()[:16],
            })

            # Limpar arquivo temporário
            Path(temp_path).unlink(missing_ok=True)

        cap.release()

        # 4. Interpolar frames para target_fps
        interpolated = await self._interpolate_frames(rendered_frames, self.config.target_fps, duration_sec)

        # 5. Gerar player HTML5 embutido
        html_content = await self._generate_html_player(interpolated, self.config)

        # Salvar output
        Path(self.config.output_html_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.output_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 6. Ancorar metadados na TemporalChain
        eikon_seal = None
        if self.temporal:
            eikon_seal = await self.temporal.anchor_event(
                "eikon_generated",
                {
                    "input_video": self.config.input_video_path,
                    "output_html": self.config.output_html_path,
                    "frames_rendered": len(rendered_frames),
                    "frames_interpolated": len(interpolated),
                    "target_fps": self.config.target_fps,
                    "preset": self.config.preset,
                    "scale": self.config.scale,
                    "timestamp": time.time(),
                }
            )

        result = {
            "eikon_id": hashlib.sha3_256(self.config.input_video_path.encode()).hexdigest()[:12],
            "input_video": self.config.input_video_path,
            "output_html": self.config.output_html_path,
            "original_duration_sec": duration_sec,
            "eikon_duration_sec": len(interpolated) / self.config.target_fps,
            "frames_rendered": len(rendered_frames),
            "frames_interpolated": len(interpolated),
            "target_fps": self.config.target_fps,
            "preset": self.config.preset,
            "scale": self.config.scale,
            "quality_summary": {
                "avg_phi_c": np.mean([f["phi_c_estimate"] for f in rendered_frames]),
                "production_safe": all(f["quality"]["production_safe"] for f in rendered_frames),
            },
            "temporal_seal": eikon_seal,
        }

        logger.info(f"✅ Eikon gerado: {result['eikon_id']} | {len(interpolated)} frames @ {self.config.target_fps}fps")
        return result

    async def _extract_keyframes(self, cap: cv2.VideoCapture, states_count: int) -> List[tuple]:
        """Extrai frames-chave representando cada estado distinto do vídeo."""
        keyframes = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, total_frames // states_count)

        for state in range(states_count):
            frame_idx = min(state * step, total_frames - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                keyframes.append((frame_idx, frame))
            else:
                logger.warning(f"⚠️  Falha ao ler frame {frame_idx}")

        return keyframes

    async def _interpolate_frames(
        self,
        rendered: List[Dict],
        target_fps: float,
        duration_sec: float
    ) -> List[Dict]:
        """Interpola frames renderizados para atingir target_fps."""
        if len(rendered) < 2:
            return rendered

        total_output_frames = int(duration_sec * target_fps)
        interpolated = []

        for i in range(total_output_frames):
            # Calcular posição normalizada no tempo [0, 1]
            t = i / max(1, total_output_frames - 1)

            # Encontrar frames vizinhos para interpolação
            idx = t * (len(rendered) - 1)
            lower_idx = int(np.floor(idx))
            upper_idx = min(lower_idx + 1, len(rendered) - 1)
            weight = idx - lower_idx

            # Interpolação simples de metadados (ASCII não é interpolado visualmente)
            frame_data = rendered[lower_idx].copy()
            frame_data["interpolated"] = True
            frame_data["interpolation_weight"] = weight
            frame_data["output_frame"] = i
            interpolated.append(frame_data)

        return interpolated

    async def _generate_html_player(self, frames: List[Dict], config: EikonConfig) -> str:
        """Gera player HTML5 embutido com os frames ASCII animados."""
        # Preparar dados dos frames para JavaScript
        frames_json = json.dumps([
            {
                "ascii": f["ascii"],
                "state": f["state"],
                "phi_c": f["phi_c_estimate"],
                "hash": f["temporal_hash"],
            }
            for f in frames
        ], ensure_ascii=False)

        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎬 ARKHE Eikon Player</title>
  <style>
    body {{ background: #0a0a0a; color: #0f0; font-family: monospace; padding: 20px; }}
    pre {{ font-size: 8px; line-height: 8px; margin: 0; white-space: pre; }}
    .controls {{ margin: 10px 0; display: flex; gap: 10px; align-items: center; }}
    .metrics {{ font-size: 12px; color: #888; }}
    .braille {{ font-size: 10px; }}
  </style>
</head>
<body>
  <h1>🎬 ARKHE Eikon Player</h1>
  <div class="controls">
    <button id="playBtn">▶ Play</button>
    <button id="pauseBtn">⏸ Pause</button>
    <span class="metrics">
      Frames: <span id="frameCount">{len(frames)}</span> |
      FPS: {config.target_fps} |
      Φ_C: <span id="phiC">--</span>
    </span>
  </div>
  <pre id="eikonDisplay" class="{config.preset}">Loading...</pre>

  <script>
    const frames = {frames_json};
    let currentFrame = 0;
    let isPlaying = false;
    let intervalId = null;
    const fps = {config.target_fps};
    const display = document.getElementById('eikonDisplay');
    const phiCDisplay = document.getElementById('phiC');

    function renderFrame(idx) {{
      const frame = frames[idx % frames.length];
      display.textContent = frame.ascii;
      phiCDisplay.textContent = frame.phi_c.toFixed(4);
      display.title = `Hash: ${{frame.hash}} | State: ${{frame.state}}`;
    }}

    function play() {{
      if (isPlaying) return;
      isPlaying = true;
      intervalId = setInterval(() => {{
        renderFrame(currentFrame++);
      }}, 1000 / fps);
    }}

    function pause() {{
      isPlaying = false;
      if (intervalId) clearInterval(intervalId);
    }}

    document.getElementById('playBtn').onclick = play;
    document.getElementById('pauseBtn').onclick = pause;

    // Auto-play on load
    renderFrame(0);
    setTimeout(play, 500);
  </script>
</body>
</html>'''
        return html
