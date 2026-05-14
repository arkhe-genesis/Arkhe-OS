# 🚀 ARKHE P³ — Quickstart Guide

## Instalação em 30 segundos

```bash
# Via Cargo (Rust)
cargo install arkhe-polyglot

# Via pip (Python bindings)
pip install arkhe-polyglot

# Via npm (Node.js bindings)
npm install @arkhe/polyglot-parser
```

## Primeiros Passos

### 1. Detectar linguagem automaticamente
```bash
$ arkhe-polyglot detect my_script.py
🔍 Detectando linguagem...
✅ Linguagem: python (confiança: 98.7%)
✅ Dialeto: Python 3.12
```

### 2. Parse e visualizar UAST
```bash
$ arkhe-polyglot parse hello.rs --format dot | dot -Tpng -o ast.png
✅ Parse concluído
📊 Nós na UAST: 47
🔗 Grafo de controle: 12 arestas
🖼️  AST visualizado em ast.png
```

### 3. Transpilar entre linguagens
```bash
$ arkhe-polyglot transpile script.py --to rust --output script.rs
🔄 Transpilando Python → Rust...
✅ Sucesso!
📏 Tamanho: 1.2KB → 1.8KB (+50%)
⚡ Complexidade: 0.42 → 0.38 (-9.5%)
🔐 Hash de integridade: a3f7b2c1...
```

### 4. Analisar semanticamente
```bash
$ arkhe-polyglot analyze app.ts --format summary
📋 Análise Semântica: app.ts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Score Geral: 0.87/1.00
🔐 Segurança: 0.92/1.00 ✅
⚡ Performance: 0.85/1.00 ✅
🧠 Complexidade: 0.84/1.00 ✅
🔗 Compatibilidade ARKHE: 0.91/1.00 ✅

⚠️  2 warnings encontrados:
   • Linha 42: Variável não utilizada 'temp'
   • Linha 89: Potencial race condition em shared_state

💡 Sugestões:
   • Remover variável 'temp' para reduzir complexidade
   • Adicionar mutex para acesso a shared_state
```

## Tutorial Interativo

Execute o tutorial no seu navegador:

```bash
$ arkhe-polyglot tutorial --launch
🌐 Abrindo tutorial em http://localhost:3000
```

O tutorial cobre:
- [x] Conceitos fundamentais da UAST
- [x] Transpilação passo-a-passo
- [x] Análise de segurança cross-language
- [x] Integração com ecossistema ARKHE
- [x] Criação de plugins customizados

## Exemplo Completo: Pipeline Multi-Linguagem

```yaml
# pipeline.arkhe.yml
name: Cross-Language CI
on: [push]

steps:
  - name: Detect languages
    run: arkhe-polyglot detect --recursive ./src

  - name: Parse all sources
    run: arkhe-polyglot parse --output ./build/uast/ ./src/**/*

  - name: Semantic analysis
    run: arkhe-polyglot analyze --fail-on-warnings ./build/uast/

  - name: Transpile to WebAssembly
    run: |
      arkhe-polyglot transpile \
        --from auto \
        --to wasm \
        --output ./build/wasm/ \
        ./src/**/*.rs ./src/**/*.ts

  - name: Deploy to edge
    run: arkhe-polyglot deploy \
        --platform cloudflare-workers \
        --env production \
        ./build/wasm/
```

## Próximos Passos

📚 [Documentação Completa](https://docs.arkhe.org/polyglot)
🔌 [Desenvolver Plugins](https://docs.arkhe.org/plugins)
💬 [Comunidade Discord](https://discord.gg/arkhe)
🐛 [Reportar Issues](https://github.com/arkhe-os/issues)

---
*ARKHE Ω‑TEMP v6.8.0 • Substrato 6062 • Código aberto, ciência aberta, verdade verificável.*
