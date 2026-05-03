#!/bin/bash
# deploy-multi-platform.sh — Deploy ARKHE Certificate Operator across platforms

set -euo pipefail

# Configuration
PLATFORMS=("azure" "gcp" "apple" "oracle")
CONFIG_DIR="config/platform"
CHART_PATH="charts/arkhe-cert-operator"
DRY_RUN="${DRY_RUN:-false}"

log() {
    echo "[$(date +%H:%M:%S)] $*" >&2
}

deploy_platform() {
    local platform=$1
    local env=${2:-staging}
    local config_file="${CONFIG_DIR}/${platform}-platform-config.yaml"

    log "Deploying to ${platform} (${env})..."

    if [[ ! -f "$config_file" ]]; then
        log "ERROR: Config file not found: $config_file"
        return 1
    fi

    # Load platform-specific values
    local values_file="${CONFIG_DIR}/${platform}-${env}-values.yaml"
    if [[ ! -f "$values_file" ]]; then
        log "WARNING: No environment-specific values file; using defaults"
        values_file="/dev/null"
    fi

    # Build Helm command
    local helm_cmd=(
        helm upgrade --install
        "arkhe-cert-operator-${platform}"
        "$CHART_PATH"
        --namespace "arkhe-${platform}-${env}"
        --create-namespace
        --set "platform.type=${platform}"
        --values "$config_file"
    )

    # Add environment-specific values if exists
    if [[ -f "$values_file" && "$values_file" != "/dev/null" ]]; then
        helm_cmd+=(--values "$values_file")
    fi

    # Add dry-run flag if requested
    if [[ "$DRY_RUN" == "true" ]]; then
        helm_cmd+=(--dry-run)
        log "DRY RUN: ${helm_cmd[*]}"
    else
        log "Executing: ${helm_cmd[*]}"
        "${helm_cmd[@]}"
    fi

    # Wait for deployment to be ready
    if [[ "$DRY_RUN" != "true" ]]; then
        log "Waiting for deployment to be ready..."
        kubectl rollout status deployment/arkhe-cert-operator \
            -n "arkhe-${platform}-${env}" --timeout=300s
    fi

    log "✅ Deployment to ${platform} (${env}) completed"
}

# Main execution
main() {
    log "🚀 ARKHE OS Multi-Platform Deployment"
    log "Platforms: ${PLATFORMS[*]}"
    log "Dry run: ${DRY_RUN}"

    for platform in "${PLATFORMS[@]}"; do
        # Deploy to staging first, then production if staging succeeds
        if deploy_platform "$platform" "staging"; then
            if [[ "${DEPLOY_PRODUCTION:-false}" == "true" ]]; then
                deploy_platform "$platform" "production"
            fi
        else
            log "❌ Failed to deploy to ${platform} staging; skipping production"
        fi
    done

    log "🎉 Multi-platform deployment completed"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORMS=("$2")
            shift 2
            ;;
        --env)
            ENV_OVERRIDE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --deploy-production)
            DEPLOY_PRODUCTION=true
            shift
            ;;
        *)
            log "Unknown option: $1"
            exit 1
            ;;
    esac
done

main "$@"