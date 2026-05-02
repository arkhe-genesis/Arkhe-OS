# arkhe_wr_adapter.py — Adapter para switches White Rabbit
import asyncio
import socket
import struct
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class WRLinkStatus:
    """Status de um link White Rabbit."""
    link_id: str                    # ID único do link (ex: "wr_lisbon_toky0_01")
    local_port: str                 # Porta local do switch
    remote_node: str                # Nó remoto conectado
    sync_locked: bool               # PLL travado?
    link_up: bool                   # Link físico ativo?
    fiber_asymmetry_ps: int         # Assimetria de fibra calibrada (ps)
    phase_offset_ps: int            # Offset de fase residual (ps)
    jitter_rms_ps: int              # Jitter RMS medido (ps)
    temperature_c: float            # Temperatura do SFP/module
    timestamp_tai_ns: int           # Timestamp da medição

class SevenSolutionsWRAdapter:
    """
    Adapter para switches White Rabbit Seven Solutions via interface ethernet.
    Implementa protocolo WR-PTP para leitura de status e calibração DDMTD.
    """

    def __init__(self, switch_ip: str, switch_port: int = 1234, node_id: str = "wr_switch_001"):
        self.switch_ip = switch_ip
        self.switch_port = switch_port
        self.node_id = node_id
        self.sock: Optional[socket.socket] = None
        self.connected = False

        # Comandos WR-PTP (simplificados)
        self.cmd_get_status = b'\x01\x00\x00\x00'  # GET_LINK_STATUS
        self.cmd_ddmtd_calib = b'\x02\x00\x00\x00'  # START_DDMTD_CALIBRATION

    async def connect(self) -> bool:
        """Estabelece conexão TCP com o switch WR."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            await asyncio.get_event_loop().run_in_executor(
                None, self.sock.connect, (self.switch_ip, self.switch_port)
            )
            self.connected = True
            print(f"✅ WR switch {self.node_id} conectado em {self.switch_ip}:{self.switch_port}")
            return True
        except Exception as e:
            print(f"❌ Falha ao conectar WR switch {self.node_id}: {e}")
            return False

    async def get_link_status(self, link_id: str) -> Optional[WRLinkStatus]:
        """Obtém status de um link White Rabbit específico."""
        if not self.connected or not self.sock:
            return None

        try:
            # Enviar comando GET_LINK_STATUS com link_id
            cmd = self.cmd_get_status + link_id.encode('ascii').ljust(32, b'\x00')
            await asyncio.get_event_loop().run_in_executor(None, self.sock.sendall, cmd)

            # Aguardar resposta (formato binário definido pelo fabricante)
            response = await asyncio.get_event_loop().run_in_executor(None, self.sock.recv, 256)

            # Parse da resposta (exemplo simplificado)
            if len(response) >= 64:
                # Extrair campos do binário (little-endian)
                sync_locked = bool(response[0] & 0x01)
                link_up = bool(response[0] & 0x02)
                fiber_asymmetry_ps = struct.unpack('<i', response[4:8])[0]
                phase_offset_ps = struct.unpack('<i', response[8:12])[0]
                jitter_rms_ps = struct.unpack('<I', response[12:16])[0]
                temperature_c = struct.unpack('<f', response[16:20])[0]
                timestamp_tai_ns = struct.unpack('<Q', response[24:32])[0]

                return WRLinkStatus(
                    link_id=link_id,
                    local_port="SFP1",  # Em produção: ler do comando
                    remote_node="peer_node",  # Em produção: ler do comando
                    sync_locked=sync_locked,
                    link_up=link_up,
                    fiber_asymmetry_ps=fiber_asymmetry_ps,
                    phase_offset_ps=phase_offset_ps,
                    jitter_rms_ps=jitter_rms_ps,
                    temperature_c=temperature_c,
                    timestamp_tai_ns=timestamp_tai_ns
                )

        except Exception as e:
            print(f"⚠️  Erro ao ler status WR link {link_id}: {e}")
            return None

        return None

    async def start_ddmtd_calibration(self, link_id: str) -> bool:
        """Inicia calibração DDMTD para medir assimetria de fibra."""
        if not self.connected or not self.sock:
            return False

        try:
            # Enviar comando START_DDMTD_CALIBRATION
            cmd = self.cmd_ddmtd_calib + link_id.encode('ascii').ljust(32, b'\x00')
            await asyncio.get_event_loop().run_in_executor(None, self.sock.sendall, cmd)

            # Aguardar confirmação (simplificado)
            response = await asyncio.get_event_loop().run_in_executor(None, self.sock.recv, 16)
            return response[0] == 0x01  # ACK

        except Exception as e:
            print(f"⚠️  Erro ao iniciar calibração DDMTD para {link_id}: {e}")
            return False

    def disconnect(self):
        """Fecha conexão TCP."""
        if self.sock:
            self.sock.close()
            self.connected = False
