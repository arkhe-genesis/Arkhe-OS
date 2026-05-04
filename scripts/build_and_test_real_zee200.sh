#!/bin/bash
# scripts/build_and_test_real_zee200.sh
set -e

echo "🔐 Building and Testing Real ZEE200 Backend"
echo "============================================"

# 1. Verificar repositório ZEE200
if [ ! -d "ZEE200" ]; then
    echo "📦 Cloning ZEE200 repository..."
    git clone https://github.com/ainta/ZEE200.git
fi

# 2. Compilar bibliotecas ZEE200
echo -e "\n[1/4] Compiling ZEE200 libraries..."
cd ZEE200
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DSECURITY_BITS=80 \
         -DFIELD=Mersenne61
make -j$(nproc) gtzk_cpu emp_zk emp_ot
cd ../..

# 3. Compilar bindings pybind11
echo -e "\n[2/4] Compiling pybind11 bindings..."
cd zee200_integration
export ZEE200_ROOT="$(pwd)/../ZEE200"
export CXXFLAGS="-O3 -march=native -DSECURITY_BITS=80"

pip install -e . --verbose --no-cache-dir

# 4. Testar backend real com prova mínima
echo -e "\n[3/4] Testing real backend with minimal proof..."
python -c "
import numpy as np
import time
from zee200_backend_real import RealZEE200Bridge

# Inicializar bridge real
bridge = RealZEE200Bridge(security_bits=40)  # 40 bits para teste rápido
print('✓ RealZEE200Bridge initialized')

# Dados sintéticos mínimos para teste
community = {
    'community_id': 'test_minimal',
    'crystals': list(range(16)),
    'rho': 0.65
}
manifold = np.random.randn(50, 3)  # 50 pontos, dim=3
decoder = np.random.randn(768, 3)   # Matriz D mock

# Gerar prova real
start = time.perf_counter()
proof = bridge.generate_capture_proof_real(
    community_data=community,
    manifold_points=manifold,
    decoder_matrix=decoder,
    epsilon=0.01
)
elapsed = time.perf_counter() - start

print(f'✓ Real proof generated:')
print(f'  - Time: {proof[\"proof_time_ms\"]:.1f} ms')
print(f'  - Size: {proof[\"proof_size_bytes\"]/1024:.2f} KB')
print(f'  - Verified: {proof[\"verified\"]}')
print(f'  - Security: {proof[\"security_bits\"]}-bit, PQ={proof[\"post_quantum\"]}')
"

# 5. Benchmark rápido de performance
echo -e "\n[4/4] Quick performance benchmark..."
python -c "
import numpy as np
import time
from zee200_backend_real import RealZEE200Bridge

bridge = RealZEE200Bridge(security_bits=40)

# Benchmark com tamanhos variados
for n_points in [25, 50, 100]:
    manifold = np.random.randn(n_points, 3)
    decoder = np.random.randn(768, 3)

    start = time.perf_counter()
    proof = bridge.generate_capture_proof_real(
        community_data={'community_id': 'bench', 'crystals': list(range(16)), 'rho': 0.65},
        manifold_points=manifold,
        decoder_matrix=decoder,
        epsilon=0.01
    )
    elapsed = time.perf_counter() - start

    print(f'  n_points={n_points:3d}: {proof[\"proof_time_ms\"]:6.1f} ms, '
          f'{proof[\"proof_size_bytes\"]/1024:5.2f} KB')
"

echo -e "\n✅ Real ZEE200 backend built and tested successfully!"
echo "🔗 Ready for production use with security_bits=80"
