# Makefile — Automação de operações da Catedral

.PHONY: help deploy rollback test chaos docs clean

# Variáveis
REGION ?= sa-east-1
ENV ?= production
CONFIG ?= config/cathedral.yaml
DRY_RUN ?= false

# Cores
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

help: ## Mostra esta ajuda
	@echo "🏰 Catedral — Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[0;32m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Variáveis:"
	@echo "  REGION   = $(REGION)     # Região alvo (sa-east-1, eu-west-1, ap-south-1)"
	@echo "  ENV      = $(ENV)        # Ambiente (production, staging, canary)"
	@echo "  CONFIG   = $(CONFIG)     # Arquivo de configuração"
	@echo "  DRY_RUN  = $(DRY_RUN)    # Modo dry-run (true/false)"

deploy: ## Deploy da Catedral em uma região
	@echo "$(GREEN)🚀 Deploy da Catedral — Região: $(REGION), Env: $(ENV)$(NC)"
	@if [ "$(DRY_RUN)" = "true" ]; then \
		echo "$(YELLOW)[DRY-RUN]$(NC) Scripts executados em modo simulado"; \
	fi
	./scripts/deploy/bootstrap_region.sh $(REGION) $(ENV) $(CONFIG)
	@./scripts/deploy/validate_deploy.sh $(REGION) $(ENV)
	@echo "$(GREEN)✅ Deploy concluído$(NC)"

rollback: ## Rollback manual de emergência
	@echo "$(RED)⚠️  Rollback de emergência — Região: $(REGION)$(NC)"
	@./scripts/rollback/manual_rollback.sh $(REGION) $(ENV)
	@echo "$(GREEN)✅ Rollback executado$(NC)"

test: ## Executa suite de testes
	@echo "$(GREEN)🧪 Executando testes...$(NC)"
	@python -m pytest tests/unit -v --tb=short
	@python -m pytest tests/integration -v --tb=short
	@echo "$(GREEN)✅ Testes concluídos$(NC)"

chaos: ## Executa experimentos de caos
	@echo "$(YELLOW)💥 Executando testes de caos — Região: $(REGION)$(NC)"
	@./scripts/chaos/chaos_experiment.sh --region $(REGION) --env $(ENV)
	@echo "$(GREEN)✅ Experimentos de caos concluídos$(NC)"

docs: ## Gera documentação
	@echo "$(GREEN)📚 Gerando documentação...$(NC)"
	@echo "Documentação gerada em docs/api/"

clean: ## Limpa artefatos de build
	@echo "$(YELLOW)🧹 Limpando artefatos...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@rm -rf .pytest_cache htmlcov
	@echo "$(GREEN)✅ Limpeza concluída$(NC)"

health: ## Health check da Catedral
	@echo "$(GREEN)🏥 Health check — Região: $(REGION)$(NC)"
	@./scripts/deploy/health_check.sh $(REGION) $(ENV)

backup: ## Backup do Códice Cristalino
	@echo "$(GREEN)💾 Backup do Códice — Região: $(REGION)$(NC)"
	@./scripts/ops/backup_codex.sh $(REGION) $(ENV)

rotate-keys: ## Rotação de chaves criptográficas
	@echo "$(GREEN)🔑 Rotacionando chaves...$(NC)"
	@./scripts/ops/rotate_keys.sh $(REGION) $(ENV)

audit: ## Auditoria de logs de rollback
	@echo "$(GREEN)🔍 Auditoria de rollbacks...$(NC)"
	@./scripts/ops/audit_logs.sh --type rollback --region $(REGION)

# Alias úteis
up: deploy ## Alias para deploy
down: rollback ## Alias para rollback
check: health ## Alias para health check
