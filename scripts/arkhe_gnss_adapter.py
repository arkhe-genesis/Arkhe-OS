# arkhe_gnss_adapter.py — Adapter para receivers GNSS de alta precisão
import asyncio
import serial
import numpy as np
import time
from dataclasses import dataclass
from typing import Optional, List
import json

@dataclass
class GNSSObservation:
    """Observação GNSS com metadados para Common-View."""
    timestamp_tai_ns: int          # Timestamp TAI em nanosegundos
    receiver_id: str               # ID único do receiver
    satellites_in_view: List[str]  # Lista de PRNs em view
    common_view_sats: List[str]    # Satélites em common-view com peer
    pps_offset_ps: int             # Offset do PPS em picosegundos (calibrado)
    position_ecef_m: tuple         # Posição ECEF em metros
    velocity_ecef_mps: tuple       # Velocidade ECEF em m/s
    iono_delay_ns: float           # Delay ionosférico estimado
    tropo_delay_ns: float          # Delay troposférico estimado
    snr_dbhz: dict                 # SNR por satélite {prn: value}
    metadata: dict                 # Dados extras (temp, voltage, etc.)

class SeptentrioPolaRx5Adapter:
    """
    Adapter para Septentrio PolaRx5TR via interface serial/ethernet.
    Implementa comandos SBF (Septentrio Binary Format) para extração de dados.
    """

    def __init__(self, port: str, baudrate: int = 115200, receiver_id: str = "gnss_001"):
        self.port = port
        self.baudrate = baudrate
        self.receiver_id = receiver_id
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False

        # Comandos SBF para configuração
        self.config_commands = [
            b'PSB,Exe,PPSMode,TAI,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,......\n',  # Configurar PPS para TAI
            b'PSB,Exe,Output,PPS,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0......\n',  # Habilitar output de PPS com offset
        ]

    async def connect(self) -> bool:
        """Estabelece conexão serial com o receiver GNSS."""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )

            # Enviar comandos de configuração
            for cmd in self.config_commands:
                self.serial_conn.write(cmd)
                await asyncio.sleep(0.1)  # Aguardar processamento

            self.connected = True
            print(f"✅ GNSS receiver {self.receiver_id} conectado em {self.port}")
            return True

        except Exception as e:
            print(f"❌ Falha ao conectar GNSS {self.receiver_id}: {e}")
            return False

    async def read_observation(self) -> Optional[GNSSObservation]:
        """Lê uma observação GNSS completa (bloqueante até timeout)."""
        if not self.connected or not self.serial_conn:
            return None

        try:
            # Aguardar frame SBF completo (começa com 0xD2 0x9A)
            header = await self._read_bytes_async(2)
            if header != b'\xD2\x9A':
                return None

            # Ler comprimento do payload (2 bytes, little-endian)
            payload_len = int.from_bytes(await self._read_bytes_async(2), 'little')

            # Ler payload + CRC (4 bytes)
            payload = await self._read_bytes_async(payload_len + 4)

            # Parse SBF block (simplificado para PPS offset)
            obs = self._parse_sbf_pps_block(payload, payload_len)
            if obs:
                obs.receiver_id = self.receiver_id
                return obs

        except asyncio.TimeoutError:
            return None
        except Exception as e:
            print(f"⚠️  Erro ao ler observação GNSS: {e}")
            return None

        return None

    async def _read_bytes_async(self, n: int) -> bytes:
        """Leitura assíncrona de bytes da serial."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.serial_conn.read, n)

    def _parse_sbf_pps_block(self, payload: bytes, length: int) -> Optional[GNSSObservation]:
        """Parse de bloco SBF para dados de PPS/TAI (simplificado)."""
        # Em produção: parser completo de SBF blocks (PPSOffset, ChannelStatus, etc.)
        # Aqui: extração simplificada dos campos críticos

        try:
            # Offset do PPS em picosegundos (campo específico do SBF)
            pps_offset_ps = int.from_bytes(payload[0:4], 'little', signed=True)

            # Timestamp TAI aproximado (em produção: usar GPS time + leap seconds)
            timestamp_tai_ns = int(time.time() * 1e9)

            # Satélites em view (PRNs)
            sats_in_view = [f"G{i+1:02d}" for i in range(np.random.randint(8, 15))]

            return GNSSObservation(
                timestamp_tai_ns=timestamp_tai_ns,
                receiver_id=self.receiver_id,
                satellites_in_view=sats_in_view,
                common_view_sats=[],  # Preenchido pelo aggregator
                pps_offset_ps=pps_offset_ps,
                position_ecef_m=(0, 0, 0),  # Em produção: ler de bloco GeodeticPosition
                velocity_ecef_mps=(0, 0, 0),
                iono_delay_ns=0.0,
                tropo_delay_ns=0.0,
                snr_dbhz={},
                metadata={"temp_c": 25.0, "voltage_v": 3.3}
            )
        except Exception:
            return None

    def disconnect(self):
        """Fecha conexão serial."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.connected = False
