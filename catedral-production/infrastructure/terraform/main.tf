# Catedral Planetária — Terraform Root Module
# Tri-regional deployment: sa-east-1, eu-west-1, ap-south-1

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.20" }
    helm = { source = "hashicorp/helm", version = "~> 2.10" }
  }
}

provider "aws" {
  alias  = "sa_east_1"
  region = "sa-east-1"
  default_tags {
    tags = {
      Project     = "Catedral"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
  default_tags {
    tags = {
      Project     = "Catedral"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

provider "aws" {
  alias  = "ap_south_1"
  region = "ap-south-1"
  default_tags {
    tags = {
      Project     = "Catedral"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPCs por região
module "vpc_sa_east_1" {
  source = "./modules/network"
  providers = { aws = aws.sa_east_1 }

  region_name    = "sa-east-1"
  cidr_block     = "10.0.0.0/16"
  availability_zones = ["sa-east-1a", "sa-east-1b", "sa-east-1c"]
  enable_nat_gateway = true
  enable_flow_logs   = true
}

module "vpc_eu_west_1" {
  source = "./modules/network"
  providers = { aws = aws.eu_west_1 }

  region_name    = "eu-west-1"
  cidr_block     = "10.1.0.0/16"
  availability_zones = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  enable_nat_gateway = true
  enable_flow_logs   = true
}

module "vpc_ap_south_1" {
  source = "./modules/network"
  providers = { aws = aws.ap_south_1 }

  region_name    = "ap-south-1"
  cidr_block     = "10.2.0.0/16"
  availability_zones = ["ap-south-1a", "ap-south-1b", "ap-south-1c"]
  enable_nat_gateway = true
  enable_flow_logs   = true
}

# EKS Clusters por região
module "eks_sa_east_1" {
  source = "./modules/compute"
  providers = { aws = aws.sa_east_1 }

  cluster_name   = "catedral-sa-east-1"
  vpc_id         = module.vpc_sa_east_1.vpc_id
  subnet_ids     = module.vpc_sa_east_1.private_subnets
  node_groups = {
    guardian = {
      instance_types = ["c6i.4xlarge"]
      min_size       = 2
      max_size       = 8
      desired_size   = 4
      disk_size      = 100
    }
  }
}

module "eks_eu_west_1" {
  source = "./modules/compute"
  providers = { aws = aws.eu_west_1 }

  cluster_name   = "catedral-eu-west-1"
  vpc_id         = module.vpc_eu_west_1.vpc_id
  subnet_ids     = module.vpc_eu_west_1.private_subnets
  node_groups = {
    guardian = {
      instance_types = ["c6i.4xlarge"]
      min_size       = 2
      max_size       = 8
      desired_size   = 4
      disk_size      = 100
    }
  }
}

module "eks_ap_south_1" {
  source = "./modules/compute"
  providers = { aws = aws.ap_south_1 }

  cluster_name   = "catedral-ap-south-1"
  vpc_id         = module.vpc_ap_south_1.vpc_id
  subnet_ids     = module.vpc_ap_south_1.private_subnets
  node_groups = {
    guardian = {
      instance_types = ["c6i.4xlarge"]
      min_size       = 2
      max_size       = 8
      desired_size   = 4
      disk_size      = 100
    }
  }
}

variable "environment" { type = string; default = "production" }
variable "quantum_endpoint_sa" { type = string; default = "" }
variable "quantum_endpoint_eu" { type = string; default = "" }
variable "quantum_endpoint_ap" { type = string; default = "" }
variable "qubit_architecture" { type = string; default = "rydberg_array" }
variable "gate_fidelity_target" { type = number; default = 0.999 }
variable "coherence_time_target_ms" { type = number; default = 500 }
variable "pagerduty_key" { type = string; default = "" }
variable "slack_webhook" { type = string; default = "" }
