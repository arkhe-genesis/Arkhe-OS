# Arkhe ASI - Operational Runbook

## 1. Overview
This runbook covers the standard operational flows to build, lint, and deploy the Arkhe ASI container and infrastructure across local and cloud environments (AWS, GCP, Azure).

## 2. Prerequisites
- Docker / Podman
- Helm (v3+)
- Terraform (v1.5+)
- Make

## 3. Operational Flows

### 3.1. Build Flow
The build phase compiles the multi-architecture container images using the consolidated `Podmanfile`/`Dockerfile`.
```bash
make build
```
*Note: Ensure your container runtime supports multi-arch buildx extensions if targeting multiple architectures.*

### 3.2. Lint Flow
The lint phase ensures both infrastructure as code (Terraform) and application deployment manifests (Helm) are syntactically correct and follow best practices.
```bash
make lint
```
*Includes: `terraform fmt -check` and `helm lint`.*

### 3.3. Deploy Flow
The deploy phase automates the provisioning of the cloud infrastructure and the deployment of the Helm chart onto the resulting Kubernetes cluster.
```bash
make deploy-cloud
```
*Executes: `terraform apply` followed by `helm upgrade --install`.*

## 4. Cloud-Specific Deployments

### AWS (Amazon Web Services)
1. Authenticate using `aws configure`.
2. Ensure `aws_region`, `aws_profile`, and cluster details are correctly set in your `terraform.tfvars`.
3. Run `make deploy-cloud`.

### GCP (Google Cloud Platform)
1. Authenticate using `gcloud auth application-default login`.
2. Ensure `gcp_project`, `gcp_region`, and `gcp_zone` are defined in your `terraform.tfvars`.
3. Run `make deploy-cloud`.

### Azure (Microsoft Azure)
1. Authenticate using `az login`.
2. Ensure `azure_subscription_id`, `azure_tenant_id`, and `azure_location` are defined in your `terraform.tfvars`.
3. Run `make deploy-cloud`.

## 5. Local Development Validation
For local development, utilize the consolidated `terraform.tfvars.example` to mock cloud environments before pushing state changes.
