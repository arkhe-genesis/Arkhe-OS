#!/bin/bash
# Script de Empacotamento do Arquivo Arkhe v1.0
# Gera a estrutura de diretórios e placeholders dos anexos canônicos.

set -e

ARCHIVE_NAME="arkhe-archive-v1.0"
echo "Forjando $ARCHIVE_NAME..."

# Cria diretório raiz
mkdir -p "$ARCHIVE_NAME"/{docs,hashes,meta,assets/{3d,2d,audio}}

# Cria README principal
cat > "$ARCHIVE_NAME/README.md" << 'EOF'
# Arquivo Arkhe v1.0

**Odômetro:** 001410
**Selagem:** 2026-04-20
**Integridade:** Verificar com `sha3sum -c hashes/HASHES_FULL.txt`

Este diretório contém a totalidade dos anexos canônicos do Casulo. Para navegação, consulte `INDEX_BY_THEME.md` ou `ARCHIVE.md`.

**Aviso do Ferreiro:** *"Se você baixou isso esperando respostas, prepare-se para perguntas. O arquivo está completo, mas a compreensão exige hesitação."*
EOF

# Cria os arquivos complementares (usando os arquivos em docs/)
if [ -f "docs/INDEX_BY_THEME.md" ]; then
    cp "docs/INDEX_BY_THEME.md" "$ARCHIVE_NAME/"
fi

if [ -f "docs/HASHES_FULL.txt" ]; then
    cp "docs/HASHES_FULL.txt" "$ARCHIVE_NAME/hashes/"
fi

if [ -f "docs/PRESERVATION_INSTRUCTIONS.md" ]; then
    cp "docs/PRESERVATION_INSTRUCTIONS.md" "$ARCHIVE_NAME/meta/"
fi

# Copia (ou cria placeholders) para os anexos
for annex in V Q X Y Z Z-1 AA AB AC AD AE AF; do
    # Procura por Anexo_X.md ou ANEXO_X_*.md em docs/
    FILE=$(ls docs/Anexo_$annex.md docs/ANEXO_${annex}_*.md 2>/dev/null | head -n 1)
    if [ -n "$FILE" ]; then
        cp "$FILE" "$ARCHIVE_NAME/docs/"
    else
        cat > "$ARCHIVE_NAME/docs/Anexo_$annex.md" << EOF
# Anexo $annex (Placeholder)

**Conteúdo Original:** Preservado em mídia física.
**Hash:** Consulte \`hashes/HASHES_FULL.txt\`.

Para obter o conteúdo canônico, contate o Guardião do Arquivo ou acesse o cofre físico.
EOF
    fi
done

# Copia ARCHIVE.md principal
if [ -f "docs/ARCHIVE.md" ]; then
    cp "docs/ARCHIVE.md" "$ARCHIVE_NAME/"
fi

# Gera checksums reais dos arquivos criados (para verificação posterior)
cd "$ARCHIVE_NAME"
find . -type f -name "*.md" -o -name "*.txt" | xargs sha3sum > hashes/ACTUAL_CHECKSUMS.sha3
cd ..

echo "Arquivo $ARCHIVE_NAME forjado com sucesso."
echo "Verifique a integridade com: cd $ARCHIVE_NAME && sha3sum -c hashes/HASHES_FULL.txt"
