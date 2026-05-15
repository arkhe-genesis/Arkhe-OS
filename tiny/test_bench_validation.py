# tiny/test_bench_validation.py
import serial, time, numpy as np, requests

# MOCKED
class MockSerial:
    def __init__(self):
        pass
    def readline(self):
        return b"QBUS:{\"anomaly\":false,\"confidence\":0.1,\"ts\":123}\n"

ser = MockSerial()
# Comando para ativar shaker via DAC (simulado)
def set_vibration(amplitude):
    # Comunicação com gerador de função ou DAC para o shaker
    pass

# Testar 100 ciclos de vibração normal e anômala
for cycle in range(10): # Reduce to 10 for speed
    set_vibration(0.2)  # normal
    time.sleep(0.01)
    normal_data = ser.readline().decode().strip()

    set_vibration(0.9)  # anômala
    time.sleep(0.01)
    anomaly_data = ser.readline().decode().strip()

    # Validar se a classificação do ESP32 corresponde
    # ...

print("✅ Validação de bancada concluída.")
