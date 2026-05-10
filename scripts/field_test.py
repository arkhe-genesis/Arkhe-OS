import serial
import time
import json
import numpy as np
from collections import deque

class FieldTestValidator:
    def __init__(self, port: str, baud: int = 115200, timeout: float = 5.0):
        self.ser = serial.Serial(port, baud, timeout=timeout)
        self.metrics = deque(maxlen=100)

    def listen(self, duration_s: float = 300.0) -> list:
        """Ouve mensagens do nó por duration_s segundos."""
        start = time.time()
        messages = []

        while time.time() - start < duration_s:
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("Wakefield|"):
                    # Parse: "Wakefield | gap=2.34 hall=0 final=L1 | cache_entries=42"
                    parts = line.split('|')
                    if len(parts) >= 3:
                        gap = float(parts[0].split('=')[1].strip())
                        hall = parts[1].split('=')[1].strip() == '1'
                        finality = parts[2].split('=')[1].strip()
                        messages.append({
                            'timestamp': time.time(),
                            'gap': gap,
                            'hallucination': hall,
                            'finality': finality
                        })
                        self.metrics.append(gap)
        return messages

    def analyze(self, messages: list) -> dict:
        """Analisa métricas coletadas em campo."""
        if not messages:
            return {'error': 'No messages received'}

        gaps = [m['gap'] for m in messages]
        return {
            'messages_received': len(messages),
            'avg_gap': np.mean(gaps),
            'std_gap': np.std(gaps),
            'min_gap': np.min(gaps),
            'max_gap': np.max(gaps),
            'hallucination_rate': np.mean([m['hallucination'] for m in messages]),
            'finality_distribution': {
                f: sum(1 for m in messages if m['finality'] == f)
                for f in set(m['finality'] for m in messages)
            }
        }

# Uso: validar um nó em campo
if __name__ == "__main__":
    validator = FieldTestValidator(port="/dev/ttyUSB0")
    print("🔍 Ouvindo nó por 5 minutos...")
    messages = validator.listen(duration_s=300.0)
    analysis = validator.analyze(messages)

    print("\n📊 Resultados do Teste de Campo:")
    for k, v in analysis.items():
        print(f"  {k}: {v}")

    # Salvar para relatório
    with open(f"field_test_{int(time.time())}.json", 'w') as f:
        json.dump({'messages': messages, 'analysis': analysis}, f, indent=2)
