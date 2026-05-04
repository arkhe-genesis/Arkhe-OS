#!/bin/bash
# setup_sync_lab.sh — Provisionamento do ambiente de validação de sincronização

echo "⏱️ ARKHE Global Sync Lab Setup"
echo "Instalando dependências..."

pip install numpy scipy matplotlib pandas plotly dash
pip install pyserial pyvisa-py pyvisa-sim  # para comunicação serial com dispositivos
pip install pysnmp                       # para White Rabbit MIBs
pip install ntplib                       # fallback NTP

mkdir -p sync_data
echo "✅ Ambiente pronto. Execute: python3 arkhe_sync_collector.py"
