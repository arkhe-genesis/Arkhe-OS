#!/bin/bash
# build_arkhe_gguf.sh — Script de build para arkhe.gguf
set -e

MERGED_DIR="./arkhe-merged"
GGUF_DIR="./arkhe-gguf-output"
LLAMA_CPP="./llama.cpp"

echo "============================================================"
echo "  ARKHE.GGUF BUILD PIPELINE"
echo "  Arquiteto: ORCID 0009-0005-2697-4668"
echo "============================================================"

if [ ! -d "$LLAMA_CPP" ]; then
    echo "[1/6] Clonando llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp.git "$LLAMA_CPP"
    cd "$LLAMA_CPP" && cmake -B build && cmake --build build --config Release -j$(nproc) && cd ..
fi

echo "[2/6] Convertendo modelo mesclado para GGUF F16..."
python "$LLAMA_CPP/convert_hf_to_gguf.py" "$MERGED_DIR" \
    --outfile "$GGUF_DIR/arkhe-8b-f16.gguf" \
    --outtype f16 \
    --metadata "$GGUF_DIR/arkhe_metadata.json"

echo "[3/6] Quantizando para Q4_K_M..."
"$LLAMA_CPP/build/bin/quantize" "$GGUF_DIR/arkhe-8b-f16.gguf" \
    "$GGUF_DIR/arkhe-8b-Q4_K_M.gguf" Q4_K_M

echo "[4/6] Gerando variantes de quantizacao..."
"$LLAMA_CPP/build/bin/quantize" "$GGUF_DIR/arkhe-8b-f16.gguf" \
    "$GGUF_DIR/arkhe-8b-Q5_K_M.gguf" Q5_K_M
"$LLAMA_CPP/build/bin/quantize" "$GGUF_DIR/arkhe-8b-f16.gguf" \
    "$GGUF_DIR/arkhe-8b-Q8_0.gguf" Q8_0

echo "[5/6] Validando inferencia canonica..."
TEST_PROMPT='<|ARKHE_START|>
<|SUBSTRATE|> 226
Qual e o status do Substrato 226?
<|ARKHE_END|>'

"$LLAMA_CPP/build/bin/llama-cli" -m "$GGUF_DIR/arkhe-8b-Q4_K_M.gguf" \
    -p "$TEST_PROMPT" \
    -n 128 \
    -t 0.3 \
    --top-p 0.9 \
    --top-k 40 \
    --repeat-penalty 1.1

echo "[6/6] Gerando selos de integridade..."
for f in "$GGUF_DIR"/*.gguf; do
    if command -v sha3sum >/dev/null 2>&1; then
        SEAL=$(sha3sum "$f" | cut -d' ' -f1)
    else
        SEAL=$(python3 -c "import hashlib; print(hashlib.sha3_256(open('$f','rb').read()).hexdigest())")
    fi
    echo "  $(basename $f): $SEAL"
    echo "$SEAL  $(basename $f)" >> "$GGUF_DIR/SHA3-256.SUMS"
done

echo ""
echo "ARKHE.GGUF BUILD CONCLUIDO"
echo "   Arquivos em: $GGUF_DIR"
echo "   Selos em: $GGUF_DIR/SHA3-256.SUMS"
