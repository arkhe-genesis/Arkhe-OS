# ARKHE OS vinf.omega - Substrato 398-DEPLOY Makefile
# Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)

.PHONY: all ci driver firmware calib soar deploy clean

all: ci driver firmware calib soar
	@echo "ARKHE 398-DEPLOY: Todos os artefatos construidos"

ci:
	@echo "Executando pipeline CI/CD..."
	act -P ubuntu-latest=nektos/act-environments-ubuntu:18.04 || \
		echo "GitHub Actions local requer 'act' instalado"

driver:
	@echo "Compilando driver kernel..."
	cd drivers && make

firmware:
	@echo "Compilando firmware FPGA..."
	cd firmware && make lint && make sim

calib:
	@echo "Executando protocolo de calibracao..."
	python3 calib/calibration_protocol.py

soar:
	@echo "Testando conector SOAR..."
	python3 soar/soar_connector.py

deploy:
	@echo "Deploy em hardware real..."
	sudo bash deploy/hardware_deploy.sh

clean:
	cd drivers && make clean
	cd firmware && make clean
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	@echo "Limpo"