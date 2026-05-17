#!/usr/bin/env python3
"""
Substrato 198-F: Optogenetics Platform Adapter
Interface para controle de hardware optogenético real (DMD, LEDs, microscópios).
Traduz campos vetoriais 3D em padrões de luz executáveis em laboratório.
"""
import asyncio
import numpy as np
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Union
from enum import Enum, auto
import logging
import json
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptogeneticHardware(Enum):
    """Tipos de hardware optogenético suportados."""
    DMD_PROJECTOR = "dmd_projector"          # Digital Micromirror Device
    LED_ARRAY = "led_array"                   # Matriz de LEDs programáveis
    LASER_SCANNER = "laser_scanner"           # Scanner de laser galvo/resonant
    SPATIAL_LIGHT_MODULATOR = "slm"           # Modulador de luz espacial
    MICROSCOPE_INTEGRATED = "microscope_integrated"  # Sistema comercial (ex: Mightex, Mightex Polygon)

@dataclass
class HardwareConfig:
    """Configuração específica do hardware optogenético."""
    hardware_type: OptogeneticHardware
    wavelength_nm: float                      # Comprimento de onda de ativação
    max_power_mw_mm2: float                   # Potência máxima segura
    spatial_resolution_um: float              # Resolução espacial mínima
    temporal_resolution_ms: float             # Resolução temporal mínima
    field_of_view_mm: Tuple[float, float]     # Campo de visão (largura, altura)
    z_stack_support: bool                     # Suporte a focalização em Z
    calibration_file: Optional[str] = None    # Arquivo de calibração do hardware

@dataclass
class LightPattern:
    """Padrão de luz gerado a partir de campo vetorial 3D."""
    pattern_id: str
    wavelength_nm: float
    intensity_map: np.ndarray                 # 2D ou 3D array de intensidades [0, 1]
    duration_ms: float
    z_planes: Optional[List[float]] = None    # Posições Z para padrão 3D
    metadata: Dict = field(default_factory=dict)

    def to_hardware_command(self, config: HardwareConfig) -> Dict:
        """Converte padrão para comando específico do hardware."""
        # Normalizar intensidade para faixa do hardware
        normalized = np.clip(self.intensity_map * config.max_power_mw_mm2, 0, config.max_power_mw_mm2)

        if config.hardware_type == OptogeneticHardware.DMD_PROJECTOR:
            # DMD: padrão binário ou grayscale via PWM
            return {
                "command": "display_pattern",
                "pattern_data": (normalized * 255).astype(np.uint8).tolist(),
                "duration_ms": self.duration_ms,
                "wavelength_nm": self.wavelength_nm,
                "z_position": self.z_planes[0] if self.z_planes else None,
            }
        elif config.hardware_type == OptogeneticHardware.LED_ARRAY:
            # LED array: ativar LEDs específicos com intensidade
            return {
                "command": "set_led_intensities",
                "led_matrix": normalized.tolist(),
                "duration_ms": self.duration_ms,
            }
        elif config.hardware_type == OptogeneticHardware.LASER_SCANNER:
            # Laser scanner: lista de pontos com intensidade
            points = np.argwhere(normalized > 0.1)  # Threshold para eficiência
            return {
                "command": "scan_points",
                "points": points.tolist(),
                "intensities": normalized[normalized > 0.1].tolist(),
                "dwell_time_us": int(config.temporal_resolution_ms * 100),
                "wavelength_nm": self.wavelength_nm,
            }
        else:
            # Fallback genérico
            return {
                "command": "apply_pattern",
                "intensity_map": normalized.tolist(),
                "duration_ms": self.duration_ms,
                "wavelength_nm": self.wavelength_nm,
            }

