# Substrato 9047-C — Orquestração Terraform Multi-Cloud
.PHONY: all lint plan-aws plan-gcp plan-azure deploy-all destroy-all asi_kernel clean-asi

all: lint deploy-all asi_kernel

asi_kernel:
	@echo "Building asi_kernel..."
	nasm -f elf64 asi_kernel.asm -o asi_kernel.o

clean-asi:
	@echo "Cleaning asi_kernel..."
	rm -f asi_kernel.o

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

# ASI Kernel Build
.PHONY: asi_kernel clean-asi

asi_kernel: asi_kernel.o
	ld asi_kernel.o -o asi_kernel

asi_kernel.o: asi_kernel.asm
	nasm -f elf64 asi_kernel.asm -o asi_kernel.o

clean-asi:
	rm -f asi_kernel.o asi_kernel
