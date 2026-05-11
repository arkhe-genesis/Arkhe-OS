resource "aws_eks_cluster" "arkhe" {
  name     = "arkhe-continental"
  role_arn = aws_iam_role.cluster.arn
  vpc_config {
    subnet_ids = module.vpc.private_subnets
  }
}

resource "aws_eks_node_group" "gpu_shards" {
  cluster_name    = aws_eks_cluster.arkhe.name
  node_group_name = "gpu-shards"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = module.vpc.private_subnets
  instance_types  = ["p4d.24xlarge"]
  scaling_config {
    desired_size = 4
    max_size     = 100
    min_size     = 1
  }
}
