# Substrato 9047‑C — Terraform Multi‑Cloud Provisioning
# Provisiona ARKHE Broadcast Mesh em AWS, GCP e Azure simultaneamente.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws   = { source = "hashicorp/aws",   version = "~> 5.0" }
    google = { source = "hashicorp/google", version = "~> 5.0" }
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.0" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.0" }
    helm = { source = "hashicorp/helm", version = "~> 2.0" }
  }
}

# ── Variáveis ───────────────────────────────────────────────────
variable "environment" { default = "production" }
variable "cluster_name" { default = "arkhe-mesh" }
variable "num_workers"  { default = 10 }

# ── Providers ────────────────────────────────────────────────────
provider "aws"   { region = "us-east-1" }
provider "google" { project = "arkhe-broadcast", region = "us-central1" }
provider "azurerm" { features {} }

# ── Módulo AWS ───────────────────────────────────────────────────
module "aws_infrastructure" {
  source = "./modules/aws"

  cluster_name = var.cluster_name
  num_workers  = var.num_workers
  enable_kafka = true
  enable_spark = true

  tags = {
    Environment = var.environment
    Substrate   = "9047-C"
    ManagedBy   = "Terraform"
  }
}

# ── Módulo GCP ───────────────────────────────────────────────────
module "gcp_infrastructure" {
  source = "./modules/gcp"

  project_id   = "arkhe-broadcast"
  region       = "us-central1"
  cluster_name = "${var.cluster_name}-gcp"
  num_workers  = var.num_workers
}

# ── Módulo Azure ─────────────────────────────────────────────────
module "azure_infrastructure" {
  source = "./modules/azure"

  resource_group = "arkhe-mesh-rg"
  location       = "East US"
  cluster_name   = "${var.cluster_name}-azure"
  num_workers    = var.num_workers
}

# ── Módulo Kubernetes (aplica a todos os clusters) ───────────────
module "kubernetes_core" {
  source = "./modules/kubernetes"

  providers = {
    kubernetes = kubernetes.aws
    helm       = helm.aws
  }

  deploy_temporal_chain = true
  deploy_phi_bus        = true
  deploy_guardian       = true
  deploy_kafka          = true
  deploy_spark          = true
  deploy_delta_lake     = true
  deploy_mesh_orchestrator = true

  temporal_chain_version = "9018"
  mesh_orchestrator_image = "arkhe/mesh-orchestrator:9043"
}

# ── Outputs ──────────────────────────────────────────────────────
output "aws_cluster_endpoint"   { value = module.aws_infrastructure.cluster_endpoint }
output "gcp_cluster_endpoint"   { value = module.gcp_infrastructure.cluster_endpoint }
output "azure_cluster_endpoint" { value = module.azure_infrastructure.cluster_endpoint }
output "mesh_api_url"           { value = module.kubernetes_core.mesh_api_url }