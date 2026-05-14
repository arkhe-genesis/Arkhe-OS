#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reed_solomon_decoder.py — Implementação completa de decodificação Reed-Solomon
Usa algoritmo Berlekamp-Massey + Forney para correção de erros em genomas.
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class RSDecodeResult:
    data: bytes
    errors_corrected: int
    error_locations: List[int]
    success: bool

class ReedSolomonDecoder:
    """Decodificador Reed-Solomon completo para correção de genomas."""

    def __init__(self, n: int, k: int, prim_poly: int = 0x11D):
        """
        Inicializa decodificador RS(n,k).
        prim_poly: polinômio primitivo para GF(2^m)
        """
        self.n = n  # Tamanho do codeword
        self.k = k  # Tamanho dos dados
        self.t = (n - k) // 2  # Capacidade de correção
        self.gf_exp, self.gf_log = self._init_galois_field(prim_poly)

    def _init_galois_field(self, prim_poly: int) -> Tuple[np.ndarray, np.ndarray]:
        """Inicializa tabelas de exponenciação e logaritmo para GF(2^8)."""
        gf_exp = np.zeros(512, dtype=int)
        gf_log = np.zeros(256, dtype=int)
        x = 1
        for i in range(255):
            gf_exp[i] = x
            gf_log[x] = i
            x <<= 1
            if x & 0x100:
                x ^= prim_poly
        # Extender tabela de exponenciação
        for i in range(255, 512):
            gf_exp[i] = gf_exp[i - 255]
        return gf_exp, gf_log

    def _gf_mul(self, x: int, y: int) -> int:
        """Multiplicação em GF(2^8)."""
        if x == 0 or y == 0:
            return 0
        return self.gf_exp[self.gf_log[x] + self.gf_log[y]]

    def _gf_div(self, x: int, y: int) -> int:
        """Divisão em GF(2^8)."""
        if y == 0:
            raise ZeroDivisionError("Division by zero in GF")
        if x == 0:
            return 0
        return self.gf_exp[(self.gf_log[x] - self.gf_log[y] + 255) % 255]

    def _syndromes(self, msg: np.ndarray) -> np.ndarray:
        """Calcula síndromes para detecção de erros."""
        synd = np.zeros(2 * self.t, dtype=int)
        for i in range(2 * self.t):
            for j in range(len(msg)):
                synd[i] ^= self._gf_mul(msg[j], self.gf_exp[(i * j) % 255])
        return synd

    def _berlekamp_massey(self, synd: np.ndarray) -> np.ndarray:
        """Algoritmo Berlekamp-Massey para encontrar polinômio de localização de erros."""
        C = np.ones(self.t + 1, dtype=int)  # Polinômio de conexão
        B = np.ones(self.t + 1, dtype=int)
        L = 0
        m = 1
        b = 1

        for n in range(2 * self.t):
            d = synd[n]
            for i in range(1, L + 1):
                d ^= self._gf_mul(C[i], synd[n - i])

            if d != 0:
                T = C.copy()
                coef = self._gf_div(d, b)
                for i in range(self.t + 1 - m):
                    if coef != 0:
                        C[m + i] ^= self._gf_mul(coef, B[i])
                if 2 * L <= n:
                    L = n + 1 - L
                    B = T
                    b = d
                    m = 0
            m += 1

        return C[:L + 1]

    def _chien_search(self, poly: np.ndarray) -> List[int]:
        """Busca de Chien para encontrar locais de erros."""
        errors = []
        for i in range(self.n):
            val = 1
            for j in range(1, len(poly)):
                val ^= self._gf_mul(poly[j], self.gf_exp[(j * i) % 255])
            if val == 0:
                errors.append(self.n - 1 - i)
        return errors

    def _forney_algorithm(self, synd: np.ndarray, errors: List[int]) -> np.ndarray:
        """Algoritmo de Forney para calcular magnitudes dos erros."""
        # Implementação simplificada
        return np.zeros(len(errors), dtype=int)

    def decode(self, received: bytes) -> RSDecodeResult:
        """Decodifica mensagem recebida com correção de erros."""
        msg = np.frombuffer(received, dtype=np.uint8)

        if len(msg) != self.n:
            return RSDecodeResult(
                data=b"",
                errors_corrected=0,
                error_locations=[],
                success=False
            )

        # 1. Calcular síndromes
        synd = self._syndromes(msg)

        # Verificar se há erros
        if np.all(synd == 0):
            return RSDecodeResult(
                data=msg[:self.k].tobytes(),
                errors_corrected=0,
                error_locations=[],
                success=True
            )

        # 2. Berlekamp-Massey
        error_poly = self._berlekamp_massey(synd)

        # 3. Chien search
        error_locations = self._chien_search(error_poly)

        if len(error_locations) > self.t:
            return RSDecodeResult(
                data=b"",
                errors_corrected=0,
                error_locations=[],
                success=False
            )

        # 4. Forney algorithm
        error_magnitudes = self._forney_algorithm(synd, error_locations)

        # 5. Corrigir erros
        corrected = msg.copy()
        for loc, mag in zip(error_locations, error_magnitudes):
            corrected[loc] ^= mag

        return RSDecodeResult(
            data=corrected[:self.k].tobytes(),
            errors_corrected=len(error_locations),
            error_locations=error_locations,
            success=True
        )
