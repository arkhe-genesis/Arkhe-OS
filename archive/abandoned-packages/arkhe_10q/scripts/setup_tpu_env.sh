#!/bin/bash
# setup_tpu_env.sh — Configura ambiente para benchmark em TPU v6

set -e

echo "🔧 Configurando ambiente TPU v6 para ARKHE 10Q..."

# Verificar variáveis de ambiente TPU
if [ -z "$TPU_NAME" ]; then
    echo "⚠️  TPU_NAME não definido. Usando TPU local ou CPU."
    export TPU_NAME="local"
fi

# Instalar dependências XLA se necessário
if ! python -c "import torch_xla" 2>/dev/null; then
    echo "📦 Instalando torch-xla..."
    pip install torch-xla[tpu] --extra-index-url https://storage.googleapis.com/libtpu-releases/index.html
fi

# Configurar flags XLA para otimização de contrações 5D
export XLA_FLAGS="--xla_disable_hlo_passes=custom-kernel-fusion \
--xla_tpu_enable_data_parallel_all_reduce_opt=true \
--xla_tpu_data_parallel_opt_different_sized_ops=true"

# Verificar dispositivos disponíveis
echo "\n🔍 Dispositivos disponíveis:"
python -c "
import torch
print(f'  CPU: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  CUDA: {torch.cuda.get_device_name(0)}')
try:
    import torch_xla
    import torch_xla.core.xla_model as xm
    devices = xm.get_xla_supported_devices()
    print(f'  TPU: {devices}')
except ImportError:
    print('  TPU: torch-xla não instalado')
"

# Criar diretórios de output
mkdir -p benchmarks/results logs

echo "\n✅ Ambiente configurado. Execute benchmarks com:"
echo "   python benchmarks/contraction_5d_vs_4d.py --device xla:0"
