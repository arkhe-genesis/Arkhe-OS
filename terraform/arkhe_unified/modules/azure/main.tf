# Azure Module Placeholder
variable "resource_group" {}
variable "location" {}
variable "cluster_name" {}
variable "num_workers" {}

output "cluster_endpoint" {
  value = "https://azure-arkhe-mesh-endpoint.example.com"
}
