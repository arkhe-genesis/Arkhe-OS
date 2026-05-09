variable "cluster_name" {}
variable "vpc_id" {}
variable "subnet_ids" { type = list(string) }
variable "node_groups" {}

output "cluster_endpoint" { value = "https://eks.example.com" }
