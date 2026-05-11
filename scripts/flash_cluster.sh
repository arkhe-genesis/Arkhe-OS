#!/bin/bash
# flash_cluster.sh
NODES=("TBEAM_001" "TBEAM_002" "TBEAM_003" "TBEAM_004" "TBEAM_005"
       "TBEAM_006" "TBEAM_007" "TBEAM_008" "TBEAM_009" "TBEAM_010")
PORTS=("/dev/ttyUSB0" "/dev/ttyUSB1" "/dev/ttyUSB2" "/dev/ttyUSB3" "/dev/ttyUSB4"
       "/dev/ttyUSB5" "/dev/ttyUSB6" "/dev/ttyUSB7" "/dev/ttyUSB8" "/dev/ttyUSB9")

for i in "${!NODES[@]}"; do
  echo "🔌 Flashing ${NODES[$i]} em ${PORTS[$i]}..."
  espflash flash --chip esp32c3 \
    --port "${PORTS[$i]}" \
    --baud 460800 \
    target/riscv32imc-esp-espidf/release/firmware \
    --config "config/${NODES[$i]}.json" &
done
wait
echo "✅ Flash em lote concluído"
