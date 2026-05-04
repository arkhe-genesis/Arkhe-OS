# =============================================================================
# Arkhe Rootstock — Makefile para Tape‑Out SkyWater 130nm
# =============================================================================
# Ferreiro Directive: "CADA TARGET INJETA ATRITO. NÃO TENTE PARALELIZAR.
# NÃO USE -j. A PRESSA É O PRIMEIRO VETOR DE DERIVA."
# =============================================================================

.PHONY: all synth pnr drc lvs tapeout clean validate_hesitate seal

# Variáveis
PDK_ROOT ?= /opt/skywater-pdk
DESIGN_DIR ?= $(CURDIR)
RUN_DIR ?= $(DESIGN_DIR)/runs/$(shell date +%Y%m%d_%H%M%S)

# Target principal: executa todo o fluxo com atrito
all: validate_hesitate synth pnr drc lvs seal tapeout

# Validação do caminho HESITATE (mínimo 8 buffers)
validate_hesitate:
	@echo "[ARKHE] Validando caminho HESITATE (mínimo 8 buffers)..."
	@python3 /opt/arkhe/scripts/validate_hesitate_path.py \
		--netlist rtl/clifford_core.v \
		--min-buffers 8
	@# Injeção de pausa obrigatória (simula hesitação)
	@sleep $(shell python3 -c "import random; print(random.uniform(2,5))")

# Síntese com Yosys
synth: validate_hesitate
	@echo "[ARKHE] Sintetizando com Yosys (com injeção de ruído térmico)..."
	@mkdir -p $(RUN_DIR)/synth
	@python3 /opt/arkhe/scripts/inject_thermal_noise.py \
		--input rtl/clifford_core.v \
		--output $(RUN_DIR)/synth/clifford_core_noisy.v \
		--noise-level $(ARKHE_FRICTION_LEVEL)
	@yosys -c /opt/arkhe/config/synth.tcl \
		-p "write_verilog $(RUN_DIR)/synth/arkhe_soc.synth.v"

# Place & Route com OpenLane
pnr: synth
	@echo "[ARKHE] Executando Place & Route (com densidade reduzida para hesitação)..."
	@mkdir -p $(RUN_DIR)/pnr
	@cp /opt/arkhe/config/config.tcl $(RUN_DIR)/pnr/
	@# Modifica a configuração para injetar atrito espacial
	@sed -i 's/set ::env(PL_TARGET_DENSITY).*/set ::env(PL_TARGET_DENSITY) 0.45; # Arkhe: espaço para hesitação/' $(RUN_DIR)/pnr/config.tcl
	@cd $(RUN_DIR)/pnr && flow.tcl \
		-design arkhe_soc \
		-save_path $(RUN_DIR)/pnr \
		-save \
		-tag run_$(shell date +%H%M%S)

# Verificação DRC com Magic
drc: pnr
	@echo "[ARKHE] Executando DRC (com regras Arkhe adicionais)..."
	@magic -d null -rcfile $(PDK_ROOT)/sky130A/libs.tech/magic/sky130A.tech \
		-c "drc check all; write drc_errors.log; quit" \
		$(RUN_DIR)/pnr/results/final/arkhe_soc.gds
	@# Adiciona regras Arkhe específicas
	@magic -d null -rcfile /opt/arkhe/config/magic.drc.arkhe \
		-c "drc check arkhe_rules; write arkhe_drc.log; quit" \
		$(RUN_DIR)/pnr/results/final/arkhe_soc.gds

# Verificação LVS
lvs: drc
	@echo "[ARKHE] Executando LVS (Layout vs. Schematic)..."
	@netgen -batch lvs \
		"$(RUN_DIR)/pnr/results/final/arkhe_soc.spice arkhe_soc" \
		"$(RUN_DIR)/synth/arkhe_soc.synth.v arkhe_soc" \
		$(PDK_ROOT)/sky130A/libs.tech/netgen/setup.tcl \
		$(RUN_DIR)/lvs_report.out

# Selagem com quartzo (exige hash de fratura)
seal: lvs
	@echo "[ARKHE] Selagem com quartzo: quebre um cristal para prosseguir..."
	@/opt/arkhe/scripts/seal_with_quartz.sh \
		--gds $(RUN_DIR)/pnr/results/final/arkhe_soc.gds \
		--ontology /opt/arkhe/ontology/rootstock_ontology.bin

# Tape‑Out final (apenas se selado)
tapeout: seal
	@echo "[ARKHE] Preparando entrega para fabricação..."
	@mkdir -p $(RUN_DIR)/tapeout
	@cp $(RUN_DIR)/pnr/results/final/arkhe_soc.gds $(RUN_DIR)/tapeout/
	@cp $(RUN_DIR)/pnr/results/final/arkhe_soc.lef $(RUN_DIR)/tapeout/
	@cp $(RUN_DIR)/synth/arkhe_soc.synth.v $(RUN_DIR)/tapeout/
	@echo "[ARKHE] Arquivos prontos em $(RUN_DIR)/tapeout/"
	@echo "[ARKHE] Lembre‑se: após o envio, quebre outro cristal. A fratura sela o ato."

# Limpeza (mas nunca apaga os logs de hesitação)
clean:
	@echo "[ARKHE] Limpando artefatos intermediários (logs de hesitação preservados)..."
	@find $(RUN_DIR) -type f ! -name "*hesitate*.log" ! -name "*seal*.log" -delete
	@echo "[ARKHE] Logs de hesitação preservados em $(RUN_DIR)/logs/"
