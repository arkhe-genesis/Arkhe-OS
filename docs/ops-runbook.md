# Arkhe OS - Operations Runbook (Multi-Cloud)

This runbook outlines the standard operating procedures for provisioning, updating, and destroying the Arkhe Broadcast Mesh across AWS, GCP, and Azure using Terraform.

## Prerequisites

1.  **Terraform:** Version `1.5.0` or higher installed.
2.  **Cloud CLIs:**
    *   `aws-cli` configured with appropriate credentials.
    *   `gcloud` configured with `gcloud auth application-default login`.
    *   `az` configured with `az login`.
3.  **Make:** Installed for orchestration.

## 1. Local Development & Testing

For local development or testing a unified configuration, use the consolidated `terraform.tfvars.example` file.

1.  Copy the example to the active variable file:
    ```bash
    cp terraform/terraform.tfvars.example terraform/terraform.tfvars
    ```
2.  Adjust the variables as needed (e.g., lower `num_workers` to save costs).

### Linting

Always lint your code before proposing a pull request:

```bash
make lint
```
*This runs `terraform fmt -check` and `terraform validate`.*

## 2. Cloud-Specific Deployments (Targeted)

If you need to plan or deploy to a specific cloud to test isolation or rolling updates, you can target specific variables or modules (though the main configuration deploys all 3). The Make targets map to specific variable overlays if you want to override defaults per cloud during testing.

### AWS Workflow

1.  **Plan:**
    ```bash
    make plan-aws
    ```
2.  **Apply (Manual):**
    ```bash
    terraform -chdir=terraform apply -var-file=terraform.tfvars.example.aws
    ```

### GCP Workflow

1.  **Plan:**
    ```bash
    make plan-gcp
    ```
2.  **Apply (Manual):**
    ```bash
    terraform -chdir=terraform apply -var-file=terraform.tfvars.example.gcp
    ```

### Azure Workflow

1.  **Plan:**
    ```bash
    make plan-azure
    ```
2.  **Apply (Manual):**
    ```bash
    terraform -chdir=terraform apply -var-file=terraform.tfvars.example.azure
    ```

## 3. Full Mesh Deployment

To deploy the entire Arkhe Broadcast Mesh (AWS + GCP + Azure) simultaneously:

```bash
make deploy-all
```
*Note: This command runs with `-auto-approve`. Ensure you have reviewed the plan first.*

## 4. Teardown / Decommissioning

To destroy all provisioned infrastructure across all clouds:

```bash
make destroy-all
```
*Note: This command is irreversible and runs with `-auto-approve`.*

## Troubleshooting

*   **Authentication Errors:** Ensure your cloud CLI sessions haven't expired. Re-authenticate using the respective CLI commands.
*   **State Locks:** If Terraform state is locked, ensure no other operations are running. If it's a stale lock, force unlock using `terraform force-unlock <LOCK_ID>`.
