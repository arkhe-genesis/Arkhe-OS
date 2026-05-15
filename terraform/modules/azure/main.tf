variable "resource_group" {}
variable "location" {}
variable "cluster_name" {}
variable "num_workers" {}

output "cluster_endpoint" {
  value = "mock_azure_endpoint"
}