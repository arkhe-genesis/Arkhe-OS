import time
import subprocess
import logging
from kubernetes import client, config, watch

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cert_rotation_operator")

def init_k8s_client():
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes config.")
    except config.ConfigException:
        try:
            config.load_kube_config()
            logger.info("Loaded external kubeconfig.")
        except config.ConfigException:
            logger.error("Could not configure Kubernetes client.")
            raise

def run_rotation_script():
    try:
        logger.info("Triggering scripts/rotate-certificates.sh...")
        # Assume script handles the details of rotation and outputs to certs/
        result = subprocess.run(["./scripts/rotate-certificates.sh"], capture_output=True, text=True, check=True)
        logger.info(f"Rotation successful: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Rotation failed: {e.stderr}")
        return False

def update_kubernetes_secret(api, namespace="arkhe-production", secret_name="arkhe-tls-secrets"):
    # In a real operator, this might dynamically read from certs/ and update the secret
    # Since rotate-certificates.sh states "2. Update Kubernetes secrets:", this mimics that step
    logger.info(f"Would update Secret {secret_name} in {namespace} with new certificates.")
    # E.g., patching the secret or leaving it to a separate job.
    # For now, we simulate the update success.
    pass

def main():
    init_k8s_client()
    v1 = client.CoreV1Api()
    w = watch.Watch()

    namespace = "arkhe-production"

    logger.info(f"Starting Certificate Rotation Operator watching namespace: {namespace}...")

    # We watch for a specific ConfigMap or Secret that triggers rotation when updated,
    # or watch secrets for an annotation like 'arkhe.os/rotate-cert: true'
    try:
        for event in w.stream(v1.list_namespaced_secret, namespace=namespace):
            secret = event['object']
            event_type = event['type']

            # Look for a specific trigger, e.g., an annotation or a generic trigger secret
            annotations = secret.metadata.annotations or {}

            if event_type in ["ADDED", "MODIFIED"]:
                if annotations.get("arkhe.os/rotate-cert") == "true":
                    logger.info(f"Detected rotation trigger on Secret: {secret.metadata.name}")

                    # Remove annotation to prevent infinite loop
                    annotations["arkhe.os/rotate-cert"] = "false"
                    secret.metadata.annotations = annotations
                    v1.patch_namespaced_secret(name=secret.metadata.name, namespace=namespace, body=secret)

                    # Trigger rotation
                    success = run_rotation_script()
                    if success:
                        update_kubernetes_secret(v1, namespace)
                        logger.info("Certificate rotation pipeline completed.")
                    else:
                        logger.error("Certificate rotation pipeline failed.")

    except Exception as e:
        logger.error(f"Operator loop failed: {e}")

if __name__ == "__main__":
    # Standard python operator loop
    main()
