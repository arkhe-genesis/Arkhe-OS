#!/bin/bash
VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
AMARELO='\033[1;33m'
CIANO='\033[0;36m'
RESET='\033[0m'
PASS=0
FAIL=0
log_sucesso() { echo -e "${VERDE}[PASS]${RESET} $1"; ((PASS++)); }
log_falha()   { echo -e "${VERMELHO}[FAIL]${RESET} $1"; ((FAIL++)); }
echo "TAU v1.1 VALIDATION"
echo -e "\n${AMARELO}[IGNIS] Firebase${RESET}"
if [ -f tau_v1_1/secrets/serviceAccountKey.json ]; then log_sucesso "serviceAccountKey.json"; else log_falha "serviceAccountKey.json"; fi
if grep -q "DATABASE_URL" tau_v1_1/secrets/.env 2>/dev/null; then log_sucesso "DATABASE_URL"; else log_falha "DATABASE_URL"; fi
echo -e "\n${AMARELO}[AER] Telegram${RESET}"
if [ -f tau_v1_1/telegram/delta_webhook.py ]; then log_sucesso "delta_webhook.py"; else log_falha "delta_webhook.py"; fi
echo -e "\n${AMARELO}[AETHER] IOTA${RESET}"
if [ -f tau_v1_1/iota/council_vote.py ]; then log_sucesso "council_vote.py"; else log_falha "council_vote.py"; fi
echo -e "\n${AMARELO}[INFRA] Recursos${RESET}"
RAM_LIVRE=$(free -m | awk '/^Mem:/{print $7}')
if [ "$RAM_LIVRE" -gt 200 ]; then log_sucesso "RAM > 200MB ($RAM_LIVRE)"; else log_falha "RAM low"; fi
echo -e "\nPASS: $PASS | FAIL: $FAIL"
