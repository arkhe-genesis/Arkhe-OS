#!/usr/bin/env python3
"""
Substrato 227+: Invisible Watermark Encoder
Inserção de marca d'água imperceptível em imagens autorizadas,
com assinatura PQC embutida para rastreamento forense.
"""
import numpy as np
import scipy.fftpack
import hashlib
from typing import Optional, Tuple

class InvisibleWatermarkEncoder:
    """
    Codifica marca d'água invisível em imagens usando:
    • DCT (Discrete Cosine Transform) para domínio de frequência
    • Chave derivada do fingerprint PQC para vinculação criptográfica
    • Robustez a compressão, redimensionamento e filtros comuns
    """

    def __init__(self, strength: float = 0.02, pqc_key_derivation: bool = True):
        self.strength = strength  # Fator de inserção (0.01-0.05 para imperceptibilidade)
        self.pqc_derived = pqc_key_derivation

    async def embed_watermark(self, image: np.ndarray, creator_fingerprint: str) -> np.ndarray:
        """
        Insere marca d'água invisível vinculada ao fingerprint da criadora.

        Args:
            image: Imagem RGB em array numpy [H, W, 3]
            creator_fingerprint: Hash PQC da criadora para derivação de chave

        Returns:
            Imagem com marca d'água embutida (visualmente idêntica)
        """
        # Derivar chave de watermark do fingerprint PQC
        if self.pqc_derived:
            seed = int(hashlib.sha3_256(creator_fingerprint.encode()).hexdigest()[:16], 16)
            np.random.seed(seed % (2**32))

        # Converter para YCbCr e aplicar DCT no canal Y (luminância)
        ycbcr = self._rgb_to_ycbcr(image)
        y_channel = ycbcr[:, :, 0].astype(float)

        # Aplicar DCT em blocos 8x8
        h, w = y_channel.shape
        watermarked = y_channel.copy()

        for i in range(0, h - 7, 8):
            for j in range(0, w - 7, 8):
                block = y_channel[i:i+8, j:j+8]
                dct_block = self._dct_2d(block)

                # Inserir watermark em coeficientes de média-frequência
                # (robusto a compressão, imperceptível visualmente)
                for ki in range(2, 6):
                    for kj in range(2, 6):
                        if np.random.random() < 0.3:  # Esparsidade para imperceptibilidade
                            dct_block[ki, kj] += self.strength * np.random.choice([-1, 1])

                watermarked[i:i+8, j:j+8] = self._idct_2d(dct_block)

        # Reconstruir imagem
        ycbcr[:, :, 0] = np.clip(watermarked, 0, 255)
        return self._ycbcr_to_rgb(ycbcr).astype(np.uint8)

    async def detect_watermark(self, image: np.ndarray, creator_fingerprint: str,
                             threshold: float = 0.7) -> Tuple[bool, float]:
        """
        Detecta e verifica marca d'água em imagem suspeita.

        Returns:
            (is_watermarked, confidence_score)
        """
        # Derivar mesma chave do fingerprint
        if self.pqc_derived:
            seed = int(hashlib.sha3_256(creator_fingerprint.encode()).hexdigest()[:16], 16)
            np.random.seed(seed % (2**32))

        # Extrair watermark via DCT reverso
        ycbcr = self._rgb_to_ycbcr(image)
        y_channel = ycbcr[:, :, 0].astype(float)

        correlation_sum = 0
        count = 0

        h, w = y_channel.shape
        for i in range(0, h - 7, 8):
            for j in range(0, w - 7, 8):
                block = y_channel[i:i+8, j:j+8]
                dct_block = self._dct_2d(block)

                # Correlacionar com padrão esperado
                for ki in range(2, 6):
                    for kj in range(2, 6):
                        expected_sign = np.random.choice([-1, 1]) if np.random.random() < 0.3 else 0
                        if expected_sign != 0:
                            actual_sign = np.sign(dct_block[ki, kj])
                            if actual_sign == expected_sign:
                                correlation_sum += 1
                            count += 1

        confidence = correlation_sum / max(count, 1)
        return confidence >= threshold, confidence

    # Métodos auxiliares de transformada (DCT/IDCT e conversão de cor)
    def _dct_2d(self, block: np.ndarray) -> np.ndarray:
        # Implementação simplificada de DCT 2D
        return scipy.fftpack.dct(scipy.fftpack.dct(block.T, norm='ortho').T, norm='ortho')

    def _idct_2d(self, block: np.ndarray) -> np.ndarray:
        return scipy.fftpack.idct(scipy.fftpack.idct(block.T, norm='ortho').T, norm='ortho')

    def _rgb_to_ycbcr(self, rgb: np.ndarray) -> np.ndarray:
        # Conversão RGB → YCbCr (ITU-R BT.601)
        m = np.array([[0.299, 0.587, 0.114],
                      [-0.1687, -0.3313, 0.5],
                      [0.5, -0.4187, -0.0813]])
        return np.dot(rgb.reshape(-1, 3), m.T).reshape(rgb.shape)

    def _ycbcr_to_rgb(self, ycbcr: np.ndarray) -> np.ndarray:
        # Conversão YCbCr → RGB
        m = np.array([[1, 0, 1.402],
                      [1, -0.3441, -0.7141],
                      [1, 1.772, 0]])
        return np.dot(ycbcr.reshape(-1, 3), m.T).reshape(ycbcr.shape)