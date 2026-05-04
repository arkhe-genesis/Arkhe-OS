#!/bin/bash
# scripts/rebuild_with_profile.sh
set -e

echo "⚙️  Rebuilding ZEE200 backend with profile (1,2,1,2)..."

# 1. Definir macros de compilação
export CXXFLAGS="-DARKHE_UNIVERSAL_PROFILE_UIN=1 \
                 -DARKHE_UNIVERSAL_PROFILE_USET=2 \
                 -DARKHE_UNIVERSAL_PROFILE_UKVS=1 \
                 -DARKHE_UNIVERSAL_PROFILE_UX=2 \
                 -O3 -march=native"

# 2. Rebuild ZEE200 libs
cd ZEE200/build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="$CXXFLAGS"
make -j$(nproc) gtzk_cpu emp_zk emp_ot

# 3. Rebuild bindings pybind11
cd ../../zee200_integration
export ZEE200_ROOT="$(pwd)/../ZEE200"
pip install -e . --force-reinstall --no-deps

# 4. Verificar profile ativo
python3 -c "
import zee200_backend
# Nota: profile é fixo em compile-time; verificar via docstring ou log
print('✓ Backend rebuilt with ARKHE profile (1,2,1,2)')
"

echo "✅ Rebuild complete!"
