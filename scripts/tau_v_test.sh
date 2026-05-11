#!/bin/bash
PASS=0
FAIL=0
VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
AMARELO='\033[1;33m'
RESET='\033[0m'
log_sucesso() { echo -e "${VERDE}[PASS]${RESET} $1"; ((PASS++)); }
log_falha()   { echo -e "${VERMELHO}[FAIL]${RESET} $1"; ((FAIL++)); }
echo -e "${AMARELO}[IGNIS] Firebase${RESET}"
[ -f tau_v_test.sh ] && log_sucesso "Script exists" || log_falha "Script missing"
echo -e "PASS: $PASS | FAIL: $FAIL"
