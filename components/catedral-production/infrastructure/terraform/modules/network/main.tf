variable "region_name" {}
variable "cidr_block" {}
variable "availability_zones" { type = list(string) }
variable "enable_nat_gateway" { default = true }
variable "enable_flow_logs" { default = true }

output "vpc_id" { value = "vpc-123" }
output "private_subnets" { value = ["subnet-1", "subnet-2"] }
