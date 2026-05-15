variable "project_id" {}
variable "region" {}
variable "cluster_name" {}
variable "num_workers" {}

output "cluster_endpoint" {
  value = "mock_gcp_endpoint"
}