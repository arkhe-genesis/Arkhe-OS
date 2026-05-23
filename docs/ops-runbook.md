# ARKHE OS - Operations Runbook

This runbook outlines the steps for building, linting, and deploying the ARKHE OS Unified Container Runtime across different environments.

## Prerequisites
- `make` installed.
- `podman` installed for local builds and rootless runtime.
- Terraform for cloud deployments.

## Standard Flows

### Linting
To check for syntax errors and forbidden f-strings (as per core invariants):
```bash
make lint
```

### Build
To build the Podman container image (`arkhe:v∞.Ω.∇+++`):
```bash
make build
```

### Local Testing
To run the full test suite (`test_substrates.py`):
```bash
make test
```

## Deployment Flows

### Local Development (Podman Rootless)
Deploy locally using Podman Quadlet and systemd integration:
```bash
make deploy
```
This script handles network setup, pod orchestration, and systemd service generation.

### Cloud Deployments (via Terraform)
We provide a consolidated `terraform/terraform.tfvars.example` that supports multiple clouds.

#### AWS (EKS)
1. Configure `terraform.tfvars` with `cloud_provider = "aws"`.
2. Ensure AWS CLI is configured.
3. Run deployment:
```bash
cd terraform
terraform init
terraform apply
```

#### GCP (GKE)
1. Configure `terraform.tfvars` with `cloud_provider = "gcp"`.
2. Authenticate with `gcloud auth application-default login`.
3. Run deployment:
```bash
cd terraform
terraform init
terraform apply
```

#### Azure (AKS)
1. Configure `terraform.tfvars` with `cloud_provider = "azure"`.
2. Login via `az login`.
3. Run deployment:
```bash
cd terraform
terraform init
terraform apply
```

## Security Posture
- Ensure all deployments respect the `227-F Principle XVI (SCALED PEACE)` by defaulting to rootless execution whenever possible.
- Capabilities are strictly dropped to minimize surface area (`--cap-drop=ALL --cap-add=NET_BIND_SERVICE`).
