import socket
import time
import struct
import math

def send_sensor_data(conn):
    t = time.time_ns()
    # Simula IMU (Acelerômetro + Giroscópio)
    ax = math.sin(t / 1e6) * 9.8
    ay = math.cos(t / 1e6) * 9.8
    az = 9.8
    gx, gy, gz = 0.1, 0.2, 0.3

    # Empacota no formato do C (3 floats + 3 floats + 1 long)
    # float=4bytes, long=8bytes. Total = 32 bytes
    payload = struct.pack('<6fQ', ax, ay, az, gx, gy, gz, t)
    conn.sendall(payload)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('127.0.0.1', 12345))
server.listen(1)
print("[VirtIO Sensor Sim] Aguardando conexão do QEMU...")
conn, addr = server.accept()

print("[VirtIO Sensor Sim] Enviando stream de sensores...")
while True:
    send_sensor_data(conn)
    time.sleep(0.001) # 1000 Hz de simulação de hardware
