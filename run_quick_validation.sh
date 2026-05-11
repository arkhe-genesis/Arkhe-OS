#!/bin/bash
# run_quick_validation.sh
# Executa validação rápida de todos os componentes.

set -e

echo "🔬 ARKHE OS v∞.327.2 — Quick Validation Suite"
echo "=============================================="

# 1. Instalar dependências
echo -e "\n[1/5] Installing dependencies..."
pip install -q numpy scipy scikit-learn

# 2. Executar testes unitários
echo -e "\n[2/5] Running unit tests..."
python test_zee200_bridge.py
python test_living_interpretability.py
python test_verifiable_steering.py

# 3. Executar pipeline integrado (mock)
echo -e "\n[3/5] Running integrated homeostasis test (mock)..."
python run_integrated_homeostasis.py

# 4. Verificar outputs
echo -e "\n[4/5] Verifying outputs..."
if [ -d "publish/interpretability" ] && [ -f "publish/interpretability/index.json" ]; then
    echo "   ✓ Evidence directory created and indexed"
else
    echo "   ❌ Evidence directory missing"
    exit 1
fi

if [ -d "results/integrated_homeostasis" ]; then
    n_runs=$(ls -1 results/integrated_homeostasis/*.json 2>/dev/null | wc -l)
    echo "   ✓ $n_runs integrated run(s) saved"
else
    echo "   ❌ Results directory missing"
    exit 1
fi

# 5. Resumo
echo -e "\n[5/5] Validation summary:"
cat << 'EOF'
✅ All unit tests PASSED
✅ Integrated pipeline executed successfully
✅ Evidence publication working
✅ Steering verification validated (mock)

🎯 Ready for:
   • Real ZEE200 backend integration (pybind11)
   • Real Crystal Brain v∞.15 data
   • Production security bits (80+)
   • Live dashboard deployment

🔗 Next command:
   python run_integrated_homeostasis.py --real-data --security-bits 80
EOF

echo -e "\n✨ Quick validation COMPLETE"
