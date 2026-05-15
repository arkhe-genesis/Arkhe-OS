#!/usr/bin/env python3
"""
Substrato 187: Processamento de Imagem Real com Pillow + OpenCV
Implementa conversão Image → ndarray, CLAHE adaptativo e detecção de bordas Laplacian
para renderização ASCII edge-aware determinística.
"""

import numpy as np
from PIL import Image, ImageEnhance
import cv2
import hashlib
from typing import Tuple, Optional, Dict
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ImageProcessingConfig:
    """Configuração para processamento de imagem edge-aware."""
    clahe_clip_limit: float = 2.0
    clahe_grid_size: Tuple[int, int] = (8, 8)
    laplacian_kernel_size: int = 3
    edge_weight: float = 0.3  # Peso para realçar bordas no downsample
    contrast_enhancement: float = 1.1
    brightness_adjustment: float = 0.0

class RealImageProcessor:
    """
    Processa imagens reais para renderização ASCII com preservação de bordas.

    Pipeline:
    1. PIL.Image.open → conversão para ndarray RGB/Grayscale
    2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    3. Laplacian edge detection para mapa de pesos
    4. Weighted downsampling preservando bordas
    5. Mapeamento determinístico para glifos ASCII/Braille
    """

    PRESET_GLYPHS = {
        "stroke-clarity": " .:-=+*#%@",
        "d30-dense": [chr(c) for c in range(0x2591, 0x2593+1)] + [chr(c) for c in range(0x2800, 0x28FF+1)],
        "braille-detail": [chr(c) for c in range(0x2800, 0x28FF+1)],  # 256 glifos Braille
        "eikon-motion": " .oO@*",
    }

    def __init__(self, config: Optional[ImageProcessingConfig] = None):
        self.config = config or ImageProcessingConfig()

    def load_and_preprocess(self, image_path: str, target_size: Tuple[int, int]) -> np.ndarray:
        """
        Carrega imagem com Pillow e aplica pré-processamento edge-aware.

        Args:
            image_path: Caminho para arquivo de imagem
            target_size: (width, height) desejado para render ASCII

        Returns:
            ndarray processado normalizado [0, 1]
        """
        # 1. Carregar com Pillow
        img = Image.open(image_path).convert("L")  # Grayscale para processamento

        # 2. Ajustes de contraste/brilho
        if self.config.contrast_enhancement != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.config.contrast_enhancement)
        if self.config.brightness_adjustment != 0.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.0 + self.config.brightness_adjustment)

        # 3. Converter para OpenCV ndarray
        img_cv = np.array(img, dtype=np.uint8)

        # 4. Aplicar CLAHE para realçar detalhes locais
        clahe = cv2.createCLAHE(
            clipLimit=self.config.clahe_clip_limit,
            tileGridSize=self.config.clahe_grid_size
        )
        img_clahe = clahe.apply(img_cv)

        # 5. Detectar bordas com Laplacian para mapa de pesos
        laplacian = cv2.Laplacian(
            img_clahe,
            cv2.CV_64F,
            ksize=self.config.laplacian_kernel_size
        )
        edge_map = np.abs(laplacian)
        edge_map = (edge_map - edge_map.min()) / (edge_map.max() - edge_map.min() + 1e-8)

        # 6. Downsample ponderado por bordas
        downsampled = self._weighted_downsample(img_clahe, edge_map, target_size)

        # 7. Normalizar para [0, 1]
        normalized = (downsampled - downsampled.min()) / (downsampled.max() - downsampled.min() + 1e-8)

        logger.info(f"✅ Imagem processada: {image_path} → {target_size} | CLAHE+Laplacian aplicado")
        return normalized

    def _weighted_downsample(
        self,
        img: np.ndarray,
        edge_map: np.ndarray,
        target_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Realiza downsample preservando regiões de alta frequência (bordas).

        Estratégia: interpolação bilinear com peso adicional para pixels com alta magnitude Laplacian.
        """
        h, w = img.shape
        th, tw = target_size

        # Criar grade de coordenadas de destino
        y_coords = np.linspace(0, h-1, th)
        x_coords = np.linspace(0, w-1, tw)

        result = np.zeros((th, tw), dtype=np.float32)

        for i, y in enumerate(y_coords):
            for j, x in enumerate(x_coords):
                # Coordenadas inteiras vizinhas
                y0, y1 = int(np.floor(y)), int(np.ceil(y))
                x0, x1 = int(np.floor(x)), int(np.ceil(x))

                # Pesos de interpolação bilinear
                wy1, wy0 = y - y0, y1 - y
                wx1, wx0 = x - x0, x1 - x

                # Valor base por interpolação bilinear
                base_value = (
                    wy0 * wx0 * img[y0, x0] +
                    wy0 * wx1 * img[y0, x1] +
                    wy1 * wx0 * img[y1, x0] +
                    wy1 * wx1 * img[y1, x1]
                ) / 4

                # Peso de borda (realçar se houver borda próxima)
                edge_weight = (
                    wy0 * wx0 * edge_map[y0, x0] +
                    wy0 * wx1 * edge_map[y0, x1] +
                    wy1 * wx0 * edge_map[y1, x0] +
                    wy1 * wx1 * edge_map[y1, x1]
                ) / 4

                # Combinação ponderada
                result[i, j] = base_value * (1 - self.config.edge_weight) + \
                              (base_value + edge_weight * 255) * self.config.edge_weight

        return np.clip(result, 0, 255).astype(np.uint8)

    def map_to_glyphs(self, normalized: np.ndarray, preset: str) -> str:
        """
        Mapeia valores normalizados [0,1] para glifos ASCII/Braille do preset.

        Mapeamento determinístico via hash do valor + posição para consistência.
        """
        glyphs = self.PRESET_GLYPHS.get(preset, self.PRESET_GLYPHS["stroke-clarity"])
        h, w = normalized.shape
        lines = []

        for i in range(h):
            line = []
            for j in range(w):
                value = normalized[i, j]
                # Índice determinístico baseado em valor + posição
                glyph_idx = int((value * (len(glyphs) - 1)) +
                               (hash(f"{i}:{j}") % 3) * 0.01) % len(glyphs)
                line.append(glyphs[glyph_idx])
            lines.append("".join(line))

        return "\n".join(lines)

    def calculate_quality_metrics(self, ascii_output: str, original_img: np.ndarray) -> Dict:
        """Calcula métricas de qualidade para gating automático."""
        # Densidade de glifos não-vazios
        non_empty = sum(1 for c in ascii_output if c.strip() and c not in " \n⠀")
        total_chars = len([c for c in ascii_output if c not in "\n"])
        density = non_empty / max(1, total_chars)

        # Variação de glifos (diversidade)
        unique_glyphs = len(set(c for c in ascii_output if c not in " \n"))
        variation = unique_glyphs / 256  # Normalizado para máximo Braille

        # Contraste local estimado
        contrast = np.std(original_img) / (np.mean(original_img) + 1e-8)

        # Verdict baseado em thresholds
        if density > 0.10 and variation > 0.05:
            verdict = "high-contrast"
        elif "⠿" in ascii_output or "⣿" in ascii_output:
            verdict = "braille-dominant"
        else:
            verdict = "low-contrast-garble-risk"

        return {
            "density": round(density, 3),
            "variation": round(variation, 3),
            "contrast": round(contrast, 3),
            "verdict": verdict,
            "production_safe": verdict in ["high-contrast", "braille-dominant"]
        }
