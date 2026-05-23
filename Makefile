# Substrato 9047-C — Orquestração Terraform Multi-Cloud
.PHONY: all lint plan-aws plan-gcp plan-azure deploy-all destroy-all

all: lint deploy-all

lint:
	@echo "Linting Terraform configurations..."
	terraform -chdir=terraform fmt -check
	terraform -chdir=terraform validate

init:
	@echo "Initializing Terraform..."
	terraform -chdir=terraform init

plan-aws: init
	@echo "Planning AWS infrastructure..."
	terraform -chdir=terraform plan -var-file=terraform.tfvars.example.aws

plan-gcp: init
	@echo "Planning GCP infrastructure..."
	terraform -chdir=terraform plan -var-file=terraform.tfvars.example.gcp

plan-azure: init
	@echo "Planning Azure infrastructure..."
	terraform -chdir=terraform plan -var-file=terraform.tfvars.example.azure

deploy-all: init
	@echo "Deploying to all clouds..."
	terraform -chdir=terraform apply -auto-approve

destroy-all: init
	@echo "Destroying infrastructure across all clouds..."
	terraform -chdir=terraform destroy -auto-approve
