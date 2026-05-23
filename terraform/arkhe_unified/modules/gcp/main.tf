# GCP Module Placeholder
variable "project_id" {}
variable "region" {}
variable "cluster_name" {}
variable "num_workers" {}

output "cluster_endpoint" {
  value = "https://gcp-arkhe-mesh-endpoint.example.com"
}
