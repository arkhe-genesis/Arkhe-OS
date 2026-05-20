#!/bin/bash
# install-pre-commit.sh — Instala hooks pre-commit para Regra dos 137

set -e

echo "🔧 Instalando pre-commit hooks para Regra dos 137 (α⁻¹)..."

# Instalar pre-commit se não existir
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Instalando pre-commit..."
    pip install pre-commit
fi

# Instalar hooks
pre-commit install

# Verificar instalação
if pre-commit run check-137-rule --all-files; then
    echo "✅ Hooks instalados e validação inicial aprovada"
else
    echo "⚠️  Validação inicial falhou - execute 'python check_137_rule.py . --fission' para corrigir"
    echo "   Ou use '--no-verify' para commit de emergência (não recomendado)"
fi

echo ""
echo "📋 Hooks ativos:"
echo "   • check-137-rule: Valida α⁻¹ em cada commit"
echo "   • Bloqueia commits que violam a Regra dos 137"
echo ""
echo "🔧 Para pular validação (emergência apenas):"
echo "   git commit --no-verify -m 'mensagem'"
echo ""
echo "Canon: ∞.Ω.∇+++.319"
