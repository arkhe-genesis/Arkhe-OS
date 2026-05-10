#!/bin/bash
# scripts/compile_bindings.sh
set -e  # Exit on error

echo "🔐 ARKHE OS v∞.320.4 — Compiling pybind11 bindings for ZEE200"
echo "=============================================================="

# 1. Verificar dependências
echo -e "\n[1/5] Checking dependencies..."
command -v cmake >/dev/null 2>&1 || { echo "❌ cmake not found"; exit 1; }
command -v pip >/dev/null 2>&1 || { echo "❌ pip not found"; exit 1; }
python3 -c "import pybind11" >/dev/null 2>&1 || {
    echo "⚠️  Installing pybind11...";
    pip install pybind11
}

# 2. Clonar/verificar ZEE200 repo se necessário
echo -e "\n[2/5] Checking ZEE200 repository..."
if [ ! -d "ZEE200" ]; then
    echo "📦 Cloning ZEE200 repository..."
    git clone https://github.com/ainta/ZEE200.git
fi

# 3. Compilar ZEE200 libs se necessário
echo -e "\n[3/5] Building ZEE200 libraries..."
cd ZEE200
if [ ! -f "build/lib/libgtzk_cpu.a" ]; then
    mkdir -p build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release
    make -j$(nproc) gtzk_cpu emp_zk emp_ot
    cd ../..
else
    echo "✓ ZEE200 libraries already built"
fi

# 4. Compilar bindings pybind11
echo -e "\n[4/5] Building pybind11 bindings..."
cd zee200_integration
export ZEE200_ROOT="$(pwd)/../ZEE200"
pip install -e . --verbose

# 5. Testar import básico
echo -e "\n[5/5] Testing basic import..."
python3 -c "
import zee200_backend
print(f'✓ zee200_backend imported successfully')
print(f'✓ Field size: {zee200_backend.get_field_size()} bits')
print(f'✓ Estimated proof size for 100 constraints: {zee200_backend.estimate_proof_size(100)} bytes')
"

echo -e "\n✅ Compilation complete! Bindings ready at: $(python3 -c 'import zee200_backend; print(zee200_backend.__file__)')"
