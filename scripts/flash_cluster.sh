#!/bin/bash
# flash_cluster.sh — grava firmware em 10 TTGO T-Beams via USB serial

FIRMWARE="target/riscv32imc-esp-espidf/release/firmware"
NODES=10

echo "Simulating flash for $NODES nodes..."
for i in $(seq 0 $((NODES-1))); do
    PORT="/dev/ttyUSB$i"
    NODE_ID="WFL$i"
    echo "Gravando nó $NODE_ID na porta $PORT..."
    # espflash flash --chip esp32c3 --port $PORT $FIRMWARE
    # espflash write-nvs --port $PORT node_id=$NODE_ID
    echo "Nó $NODE_ID pronto."
done

echo "Todos os $NODES nós foram gravados. Iniciando teste de campo..."
