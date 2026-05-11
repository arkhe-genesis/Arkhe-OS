resource "aws_eks_addon" "nvidia_device_plugin" {
  cluster_name = var.eks_cluster_name
  addon_name   = "nvidia-device-plugin"
}

resource "helm_release" "arkhe_orbital" {
  name       = "arkhe-orbital"
  chart      = "./helm/arkhe-orbital"
  namespace  = "orbital-mesh"
  set {
    name  = "hardwareProfile"
    value = "nvidia-vera-rubin"
  }
}
