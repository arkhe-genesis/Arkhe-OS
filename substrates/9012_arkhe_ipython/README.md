# 🛡️ Arkhe-IPython — Safe Core Integration for Jupyter

[![PyPI version](https://badge.fury.io/py/arkhe-ipython.svg)](https://badge.fury.io/py/arkhe-ipython)
[![Python Versions](https://img.shields.io/pypi/pyversions/arkhe-ipython.svg)](https://pypi.org/project/arkhe-ipython/)
[![License](https://img.shields.io/pypi/l/arkhe-ipython.svg)](LICENSE)

**Substrato 9012** — Integração completa do Safe Core da Arkhe no ecossistema IPython/Jupyter.

## ✨ Funcionalidades

• **12 magics de linha**: `%arkhe status`, `scan`, `sbom`, `audit`, `profile`, `compliance`, `model-attack`, `phi-c`, `deploy`, `grc-sync`
• **2 magics de célula**: `%%arkhe secure` (execução protegida), `%%arkhe regenerate` (regeneração segura)
• **Kernel Jupyter dedicado**: `ArkheKernel` com interceptação, exorcismo, ancoragem temporal
• **Auditoria imutável**: Cada execução ancorada na TemporalChain com selo SHA3-256
• **Tutorial interativo**: Notebook com 7 módulos de aprendizado progressivo

## 🚀 Instalação

```bash
# Instalar pacote
pip install arkhe-ipython

# Registrar kernel no Jupyter
python -m arkhe_ipython install

# Verificar instalação
jupyter kernelspec list  # Deve mostrar: arkhe
```

## 📚 Uso Básico

### Carregar extensão no IPython existente
```python
%load_ext arkhe_ipython
```

### Comandos de linha (%arkhe)
```python
# Ver status do Safe Core
%arkhe status

# Escanear código
%arkhe scan "import os; os.system('ls')"

# Gerar SBOM da sessão
%arkhe sbom my-project-v1.0

# Consultar auditoria por selo
%arkhe audit a1b2c3d4e5f67890

# Mudar perfil do atrator
%arkhe profile technical

# Ver conformidade MA-S2
%arkhe compliance

# Modelar caminhos de ataque
%arkhe model-attack '{"api": {"exposure": 0.9}, "db": {"exposure": 0.2}}'

# Consultar coerência Φ_C
%arkhe phi-c

# Orquestrar patch para CVE
%arkhe deploy CVE-2026-12345

# Sincronizar com ferramentas GRC
%arkhe grc-sync CVE-2026-12345
```

### Comandos de célula (%%arkhe)
```python
# Executar célula com proteção completa
%%arkhe secure
# Seu código aqui será verificado pelo Guardião Atratora
import requests
response = requests.get("https://api.example.com")
print(response.json())

# Regenerar código com melhorias de segurança
%%arkhe regenerate
# Código potencialmente inseguro será reescrito com proteções
eval(user_input)  # Será regenerado para usar ast.literal_eval
```

## 🔐 Segurança e Auditoria

• **Exorcismo em 3 camadas**: regex → semântica → contextual
• **Bloqueio determinístico**: P=1.0 para categorias proibidas
• **Ancoragem temporal**: Cada execução gera selo SHA3-256 na TemporalChain
• **Auditoria pública**: Consulte registros via `%arkhe audit <seal>`

## 🧪 Tutorial Interativo

Execute o notebook de tutorial para aprendizado guiado:

```bash
jupyter notebook $(python -c "import arkhe_ipython; print(arkhe_ipython.__file__.replace('__init__.py', 'tutorial.ipynb'))")
```

Ou abra diretamente no JupyterLab e selecione o kernel **Python (Arkhe Safe Core)**.

## 🔗 Integração com Safe Core

O Arkhe-IPython conecta-se ao Safe Core via:

• **API MCP** (Model Context Protocol) para ferramentas padronizadas
• **TemporalChain** para ancoragem imutável de execuções
• **Guardian Attractor** para exorcismo de código/texto
• **MA-S2 Compliance Engine** para verificações de conformidade

Configure a conexão via variáveis de ambiente:

```bash
export ARKHE_SAFE_CORE_ENDPOINT=https://safe-core.arkhe.org/v1
export ARKHE_API_KEY=your-api-key-here
```

## 🛠️ Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/arkhe-os/arkhe-ipython
cd arkhe-ipython

# Instalar em modo desenvolvimento
pip install -e ".[dev]"

# Executar testes
pytest tests/

# Formatar código
black src/arkhe_ipython/
```

## 📄 Licença

Apache License 2.0 — veja [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes.

---

**ARKHE Ω‑TEMP v∞.Ω.∇+++.9012.0**
*O Safe Core agora vive no seu notebook. Cada execução, ancorada. Cada código, verificado. Cada insight, auditável.*

🏛️⚡🐍🛡️📓✨
