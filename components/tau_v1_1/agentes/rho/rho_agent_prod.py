#!/usr/bin/env python3
"""
RHO Agent v1.2 — Production Deploy for Versal ACAP
Autor: Ferreiro & Guardião TP53
"""
import struct
import mmap
import os
import time
import select
import requests
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='[RHO] %(asctime)s %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES DE HARDWARE (devem casar com o RTL e Device Tree)
# ============================================================================
DDR_ROI_BASE = 0x40000000
RING_BUFFER_SIZE = 4 * 1024 * 1024  # 4 MiB
ROI_TOKEN_SIZE = 8
UIO_DEVICE = "/dev/uio0"
FIREBASE_URL = "https://tau-enxame.firebaseio.com/roi_tokens.json"

# ============================================================================
# SCAFFOLD: ROIToken (Σ)
# ============================================================================
@dataclass
class ROIToken:
    x: int; y: int; z: int
    is_red: bool; is_green: bool; is_blue: bool; is_high_intensity: bool
    intensity_msb: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "ROIToken":
        if len(data) != 8:
            raise ValueError(f"Esperado 8 bytes, recebido {len(data)}")
        x, y, z, intensity_msb, flags = struct.unpack('<HHHBB', data)
        return cls(
            x=x, y=y, z=z,
            is_red=bool(flags & 0x01),
            is_green=bool(flags & 0x02),
            is_blue=bool(flags & 0x04),
            is_high_intensity=bool(flags & 0x08),
            intensity_msb=intensity_msb
        )

    def to_dict(self) -> dict:
        return {
            "x": self.x, "y": self.y, "z": self.z,
            "flags": {
                "red": self.is_red, "green": self.is_green,
                "blue": self.is_blue, "high_intensity": self.is_high_intensity
            },
            "intensity_msb": self.intensity_msb,
            "timestamp": time.time()
        }

# ============================================================================
# AGENTE RHO (Γ + Δ)
# ============================================================================
class RHOAgent:
    def __init__(self):
        self.mm: mmap.mmap = None
        self.uio_fd: int = None
        self.read_ptr = 0
        self.frame_count = 0
        self.session = requests.Session()

    def setup_memory(self):
        try:
            mem_fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
            self.mm = mmap.mmap(
                mem_fd, RING_BUFFER_SIZE,
                mmap.MAP_SHARED, mmap.PROT_READ,
                offset=DDR_ROI_BASE
            )
            os.close(mem_fd)
            logger.info(f"DDR mapeada em 0x{DDR_ROI_BASE:X}")
        except Exception as e:
            logger.error(f"Falha ao mapear memória: {e}")

    def setup_interrupt(self):
        try:
            self.uio_fd = os.open(UIO_DEVICE, os.O_RDWR)
            os.write(self.uio_fd, struct.pack('I', 1))  # Habilita IRQ
            logger.info(f"UIO {UIO_DEVICE} configurado")
        except Exception as e:
            logger.error(f"Falha ao configurar UIO: {e}")

    def wait_for_frame(self, timeout_ms: int = 5000) -> bool:
        if self.uio_fd is None:
            time.sleep(1)
            return False
        poller = select.poll()
        poller.register(self.uio_fd, select.POLLIN)
        if poller.poll(timeout_ms):
            os.read(self.uio_fd, 4)  # ACK
            os.write(self.uio_fd, struct.pack('I', 1))  # Re-habilita
            return True
        return False

    def read_frame_tokens(self, max_tokens: int = 1024) -> list:
        if self.mm is None:
            return []
        tokens = []
        for _ in range(max_tokens):
            if self.read_ptr + ROI_TOKEN_SIZE > RING_BUFFER_SIZE:
                self.read_ptr = 0

            raw = self.mm[self.read_ptr:self.read_ptr + ROI_TOKEN_SIZE]
            if len(raw) < ROI_TOKEN_SIZE:
                break

            # Sentinela: zeros absolutos indicam fim de frame ou buffer vazio
            if raw == b'\x00\x00\x00\x00\x00\x00\x00\x00':
                self.read_ptr += ROI_TOKEN_SIZE
                break

            try:
                tokens.append(ROIToken.from_bytes(raw))
            except Exception as e:
                logger.error(f"Parse error: {e}")
                break

            self.read_ptr += ROI_TOKEN_SIZE

        self.frame_count += 1
        return tokens

    def publish_tokens(self, tokens: list):
        for token in tokens:
            try:
                # Publicação REST direta (sem Firebase Admin SDK)
                payload = token.to_dict()
                response = self.session.post(FIREBASE_URL, json=payload, timeout=5)
                if response.status_code == 200:
                    logger.debug(f"Token publicado: {token.x},{token.y},{token.z}")
                else:
                    logger.warning(f"HTTP {response.status_code} ao publicar")
            except Exception as e:
                logger.error(f"Falha de rede: {e}")

    def run(self):
        self.setup_memory()
        self.setup_interrupt()
        logger.info("RHO Agent iniciado. Aguardando frames do VRP...")

        while True:
            if self.wait_for_frame():
                tokens = self.read_frame_tokens()
                if tokens:
                    logger.info(f"Frame {self.frame_count}: {len(tokens)} tokens")
                    self.publish_tokens(tokens)
            else:
                logger.warning("Timeout aguardando IRQ — verificar VRP")

    def shutdown(self):
        if self.mm:
            self.mm.close()
        if self.uio_fd:
            os.close(self.uio_fd)

if __name__ == "__main__":
    agent = RHOAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("Shutdown solicitado")
        agent.shutdown()
