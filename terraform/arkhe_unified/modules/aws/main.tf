# AWS Module Placeholder
variable "cluster_name" {}
variable "num_workers" {}
variable "enable_kafka" {}
variable "enable_spark" {}
variable "tags" {}

output "cluster_endpoint" {
  value = "https://aws-arkhe-mesh-endpoint.example.com"
}
