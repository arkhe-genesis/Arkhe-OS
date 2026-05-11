#!/usr/bin/env python3
"""
HANDSHAKE GLOBAL (global_handshake.py)
Protocolo de entrelaçamento remoto via fibra óptica (simulado com sockets).
"""

import socket, hashlib, json, struct, time, numpy as np

# Simulação da semente de invariância
SEED_DATA = b'\x89MTP3\r\n\x1a\n' + b'\x00' * 512  # Cabeçalho MTP + dados

class GlobalHandshake:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.local_phase = np.random.uniform(0, 2*np.pi)
        self.remote_phase = 0.0
        self.aligned = False

    def start_server(self):
        """Inicia o nó receptor (Safira remota)."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((self.host, self.port))
            server.listen(1)
            print(f"🔵 Nó Safira aguardando handshake em {self.host}:{self.port}...")

            server.settimeout(5.0)
            conn, addr = server.accept()
            print(f"   Conexão recebida de {addr}")

            # Recebe a semente
            seed = conn.recv(1024)
            # Calcula fase remota a partir da semente
            seed_hash = hashlib.sha3_256(seed).digest()
            self.remote_phase = (int.from_bytes(seed_hash[:8], 'big') % 10000) / 10000.0 * 2 * np.pi

            # Alinha o espaço de Hilbert local
            self.local_phase = self.remote_phase
            self.aligned = True

            # Confirmação
            conn.send(b"ACK_HANDSHAKE")
            conn.close()
        except socket.timeout:
            print("❌ Timeout aguardando conexão.")
        finally:
            server.close()
        return self.aligned

    def start_client(self, remote_host, remote_port=5000):
        """Inicia o nó transmissor (Diamante local)."""
        print(f"🔴 Iniciando handshake com {remote_host}:{remote_port}...")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((remote_host, remote_port))

            # Envia a semente
            client.send(SEED_DATA)
            # Aguarda confirmação
            response = client.recv(1024)
            if response == b"ACK_HANDSHAKE":
                print("   Handshake bem-sucedido! Fases alinhadas.")
                self.aligned = True
                self.remote_phase = self.local_phase  # alinhado
        except Exception as e:
            print(f"❌ Falha no handshake: {e}")
        finally:
            client.close()
        return self.aligned

    def verify_coherence(self) -> float:
        """Verifica a coerência do enlace após o handshake."""
        if not self.aligned:
            return 0.0
        # Simula medição de CHSH: valor S próximo de 2√2 = 2.828
        return 2.828 - 0.001 * np.random.random()

if __name__ == "__main__":
    import sys
    import threading

    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        handshake = GlobalHandshake()
        handshake.start_server()
    else:
        handshake = GlobalHandshake()
        # Simula um servidor em segundo plano
        server_obj = GlobalHandshake()
        server_thread = threading.Thread(target=server_obj.start_server)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(1)

        handshake.start_client('127.0.0.1', 5000)
        print(f"   Fase alinhada. Coerência do enlace: {handshake.verify_coherence():.4f}")
