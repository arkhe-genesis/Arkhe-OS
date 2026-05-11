variable "cluster_name" {
  type    = string
  default = "arkhe-production"
}

provider "aws" {
  region = "us-east-1"
}

# Dummy EKS resource for demonstration
resource "aws_eks_cluster" "arkhe" {
  name     = var.cluster_name
  role_arn = "arn:aws:iam::123456789012:role/dummy-role"

  vpc_config {
    subnet_ids = ["subnet-123", "subnet-456"]
  }
}
