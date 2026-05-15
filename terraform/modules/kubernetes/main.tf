# Módulo Kubernetes — Deploy dos componentes core da malha

variable "deploy_temporal_chain" { default = true }
variable "deploy_phi_bus" { default = true }
variable "deploy_guardian" { default = true }
variable "deploy_kafka" { default = true }
variable "deploy_spark" { default = true }
variable "deploy_delta_lake" { default = true }
variable "deploy_mesh_orchestrator" { default = true }

variable "temporal_chain_version" {}
variable "mesh_orchestrator_image" {}

resource "kubernetes_namespace" "arkhe" {
  metadata {
    name = "arkhe-broadcast"
    labels = {
      substrate = "9047-C"
    }
  }
}

# TemporalChain
resource "helm_release" "temporal_chain" {
  count      = var.deploy_temporal_chain ? 1 : 0
  name       = "temporal-chain"
  repository = "https://charts.arkhe.org"
  chart      = "temporal-chain"
  version    = var.temporal_chain_version
  namespace  = kubernetes_namespace.arkhe.metadata[0].name

  set {
    name  = "storage.backend"
    value = "postgresql"
  }
}

# Phi‑Bus
resource "kubernetes_deployment" "phi_bus" {
  count      = var.deploy_phi_bus ? 1 : 0
  metadata {
    name      = "phi-bus"
    namespace = kubernetes_namespace.arkhe.metadata[0].name
  }

  spec {
    replicas = 2
    selector {
      match_labels = { app = "phi-bus" }
    }
    template {
      metadata { labels = { app = "phi-bus" } }
      spec {
        container {
          name  = "phi-bus"
          image = "arkhe/phi-bus:latest"
          env {
            name  = "TARGET_PHI_C"
            value = "1.0"
          }
        }
      }
    }
  }
}

# Kafka + Spark + Mesh Orchestrator
# (configurações similares omitidas por brevidade)

output "mesh_api_url" {
  value = "http://mesh-orchestrator.${kubernetes_namespace.arkhe.metadata[0].name}.svc.cluster.local:8053"
}