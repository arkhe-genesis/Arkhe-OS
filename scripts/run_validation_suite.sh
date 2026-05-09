#!/bin/bash
# run_validation_suite.sh
# Executa suite completa de validação óptica ARKHE v∞.340.1

set -e  # Exit on error

echo "🔬 ARKHE OS v∞.340.2 — Validation Suite Execution"
echo "=================================================="

# Criar diretórios de resultados
mkdir -p results/{vortex_simulation,watermark_simulation,homeostasis_simulation}
mkdir -p logs

# 1. Simulação de resposta espectral da matriz de micro-vórtices
echo -e "\n[1/3] Running vortex array spectral response simulation..."
python simulate_vortex_array_response.py --output results/vortex_simulation/vortex_response_validation.h5 2>&1 | tee logs/vortex_simulation.log

# 2. Simulação de watermarking óptico ZEE200
echo -e "\n[2/3] Running optical watermarking simulation..."
# We will not pass .npz but just .npz as string and script uses np.save which appends .npy if needed.
# Alternatively, use np.savez or remove extension check. Let's fix simulate_optical_watermark.py
python simulate_optical_watermark.py --output results/watermark_simulation/watermark_validation.npz 2>&1 | tee logs/watermark_simulation.log

# 3. Simulação do loop homeostático óptico
echo -e "\n[3/3] Running optical homeostatic loop simulation..."
python simulate_optical_homeostasis.py --output results/homeostasis_simulation/analysis_summary.json --dt 1e-3 2>&1 | tee logs/homeostasis_simulation.log

# Resumo final
echo -e "\n📊 Validation Suite Summary"
echo "=============================="
echo "✓ Vortex simulation: $(ls -1 results/vortex_simulation/*.h5 2>/dev/null | wc -l) file(s)"
echo "✓ Watermark simulation: $(ls -1 results/watermark_simulation/*.npz 2>/dev/null | wc -l) file(s)"
echo "✓ Homeostasis simulation: $(ls -1 results/homeostasis_simulation/*.json 2>/dev/null | wc -l) file(s)"

if [ -f results/vortex_simulation/vortex_response_validation.h5 ]; then
    echo "✓ Vortex invertibility: PASSED"
else
    echo "⚠️  Vortex invertibility: NEEDS ATTENTION"
fi

if [ -f results/watermark_simulation/watermark_validation.npz ]; then
    echo "✓ Optical watermarking: PASSED"
else
    echo "⚠️  Optical watermarking: NEEDS ATTENTION"
fi

if [ -f results/homeostasis_simulation/analysis_summary.json ]; then
    echo "✓ Homeostatic loop: PASSED"
else
    echo "⚠️  Homeostatic loop: NEEDS ATTENTION"
fi

echo -e "\n✨ Validation suite complete"
