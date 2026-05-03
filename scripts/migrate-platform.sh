#!/bin/bash
# migrate-platform.sh — Assist migration from single-platform to multi-platform ARKHE OS

set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*" >&2; }

# Configuration
SOURCE_PLATFORM="${SOURCE_PLATFORM:-kubernetes}"
TARGET_PLATFORMS=("${@:-azure gcp}")  # Default to Azure and GCP if no args
MIGRATION_MODE="${MIGRATION_MODE:-parallel}"  # or "sequential"
DRY_RUN="${DRY_RUN:-false}"

validate_migration_prerequisites() {
    log "Validating migration prerequisites..."

    # Check source platform health
    if ! kubectl get pods -l app.kubernetes.io/name=arkhe-cert-operator -A --no-headers | grep -q "Running"; then
        log "ERROR: Source platform operator not healthy"
        return 1
    fi

    # Check target platform credentials
    for platform in "${TARGET_PLATFORMS[@]}"; do
        case $platform in
            azure)
                [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]] || { log "ERROR: AZURE_SUBSCRIPTION_ID not set"; return 1; }
                ;;
            gcp)
                [[ -n "${GCP_PROJECT_ID:-}" ]] || { log "ERROR: GCP_PROJECT_ID not set"; return 1; }
                ;;
            apple)
                [[ "$(uname -s)" == "Darwin" ]] || { log "WARNING: Apple platform tests require macOS"; }
                ;;
            oracle)
                [[ -n "${OCI_TENANCY_OCID:-}" ]] || { log "ERROR: OCI_TENANCY_OCID not set"; return 1; }
                ;;
        esac
    done

    log "✅ Prerequisites validated"
}

migrate_platform() {
    local platform=$1

    log "Migrating to ${platform}..."

    # Step 1: Export current ARKHE configuration from source platform
    log "Exporting configuration from ${SOURCE_PLATFORM}..."
    local export_dir="/tmp/arkhe-migration-${platform}-$(date +%s)"
    mkdir -p "$export_dir"

    # Export ArkheCertificate CRs
    kubectl get arkhecertificate -A -o yaml > "${export_dir}/arkhecertificates.yaml"

    # Export keystore secrets (encrypted)
    kubectl get secret -l arkhe.os/backup=keystore -A -o yaml | \
        yq 'del(.items[].metadata.annotations, .items[].metadata.resourceVersion, .items[].metadata.uid)' > "${export_dir}/keystore-secrets.yaml"

    # Export configuration maps
    kubectl get configmap -l app.kubernetes.io/name=arkhe-cert-operator -A -o yaml > "${export_dir}/configmaps.yaml"

    # Step 2: Transform configuration for target platform
    log "Transforming configuration for ${platform}..."
    python3 scripts/transform-config-for-platform.py \
        --source "${SOURCE_PLATFORM}" \
        --target "${platform}" \
        --input-dir "${export_dir}" \
        --output-dir "${export_dir}/transformed"

    # Step 3: Deploy operator to target platform
    log "Deploying operator to ${platform}..."
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would execute: ./scripts/deploy-multi-platform.sh --platform ${platform} --env staging --dry-run"
    else
        ./scripts/deploy-multi-platform.sh --platform "${platform}" --env staging
    fi

    # Step 4: Migrate ArkheCertificate resources
    log "Migrating ArkheCertificate resources to ${platform}..."
    if [[ "$DRY_RUN" != "true" ]]; then
        kubectl apply -f "${export_dir}/transformed/arkhecertificates.yaml"

        # Wait for certificates to be issued
        log "Waiting for certificate issuance on ${platform}..."
        kubectl wait --for=condition=Ready arkhecertificate --all -A --timeout=300s
    fi

    # Step 5: Validate migration
    log "Validating migration to ${platform}..."
    if [[ "$DRY_RUN" != "true" ]]; then
        # Run platform-specific validation tests
        ./scripts/validate-platform-migration.sh --platform "${platform}" --export-dir "${export_dir}"

        # Compare certificate status between source and target
        log "Comparing certificate status..."
        python3 scripts/compare-certificate-status.py \
            --source "${SOURCE_PLATFORM}" \
            --target "${platform}" \
            --export-dir "${export_dir}"
    fi

    log "✅ Migration to ${platform} completed"
}

main() {
    log "🔄 ARKHE OS Platform Migration"
    log "Source: ${SOURCE_PLATFORM}"
    log "Targets: ${TARGET_PLATFORMS[*]}"
    log "Mode: ${MIGRATION_MODE}"
    log "Dry run: ${DRY_RUN}"

    validate_migration_prerequisites

    if [[ "$MIGRATION_MODE" == "parallel" ]]; then
        # Run migrations in parallel (background jobs)
        for platform in "${TARGET_PLATFORMS[@]}"; do
            migrate_platform "$platform" &
        done
        wait  # Wait for all background jobs to complete
    else
        # Run migrations sequentially
        for platform in "${TARGET_PLATFORMS[@]}"; do
            migrate_platform "$platform"
        done
    fi

    log "🎉 Platform migration completed"

    # Post-migration: generate report
    if [[ "$DRY_RUN" != "true" ]]; then
        log "Generating migration report..."
        python3 scripts/generate-migration-report.py \
            --source "${SOURCE_PLATFORM}" \
            --targets "${TARGET_PLATFORMS[*]}" \
            --output "/tmp/arkhe-migration-report-$(date +%Y%m%d).md"
    fi
}

main "$@"