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
# ══════════════════════════════════════════════════════════════════════
# ExtendDB Infrastructure — PostgreSQL + ExtendDB Deployment
# ══════════════════════════════════════════════════════════════════════

locals {
  extenddb_postgres_db_name = "extenddb_catalog"
  extenddb_postgres_user    = "arkhe_extenddb"
}

# ── AWS RDS PostgreSQL para ExtendDB ──
resource "aws_db_instance" "extenddb_postgres" {
  count = var.cloud_provider == "aws" && var.extenddb_enabled ? 1 : 0

  identifier     = "${var.cluster_name}-extenddb"
  engine         = "postgres"
  engine_version = "16.4"
  instance_class = var.extenddb_postgres_instance_class

  db_name  = local.extenddb_postgres_db_name
  username = local.extenddb_postgres_user
  password = random_password.extenddb_postgres[0].result

  allocated_storage     = var.extenddb_postgres_storage_gb
  storage_encrypted     = true
  storage_type          = "gp3"
  multi_az              = var.environment == "production"
  publicly_accessible   = false
  vpc_security_group_ids = [aws_security_group.extenddb_postgres[0].id]
  db_subnet_group_name  = aws_db_subnet_group.extenddb[0].name

  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  deletion_protection     = var.environment == "production"

  tags = {
    Name    = "${var.cluster_name}-extenddb"
    Arkhe   = "true"
    Service = "extenddb"
  }
}

resource "random_password" "extenddb_postgres" {
  count   = var.extenddb_enabled ? 1 : 0
  length  = 32
  special = false
}

resource "aws_security_group" "extenddb_postgres" {
  count       = var.cloud_provider == "aws" && var.extenddb_enabled ? 1 : 0
  name        = "${var.cluster_name}-extenddb-postgres"
  description = "Security group for ExtendDB PostgreSQL"
  vpc_id      = module.aws_vpc[0].vpc_id

  ingress {
    description     = "PostgreSQL from EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.aws_eks[0].node_security_group_id]
  }
}

resource "aws_db_subnet_group" "extenddb" {
  count      = var.cloud_provider == "aws" && var.extenddb_enabled ? 1 : 0
  name       = "${var.cluster_name}-extenddb"
  subnet_ids = module.aws_vpc[0].private_subnets
}

# ── GCP Cloud SQL PostgreSQL para ExtendDB ──
resource "google_sql_database_instance" "extenddb_postgres" {
  count            = var.cloud_provider == "gcp" && var.extenddb_enabled ? 1 : 0
  name             = "${var.cluster_name}-extenddb"
  database_version = "POSTGRES_16"
  region           = var.gcp_region

  settings {
    tier              = var.extenddb_postgres_instance_class
    disk_size         = var.extenddb_postgres_storage_gb
    disk_type         = "PD_SSD"
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "production"
      start_time                     = "03:00"
    }

    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.vpc[0].id
    }
  }

  deletion_protection = var.environment == "production"
}

resource "google_sql_database" "extenddb" {
  count    = var.cloud_provider == "gcp" && var.extenddb_enabled ? 1 : 0
  name     = local.extenddb_postgres_db_name
  instance = google_sql_database_instance.extenddb_postgres[0].name
}

resource "google_sql_user" "extenddb" {
  count    = var.cloud_provider == "gcp" && var.extenddb_enabled ? 1 : 0
  name     = local.extenddb_postgres_user
  instance = google_sql_database_instance.extenddb_postgres[0].name
  password = random_password.extenddb_postgres[0].result
}

# ── Azure PostgreSQL Flexible Server para ExtendDB ──
resource "azurerm_postgresql_flexible_server" "extenddb" {
  count               = var.cloud_provider == "azure" && var.extenddb_enabled ? 1 : 0
  name                = "${var.cluster_name}-extenddb"
  resource_group_name = azurerm_resource_group.rg[0].name
  location            = azurerm_resource_group.rg[0].location
  version             = "16"

  administrator_login    = local.extenddb_postgres_user
  administrator_password = random_password.extenddb_postgres[0].result

  storage_mb   = var.extenddb_postgres_storage_gb * 1024
  storage_tier = "P30"
  sku_name     = var.extenddb_postgres_instance_class

  backup_retention_days = var.environment == "production" ? 35 : 7

  delegated_subnet_id = azurerm_subnet.aks[0].id
  private_dns_zone_id = azurerm_private_dns_zone.postgres[0].id

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "azurerm_postgresql_flexible_server_database" "extenddb" {
  count     = var.cloud_provider == "azure" && var.extenddb_enabled ? 1 : 0
  name      = local.extenddb_postgres_db_name
  server_id = azurerm_postgresql_flexible_server.extenddb[0].id
}

# ── Kubernetes Secret com credenciais do PostgreSQL ──
resource "kubernetes_secret" "extenddb_postgres" {
  count = var.extenddb_enabled ? 1 : 0
  metadata {
    name      = "extenddb-postgres-credentials"
    namespace = var.helm_namespace
  }

  data = {
    host     = var.cloud_provider == "aws"   ? aws_db_instance.extenddb_postgres[0].address : var.cloud_provider == "gcp"   ? google_sql_database_instance.extenddb_postgres[0].private_ip_address : azurerm_postgresql_flexible_server.extenddb[0].fqdn
    port     = "5432"
    user     = local.extenddb_postgres_user
    password = random_password.extenddb_postgres[0].result
    dbname   = local.extenddb_postgres_db_name
  }

  depends_on = [
    aws_db_instance.extenddb_postgres,
    google_sql_database_instance.extenddb_postgres,
    azurerm_postgresql_flexible_server.extenddb
  ]
}

variable "extenddb_enabled" {
  description = "Enable ExtendDB infrastructure"
  type        = bool
  default     = true
}

variable "extenddb_postgres_instance_class" {
  description = "PostgreSQL instance class for ExtendDB"
  default = {
    aws   = "db.t4g.large"
    gcp   = "db-custom-2-8192"
    azure = "GP_Standard_D2s_v3"
  }
}

variable "extenddb_postgres_storage_gb" {
  description = "Storage size for ExtendDB PostgreSQL (GB)"
  type        = number
  default     = 100
}
