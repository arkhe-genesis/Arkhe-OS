module "arkhe_cluster" {
  source = "./modules/arkhe"

  cloud_provider = var.cloud_provider        # aws, gcp, azure
  node_count     = 3
  kubernetes     = true
  enable_phi_c_monitoring = true

  temporal_chain_endpoint = var.temporal_endpoint
}
