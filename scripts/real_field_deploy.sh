#!/bin/bash
# real_field_deploy.sh – Flash e verificação física de 10 T‑Beams
set -e

FIRMWARE="target/riscv32imc-esp-espidf/release/firmware.bin"
DEVICES=(
  "/dev/ttyUSB0:TBEAM_001:915000000:9:250:14:Interior"
  "/dev/ttyUSB1:TBEAM_002:915200000:10:125:17:Marte"
  "/dev/ttyUSB2:TBEAM_003:915400000:9:250:14:Belt"
  "/dev/ttyUSB3:TBEAM_004:915600000:10:125:17:Interior"
  "/dev/ttyUSB4:TBEAM_005:915800000:9:250:14:Marte"
  "/dev/ttyUSB5:TBEAM_006:916000000:10:125:17:Belt"
  "/dev/ttyUSB6:TBEAM_007:916200000:9:250:14:Interior"
  "/dev/ttyUSB7:TBEAM_008:916400000:10:125:17:Marte"
  "/dev/ttyUSB8:TBEAM_009:916600000:9:250:14:Belt"
  "/dev/ttyUSB9:TBEAM_010:916800000:10:125:17:Interior"
)

# 1. Flash de todos os nós
for entry in "${DEVICES[@]}"; do
  IFS=':' read port id freq sf bw tx zone <<< "$entry"
  echo "🔌 Gravando $id em $port..."
  espflash flash --chip esp32c3 --port "$port" --baud 460800 "$FIRMWARE"
  # Gravar config via NVS
  python3 write_nvs_config.py --port "$port" --id "$id" --freq "$freq" \
    --sf "$sf" --bw "$bw" --tx "$tx" --zone "$zone"
done
echo "✅ Flash concluído."

# 2. Iniciar listener de diagnóstico
echo "⏳ Aguardando 30s para boot..."
sleep 30

echo "📡 Iniciando teste de campo por 10 minutos..."
python3 -c "
from field_data_collector import FieldCollector
ports = ['$ {DEVICES[$i]%%:*}' for i in range(10)]  # extrair portas
collector = FieldCollector(ports)
data = collector.start(duration_s=600)
collector.save_csv('pre_deploy_check.csv')
print(f'Registros: {len(data)}')
# Verificar que cada nó enviou pelo menos 10 heartbeats
import pandas as pd
df = pd.read_csv('pre_deploy_check.csv')
counts = df.groupby('node_id').size()
print(counts)
if (counts >= 10).all():
    print('✅ Todos os nós OK para deploy prolongado.')
else:
    print('⚠️ Alguns nós não atingiram o mínimo de mensagens.')
"