class OptogeneticsPlatformAdapter:
    """
    Adaptador para controle de hardware optogenético real.

    Funcionalidades:
    • Tradução de campos vetoriais 3D → padrões de luz executáveis
    • Calibração automática de intensidade/resolução por hardware
    • Controle assíncrono de múltiplos dispositivos
    • Monitoramento em tempo real de parâmetros de segurança
    • Logging completo para auditoria experimental
    """

    # Limites de segurança para experimentos biológicos
    SAFETY_LIMITS = {
        "max_irradiance_mw_mm2": 10.0,        # Limite para viabilidade celular
        "max_exposure_time_s": 300,            # 5 minutos máximo contínuo
        "min_recovery_time_s": 60,             # 1 minuto entre exposições
        "temperature_max_celsius": 38.0,       # Limite térmico
    }

    def __init__(
        self,
        config: HardwareConfig,
        connection_params: Optional[Dict] = None,
        safety_monitor: Optional[Callable] = None,
    ):
        self.config = config
        self.connection_params = connection_params or {}
        self.safety_monitor = safety_monitor
        self._connected = False
        self._last_exposure_time: Optional[float] = None
        self._exposure_log: List[Dict] = []

    async def connect(self) -> bool:
        """Estabelece conexão com hardware optogenético."""
        try:
            # Simulação de conexão (em produção: usar biblioteca do fabricante)
            await asyncio.sleep(0.2)

            # Carregar calibração se disponível
            if self.config.calibration_file:
                await self._load_calibration(self.config.calibration_file)

            self._connected = True
            logger.info(f"✅ Conectado a {self.config.hardware_type.value} @ {self.config.wavelength_nm}nm")
            return True

        except Exception as e:
            logger.error(f"❌ Falha ao conectar: {e}")
            return False

    async def _load_calibration(self, calibration_file: str):
        """Carrega arquivo de calibração do hardware."""
        # Em produção: carregar matriz de correção, curva de resposta, etc.
        logger.info(f"🔧 Calibração carregada: {calibration_file}")

    async def apply_field_as_light(
        self,
        field_3d: np.ndarray,                    # Campo vetorial [W, H, D, 3]
        target_z_position: Optional[float] = None,
        duration_ms: float = 1000,
        safety_check: bool = True,
    ) -> bool:
        """
        Aplica campo vetorial 3D como padrão de luz no hardware.

        Args:
            field_3d: Campo vetorial do P2I
            target_z_position: Posição Z focal (se suportado)
            duration_ms: Duração da exposição
            safety_check: Executar verificações de segurança

        Returns:
            True se aplicação bem-sucedida
        """
        if not self._connected:
            logger.error("❌ Hardware não conectado")
            return False

        # Verificações de segurança
        if safety_check:
            if not await self._safety_check(duration_ms, field_3d):
                logger.warning("⚠️  Aplicação bloqueada por limites de segurança")
                return False

        # Converter campo para padrão de luz
        light_pattern = await self._field_to_light_pattern(field_3d, target_z_position, duration_ms)

        # Gerar comando específico do hardware
        hardware_command = light_pattern.to_hardware_command(self.config)

        # Executar comando (simulado)
        success = await self._execute_hardware_command(hardware_command)

        if success:
            # Registrar exposição
            self._exposure_log.append({
                "timestamp": time.time(),
                "pattern_id": light_pattern.pattern_id,
                "duration_ms": duration_ms,
                "max_intensity": float(np.max(light_pattern.intensity_map)),
                "z_position": target_z_position,
            })
            self._last_exposure_time = time.time()
            logger.info(f"💡 Padrão aplicado: {light_pattern.pattern_id} ({duration_ms}ms)")

        return success

    async def _field_to_light_pattern(
        self,
        field_3d: np.ndarray,
        z_position: Optional[float],
        duration_ms: float,
    ) -> LightPattern:
        """Converte campo vetorial 3D em padrão de luz executável."""
        # Extrair magnitude do campo como intensidade luminosa
        intensity = np.linalg.norm(field_3d, axis=-1)

        # Normalizar para [0, 1]
        if np.max(intensity) > 0:
            intensity = intensity / np.max(intensity)

        # Se hardware não suporta Z-stack, projetar para plano focal
        if not self.config.z_stack_support and field_3d.ndim == 4:
            # Média ao longo do eixo Z ou slice no plano alvo
            if z_position is not None:
                # Encontrar índice Z mais próximo
                z_idx = int(np.clip(
                    z_position / self.config.field_of_view_mm[1] * field_3d.shape[2],
                    0, field_3d.shape[2] - 1
                ))
                intensity = intensity[:, :, z_idx]
            else:
                intensity = np.mean(intensity, axis=2)  # Projeção média

        # Gerar ID único para o padrão
        pattern_id = hashlib.sha3_256(
            f"{intensity.tobytes()}:{duration_ms}:{z_position}".encode()
        ).hexdigest()[:12]

        return LightPattern(
            pattern_id=pattern_id,
            wavelength_nm=self.config.wavelength_nm,
            intensity_map=intensity,
            duration_ms=duration_ms,
            z_planes=[z_position] if z_position and self.config.z_stack_support else None,
            metadata={
                "source_field_shape": field_3d.shape,
                "conversion_method": "magnitude_projection",
            }
        )

    async def _safety_check(self, duration_ms: float, field_3d: np.ndarray) -> bool:
        """Executa verificações de segurança antes da exposição."""
        # Verificar tempo desde última exposição
        if self._last_exposure_time:
            elapsed = time.time() - self._last_exposure_time
            if elapsed < self.SAFETY_LIMITS["min_recovery_time_s"]:
                logger.warning(f"⚠️  Tempo de recuperação insuficiente: {elapsed:.1f}s < {self.SAFETY_LIMITS['min_recovery_time_s']}s")
                return False

        # Verificar duração máxima
        if duration_ms > self.SAFETY_LIMITS["max_exposure_time_s"] * 1000:
            logger.warning(f"⚠️  Exposição muito longa: {duration_ms}ms > {self.SAFETY_LIMITS['max_exposure_time_s']*1000}ms")
            return False

        # Verificar intensidade máxima
        intensity = np.linalg.norm(field_3d, axis=-1)
        max_intensity = np.max(intensity)
        if max_intensity > self.SAFETY_LIMITS["max_irradiance_mw_mm2"]:
            logger.warning(f"⚠️  Intensidade excede limite: {max_intensity} > {self.SAFETY_LIMITS['max_irradiance_mw_mm2']}")
            return False

        # Callback externo para monitoramento adicional
        if self.safety_monitor:
            return await self.safety_monitor({
                "duration_ms": duration_ms,
                "max_intensity": float(max_intensity),
                "field_shape": field_3d.shape,
            })

        return True

    async def _execute_hardware_command(self, command: Dict) -> bool:
        """Executa comando no hardware (simulado)."""
        # Em produção: enviar via socket/serial/API do fabricante
        await asyncio.sleep(command.get("duration_ms", 100) / 1000 * 0.1)  # Simular latência
        return True

    async def disconnect(self):
        """Encerra conexão com hardware."""
        if self._connected:
            # Comando de shutdown seguro
            await asyncio.sleep(0.1)
            self._connected = False
            logger.info("✅ Hardware desconectado")

    def get_exposure_log(self, time_window_hours: float = 24) -> List[Dict]:
        """Retorna log de exposições dentro da janela de tempo."""
        cutoff = time.time() - (time_window_hours * 3600)
        return [e for e in self._exposure_log if e["timestamp"] >= cutoff]

    def get_safety_status(self) -> Dict:
        """Retorna status atual de segurança do sistema."""
        return {
            "connected": self._connected,
            "last_exposure": self._last_exposure_time,
            "recovery_time_remaining": max(
                0,
                self.SAFETY_LIMITS["min_recovery_time_s"] -
                (time.time() - (self._last_exposure_time or 0))
            ),
            "exposures_last_24h": len(self.get_exposure_log(24)),
            "limits": self.SAFETY_LIMITS,
        }
