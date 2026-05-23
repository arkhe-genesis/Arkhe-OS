# Kubernetes Module Placeholder
variable "deploy_temporal_chain" {}
variable "deploy_phi_bus" {}
variable "deploy_guardian" {}
variable "deploy_kafka" {}
variable "deploy_spark" {}
variable "deploy_delta_lake" {}
variable "deploy_mesh_orchestrator" {}
variable "temporal_chain_version" {}
variable "mesh_orchestrator_image" {}

output "mesh_api_url" {
  value = "https://mesh-api.example.com"
}
