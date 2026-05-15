# Módulo AWS — Provisiona EKS + VPC + S3 para Delta Lake

variable "cluster_name" {}
variable "num_workers" {}
variable "enable_kafka" { default = true }
variable "enable_spark" { default = true }
variable "tags" { type = map(string) }

resource "aws_vpc" "mesh_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = { Name = "${var.cluster_name}-vpc" }
}

resource "aws_subnet" "mesh_subnet" {
  vpc_id     = aws_vpc.mesh_vpc.id
  cidr_block = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = { Name = "${var.cluster_name}-subnet" }
}

resource "aws_iam_role" "eks_role" {
  name = "${var.cluster_name}-eks-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role" "node_role" {
  name = "${var.cluster_name}-node-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_eks_cluster" "mesh_cluster" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_role.arn

  vpc_config {
    subnet_ids = [aws_subnet.mesh_subnet.id]
  }
}

resource "aws_eks_node_group" "mesh_workers" {
  cluster_name    = aws_eks_cluster.mesh_cluster.name
  node_group_name = "${var.cluster_name}-workers"
  node_role_arn   = aws_iam_role.node_role.arn
  subnet_ids      = [aws_subnet.mesh_subnet.id]

  scaling_config {
    desired_size = var.num_workers
    max_size     = var.num_workers * 3
    min_size     = 3
  }

  instance_types = ["c5.2xlarge"]
}

# Bucket S3 para Delta Lake
resource "aws_s3_bucket" "delta_lake" {
  bucket = "${var.cluster_name}-delta-lake"
}

resource "aws_s3_bucket_versioning" "delta_lake_versioning" {
  bucket = aws_s3_bucket.delta_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "delta_lake_lifecycle" {
  bucket = aws_s3_bucket.delta_lake.id

  rule {
    id      = "expiration"
    status  = "Enabled"

    expiration {
      days = 365
    }
  }
}

output "cluster_endpoint" {
  value = aws_eks_cluster.mesh_cluster.endpoint
}