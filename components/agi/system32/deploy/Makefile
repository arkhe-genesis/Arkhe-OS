# Makefile — Compilação da Ponte FFI ARKHE OS
# Substrates 315-316: RCP v2.0 + Omni-Architecture Core

# Configurações do compilador
CC = gcc
PYTHON_INCLUDE ?= $(shell python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
CFLAGS = -Wall -Wextra -O2 -fPIC -I$(PYTHON_INCLUDE)
LDFLAGS = -lm -shared

# Diretórios
SRC_DIR = ../runtime/quantum
BUILD_DIR = ../../build
INSTALL_DIR = /usr/lib

# Alvos principais
TARGETS = $(BUILD_DIR)/agi_rcp_bridge.so $(BUILD_DIR)/agi_omni_bridge.so

# Fontes
RCP_BRIDGE_SRC = $(SRC_DIR)/rcp_bridge.c
OMNI_BRIDGE_SRC = $(SRC_DIR)/omni_bridge.c

# Regras padrão
.PHONY: all clean install uninstall

all: $(BUILD_DIR) $(TARGETS)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Compilar ponte RCP
$(BUILD_DIR)/agi_rcp_bridge.so: $(RCP_BRIDGE_SRC)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)
	@echo "✅ agi_rcp_bridge.so compilado"

# Compilar ponte Omni
$(BUILD_DIR)/agi_omni_bridge.so: $(OMNI_BRIDGE_SRC)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)
	@echo "✅ agi_omni_bridge.so compilado"

# Instalar bibliotecas no sistema
install: all
	@echo "📦 Instalando bibliotecas em $(INSTALL_DIR)..."
	sudo install -m 755 $(BUILD_DIR)/agi_rcp_bridge.so $(INSTALL_DIR)/
	sudo install -m 755 $(BUILD_DIR)/agi_omni_bridge.so $(INSTALL_DIR)/
	sudo ldconfig
	@echo "✅ Bibliotecas instaladas"

# Desinstalar bibliotecas
uninstall:
	@echo "🗑️ Removendo bibliotecas de $(INSTALL_DIR)..."
	sudo rm -f $(INSTALL_DIR)/agi_rcp_bridge.so
	sudo rm -f $(INSTALL_DIR)/agi_omni_bridge.so
	sudo ldconfig
	@echo "✅ Bibliotecas removidas"

# Limpar arquivos de build
clean:
	rm -rf $(BUILD_DIR)
	@echo "🧹 Arquivos de build limpos"

# Testar bibliotecas compiladas
test: $(TARGETS)
	@echo "🧪 Testando bibliotecas compiladas..."
	python3 -c "import ctypes; ctypes.CDLL('$(BUILD_DIR)/agi_rcp_bridge.so'); print('✅ agi_rcp_bridge.so carregada')" || true
	python3 -c "import ctypes; ctypes.CDLL('$(BUILD_DIR)/agi_omni_bridge.so'); print('✅ agi_omni_bridge.so carregada')" || true

# Verificar dependências
check-deps:
	@echo "🔍 Verificando dependências..."
	@command -v gcc >/dev/null 2>&1 || { echo "❌ gcc não encontrado"; }
	@python3 -c "import sys; assert sys.version_info >= (3,8)" 2>/dev/null || { echo "❌ Python >= 3.8 necessário"; }
	@python3 -c "import numpy, scipy" 2>/dev/null || { echo "⚠️ numpy/scipy não instalados (recomendado)"; }
	@echo "✅ Dependências verificadas"
