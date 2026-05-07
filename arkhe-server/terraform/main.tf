provider "aws" {
  region = "us-west-2"
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = "arkhe-cluster"
  cluster_version = "1.21"
  subnets         = ["subnet-abcde012", "subnet-bcde012a", "subnet-fghi345a"]
  vpc_id          = "vpc-1234556abcdef"

  node_groups = {
    eks_nodes = {
      desired_capacity = 3
      max_capacity     = 10
      min_capacity     = 3
      instance_type    = "m5.large"
    }
  }
}

provider "google" {
  project = "arkhe-project"
  region  = "us-central1"
}

resource "google_container_cluster" "gke_cluster" {
  name     = "arkhe-gke-cluster"
  location = "us-central1"
  initial_node_count = 3

  node_config {
    machine_type = "e2-medium"
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_kubernetes_cluster" "aks_cluster" {
  name                = "arkhe-aks-cluster"
  location            = "East US"
  resource_group_name = "arkhe-resources"
  dns_prefix          = "arkheaks"

  default_node_pool {
    name       = "default"
    node_count = 3
    vm_size    = "Standard_DS2_v2"
  }

  identity {
    type = "SystemAssigned"
  }
}
