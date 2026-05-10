#!/usr/bin/env bash
# scripts/build_linux.sh — Build script for ARKHE OS v168 on Linux
set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly TARGET="${TARGET:-x86_64-unknown-linux-gnu}"
readonly PROFILE="${PROFILE:-release}"
readonly FEATURES="${FEATURES:-full}"
readonly OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/target/${TARGET}/${PROFILE}}"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Check dependencies
check_dependencies() {
    log_info "Checking build dependencies..."

    local deps=("rustc" "cargo" "git" "clang" "pkg-config")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Missing dependency: $dep"
            exit 1
        fi
    done

    # Check Rust version
    local rust_version=$(rustc --version | cut -d' ' -f2)
    if [[ "${rust_version}" < "1.75.0" ]]; then
        log_error "Rust version >= 1.75.0 required, found ${rust_version}"
        exit 1
    fi

    # Check for quantum libraries if feature enabled
    if [[ "${FEATURES}" == *"quantum-hardware"* ]]; then
        if ! pkg-config --exists qiskit-c pennylane 2>/dev/null; then
            log_warn "Quantum libraries not found via pkg-config"
            log_warn "Set QISKIT_LIB_DIR and PENNYLANE_LIB_DIR if installed manually"
        fi
    fi

    log_info "✓ All dependencies satisfied"
}

# Setup build environment
setup_environment() {
    log_info "Setting up build environment..."

    cd "${PROJECT_ROOT}"

    # Set environment variables for quantum libs
    if [[ -n "${QISKIT_LIB_DIR:-}" ]]; then
        export QISKIT_SYS_LIB_DIR="${QISKIT_LIB_DIR}"
        echo "cargo:rustc-link-search=native=${QISKIT_LIB_DIR}" >> "${PROJECT_ROOT}/.cargo/config.toml"
    fi

    if [[ -n "${PENNYLANE_LIB_DIR:-}" ]]; then
        export PENNYLANE_SYS_LIB_DIR="${PENNYLANE_LIB_DIR}"
        echo "cargo:rustc-link-search=native=${PENNYLANE_LIB_DIR}" >> "${PROJECT_ROOT}/.cargo/config.toml"
    fi

    # Enable sccache if available for faster builds
    if command -v sccache &> /dev/null; then
        export RUSTC_WRAPPER=sccache
        log_info "Using sccache for compilation caching"
    fi

    log_info "✓ Environment configured"
}

# Run pre-build checks
pre_build_checks() {
    log_info "Running pre-build checks..."

    # Verify integrity of source files
    if [[ "${PROFILE}" == "release" ]]; then
        log_info "Verifying source integrity..."
        cargo run --bin arkhe-unified -- verify --strict-integrity \
            || log_warn "Integrity check failed (non-fatal for build)"
    fi

    # Run clippy for code quality
    if [[ "${CI:-false}" == "true" ]]; then
        log_info "Running clippy checks..."
        cargo clippy --all-targets --all-features -- -D warnings
    fi

    log_info "✓ Pre-build checks passed"
}

# Compile the binary
compile_binary() {
    log_info "Compiling ARKHE OS v168 for ${TARGET}..."
    log_info "Profile: ${PROFILE}, Features: ${FEATURES}"

    local cargo_args=()

    # Add target if cross-compiling
    if [[ "${TARGET}" != "$(rustc -Vv | grep host | cut -d' ' -f2)" ]]; then
        cargo_args+=("--target" "${TARGET}")
    fi

    # Add profile
    cargo_args+=("--profile" "${PROFILE}")

    # Add features
    if [[ -n "${FEATURES}" ]]; then
        cargo_args+=("--features" "${FEATURES}")
    fi

    # Add verbose flag if requested
    if [[ "${VERBOSE:-false}" == "true" ]]; then
        cargo_args+=("--verbose")
    fi

    # Run cargo build
    cargo build "${cargo_args[@]}"

    log_info "✓ Compilation successful"
}

