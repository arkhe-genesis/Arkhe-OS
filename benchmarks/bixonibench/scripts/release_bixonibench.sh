#!/bin/bash
# release_bixonibench.sh — Lança BixoniBench como open-source

set -e
VERSION="1.0.0"
REPO="arkhe-os/bixonibench"

echo "🚀 Lançando BixoniBench v${VERSION}"

# 1. Validar estrutura do benchmark
echo "  ✅ Validando estrutura..."
test -d benchmarks/bixonibench/datasets/programming || { echo "❌ Dataset não encontrado"; exit 1; }
test -f benchmarks/bixonibench/README.md || { echo "❌ README não encontrado"; exit 1; }

# 2. Executar auto-teste
echo "  🧪 Executando auto-teste..."
python benchmarks/bixonibench/scripts/run_benchmark.py \
  --dataset benchmarks/bixonibench/datasets/programming \
  --output reports/bixonibench_selftest.json

# 3. Gerar badges para README
ACCURACY=$(jq -r '.accuracy' reports/bixonibench_selftest.json)
ECE=$(jq -r '.ece' reports/bixonibench_selftest.json)
cat > benchmarks/bixonibench/BADGES.md << EOF
[![Accuracy](https://img.shields.io/badge/accuracy-${ACCURACY%.*}%25-green)](https://github.com/$REPO)
[![ECE](https://img.shields.io/badge/ECE-${ECE}-blue)](https://github.com/$REPO)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/$REPO)
EOF

# 4. Criar release no GitHub (se token disponível)
if [ -n "$GITHUB_TOKEN" ]; then
  echo "  📦 Criando release no GitHub..."
  gh release create "v$VERSION" \
    --repo "$REPO" \
    --title "BixoniBench v$VERSION" \
    --notes "Primeiro lançamento público do benchmark de imunidade a alucinação para IAs." \
    benchmarks/bixonibench/
fi

# 5. Publicar no PyPI (se aplicável)
if [ -f benchmarks/bixonibench/setup.py ]; then
  echo "  📦 Publicando no PyPI..."
  cd benchmarks/bixonibench
  python setup.py sdist bdist_wheel
  twine upload dist/* --repository pypi
  cd ../..
fi

echo "
✅ BixoniBench v${VERSION} lançado com sucesso!

🔗 Links:
   • Repositório: https://github.com/$REPO
   • Leaderboard: https://arkhe-os.github.io/bixonibench/leaderboard
   • Documentação: https://arkhe-os.github.io/bixonibench/docs

📊 Métricas de referência:
   • Acurácia alvo: 100% em casos fictícios
   • ECE alvo: < 0.05
   • Tempo médio: < 100ms/caso

🎯 Próximo passo: Convidar a comunidade para submeter resultados!
"