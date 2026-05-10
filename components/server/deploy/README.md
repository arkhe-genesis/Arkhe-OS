# Arkhe(n) Cluster Deployment

This directory contains the deployment scripts, Kubernetes manifests, and Helm charts for deploying the Arkhe(n) cluster with Ray, NCCL, and Hashtree P2P integration.

## Prerequisites

- `kubectl` configured to point to your Kubernetes cluster.
- `helm` installed.
- `htree` CLI installed (for Hashtree P2P integration).
- A Kubernetes cluster with GPU nodes (A100/H100) available.

## Deployment

To deploy the cluster, you can run the `deploy.sh` script.

**Important:** If the script is not executable, you will need to run it using `bash` or make it executable manually:

```bash
# Option 1: Run with bash directly
bash deploy.sh

# Option 2: Make executable (if your environment permits)
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Create the `arkhe-system` namespace.
2. Configure the CUDA nodepool.
3. Deploy the Helm chart with the required values.
4. Wait for the Ray cluster to become ready.
5. Verify the deployed services.

## Components

- `kubernetes/`: Contains raw Kubernetes manifests (namespace, nodepool).
- `helm/`: Contains the Helm chart for deploying the Ray cluster, gRPC telemetry, and Hashtree P2P services.
- `nccl/`: Contains the CUDA C++ code and Python bindings for NCCL-based global resonance calculations.
- `grpc/`: Contains the Protocol Buffers definitions and Python implementations for the `qhttp://` protocol.
- `ray/`: Contains the Ray distributed trainer and ResonanceActor implementation.
- `hashtree/`: Contains the Python integration for the Hashtree P2P network.
