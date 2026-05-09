#!/bin/bash
# run_demo.sh — Executa pipeline híbrido Moonlab + Catedral Arkhe
# Uso: ./run_demo.sh [--benchmark] [--audit] [--report]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   CATEDRAL ARKHE × MOONLAB — PIPELINE UNIFICADO  ║${NC}"
echo -e "${GREEN}║   Odômetro: 001646 | Versão: 2.6.1               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo

# Parse de argumentos
RUN_BENCHMARK=false
RUN_AUDIT=false
GENERATE_REPORT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --benchmark)
            RUN_BENCHMARK=true
            shift
            ;;
        --audit)
            RUN_AUDIT=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        *)
            echo "Uso: $0 [--benchmark] [--audit] [--report]"
            exit 1
            ;;
    esac
done

# 1. Compilar código C
echo -e "${YELLOW}[1/4] Compilando código C...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

mkdir -p build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j
cd ..
echo -e "${GREEN}[✓] Compilação concluída${NC}"

# 2. Executar demo principal
echo -e "${YELLOW}[2/4] Executando demo híbrida...${NC}"
python3 python/hybrid_demo.py
echo

# 3. Executar demo C
echo -e "${YELLOW}[2.1/4] Executando demo C...${NC}"
./build/cathedral_main
echo

# 4. Executar benchmark (opcional)
if [ "$RUN_BENCHMARK" = true ]; then
    echo -e "${YELLOW}[3/4] Executando benchmark de hesitação...${NC}"
    python3 python/benchmark_hesitation.py
    echo
fi

# 5. Executar auditoria e gerar relatório (opcional)
if [ "$RUN_AUDIT" = true ] || [ "$GENERATE_REPORT" = true ]; then
    echo -e "${YELLOW}[4/4] Executando protocolo de auditoria...${NC}"
    python3 python/audit_protocol.py

    if [ "$GENERATE_REPORT" = true ]; then
        echo
        echo -e "${GREEN}[✓] Relatório de auditoria (JSON):${NC}"
        python3 -c "import sys; sys.path.append('python'); from audit_protocol import demo_audit_protocol; import json; print(json.dumps(demo_audit_protocol().to_dict(), indent=2))"
    fi
    echo
fi

echo -e "${GREEN}[✓] Pipeline executado com sucesso.${NC}"
echo -e "${YELLOW}Próximos passos sugeridos:${NC}"
echo "  • Analisar benchmark_data.csv para dados brutos"
echo "  • Integrar com hardware real via moonlab C API"

exit 0
