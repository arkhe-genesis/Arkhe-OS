---
license: mit
tags:
  - quantum-oscillators
  - crystal-brain
  - sparse-autoencoder
  - onnx
  - manifold-learning
  - wigner-function
---

# 🧠 ARKHE Crystal Brain ONNX

Modelos ONNX exportados do **ARKHE OS** para inferência portátil do Crystal Brain.

## 📦 Modelos Incluídos

| Modelo | Descrição | Input Shape | Output |
|--------|-----------|-------------|--------|
| `crystal_sae.onnx` | Sparse Autoencoder para extração de códigos do manifold | `[batch, 768]` | `reconstructed`, `latent_code` |
| `wigner_approx.onnx` | Aproximador neural da função de Wigner | `[batch, 2]` (x, p) | `wigner_value` |

## 🚀 Uso Rápido

### Python (onnxruntime)
```python
import onnxruntime as ort
import numpy as np

session = ort.InferenceSession("crystal_sae.onnx")
phases = np.random.randn(1, 768).astype(np.float32)
outputs = session.run(None, {"phases": phases})
reconstructed, latent = outputs
```

### JavaScript (navegador)
```javascript
import * as ort from 'onnxruntime-web';

const session = await ort.InferenceSession.create('./crystal_sae.onnx');
const phases = new ort.Tensor('float32', new Float32Array(768), [1, 768]);
const outputs = await session.run({ phases });
```

### Rust (ort crate)
```rust
use ort::{Session, Value};
let session = Session::builder()?.commit_from_file("crystal_sae.onnx")?;
// ... ver exemplos/infer_rust.rs
```

## 🔬 Métricas do Modelo

- **Reconstruction MSE**: < 0.02 (em dados de teste do Crystal Brain v∞.15)
- **Sparsity**: ~95% de zeros no código latente (threshold=0.01)
- **Coherence preservation**: ρ > 0.85 no regime CAPTURE

## 🤝 Contribuindo

1. Fork o repositório
2. Treine/ajuste o modelo localmente
3. Exporte para ONNX com `python core/export_onnx.py`
4. Submeta um PR com os novos pesos

## 📜 Licença

MIT — Use, modifique, distribua. A geometria é livre. 🔭⚛️🧠