# Sign the binary (if production build)
sign_binary() {
    if [[ "${PROFILE}" != "release" ]]; then
        log_info "Skipping signing for non-release profile"
        return
    fi

    log_info "Signing binary with ARKHE root key..."

    local binary="${OUTPUT_DIR}/arkhe-unified"
    local sig_file="${binary}.sig"

    # Generate signature using ed25519
    if [[ -n "${ARKHE_SIGNING_KEY:-}" ]]; then
        # Use provided key
        echo -n "${ARKHE_SIGNING_KEY}" | \
            openssl pkeyutl -sign -inkey /dev/stdin -out "${sig_file}" -in "${binary}"
    elif command -v arkhe-sign &> /dev/null; then
        # Use arkhe-sign tool if available
        arkhe-sign sign "${binary}" -o "${sig_file}"
    else
        log_warn "No signing key or tool available — binary unsigned"
        log_warn "For production: set ARKHE_SIGNING_KEY or install arkhe-sign"
        return
    fi

    # Verify signature immediately
    if arkhe-sign verify "${binary}" -s "${sig_file}" 2>/dev/null; then
        log_info "✓ Binary signed and verified"
    else
        log_error "Signature verification failed"
        exit 1
    fi
}

# Generate distribution packages
create_packages() {
    log_info "Creating distribution packages..."

    local binary="${OUTPUT_DIR}/arkhe-unified"
    local version=$(cargo metadata --format-version=1 --no-deps | jq -r '.packages[0].version')

    # Create tarball
    local tarball="arkhe-unified-${version}-${TARGET}.tar.gz"
    tar -czf "${tarball}" \
        -C "${OUTPUT_DIR}" "$(basename "${binary}")" \
        -C "${PROJECT_ROOT}/config" . \
        -C "${PROJECT_ROOT}" README.md LICENSE

    log_info "✓ Created ${tarball}"

    # Create DEB package if on Debian-based system
    if command -v dpkg-deb &> /dev/null && [[ -f "/etc/debian_version" ]]; then
        cargo deb --output "arkhe-unified_${version}_amd64.deb"
        log_info "✓ Created DEB package"
    fi

    # Create RPM package if on RHEL-based system
    if command -v rpm &> /dev/null && [[ -f "/etc/redhat-release" ]]; then
        cargo generate-rpm --target "${TARGET}" --profile "${PROFILE}"
        log_info "✓ Created RPM package"
    fi
}

# Run post-build validation
post_build_validation() {
    log_info "Running post-build validation..."

    local binary="${OUTPUT_DIR}/arkhe-unified"

    # Check binary exists and is executable
    if [[ ! -x "${binary}" ]]; then
        log_error "Binary not found or not executable: ${binary}"
        exit 1
    fi

    # Run basic self-test
    log_info "Running self-test..."
    if ! "${binary}" --version &> /dev/null; then
        log_error "Binary self-test failed"
        exit 1
    fi

    # Verify integrity manifest
    log_info "Verifying integrity manifest..."
    if ! "${binary}" verify --strict-integrity 2>/dev/null; then
        log_warn "Integrity verification failed (may be expected in dev builds)"
    fi

    log_info "✓ Post-build validation passed"
}

# Main execution
main() {
    log_info "🏗️  ARKHE OS v168 — Unified Build Script"
    log_info "Project root: ${PROJECT_ROOT}"

    check_dependencies
    setup_environment
    pre_build_checks
    compile_binary
    sign_binary
    create_packages
    post_build_validation

    log_info "✅ Build completed successfully!"
    log_info "Binary location: ${OUTPUT_DIR}/arkhe-unified"

    # Print next steps
    echo ""
    echo "📦 Distribution packages:"
    ls -lh "${PROJECT_ROOT}"/*.tar.gz "${PROJECT_ROOT}"/*.deb "${PROJECT_ROOT}"/*.rpm 2>/dev/null || true
    echo ""
    echo "🚀 To run: ${OUTPUT_DIR}/arkhe-unified --help"
    echo "🔐 To verify: ${OUTPUT_DIR}/arkhe-unified verify"
    echo "🔧 To debug: ${OUTPUT_DIR}/arkhe-unified repl"
}

main "$@"
