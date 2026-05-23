# Ops Runbook: ARKHE OS Unified Mesh (Substrate 9047-C)

## 1. Build and Lint

### Podman Build
```bash
podman build -t arkhe:unified-v∞.Ω.∇+++ -f substrates/500-599_advanced/substrato_unified_container/arkhe_unified/Podmanfile.unified .
```

### Terraform Lint
```bash
cd terraform/arkhe_unified
terraform init -backend=false
terraform validate
terraform fmt -check
```

### Helm Lint
```bash
helm lint helm-arkhe-os-unified/
```

## 2. Deploy Flows by Cloud

### AWS Deploy
```bash
cd terraform/arkhe_unified
terraform workspace select aws || terraform workspace new aws
terraform apply -var="environment=production" -target=module.aws_infrastructure -target=module.kubernetes_core
```

### GCP Deploy
```bash
cd terraform/arkhe_unified
terraform workspace select gcp || terraform workspace new gcp
terraform apply -var="environment=production" -target=module.gcp_infrastructure -target=module.kubernetes_core
```

### Azure Deploy
```bash
cd terraform/arkhe_unified
terraform workspace select azure || terraform workspace new azure
terraform apply -var="environment=production" -target=module.azure_infrastructure -target=module.kubernetes_core
```
