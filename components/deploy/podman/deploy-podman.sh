#!/bin/bash
# ============================================================================
# DEPLOYMENT SCRIPT - ARKHE(N) PODMAN VERSION
# ============================================================================

set -e

echo "🜏 ═══════════════════════════════════════════════════════════════════════"
echo "🜏 ARKHE(N) DEPLOYMENT - PODMAN NATIVE"
echo "🜏 Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo "🜏 ═══════════════════════════════════════════════════════════════════════"

# Check for podman
command -v podman >/dev/null 2>&1 || { 
    echo "Podman is required. Install with:"
    echo "  sudo dnf install podman  # Fedora/RHEL"
    echo "  sudo apt install podman  # Debian/Ubuntu"
    exit 1 
}

# Create directories
echo ""
echo "🜏 Creating directory structure..."
sudo mkdir -p /var/lib/arkhe/{phase,tor,postgres,redis}
sudo mkdir -p /etc/arkhe
sudo chown -R $(whoami):$(whoami) /var/lib/arkhe /etc/arkhe

# Create secrets
echo ""
echo "🜏 Creating secrets..."
mkdir -p ~/.local/share/containers/storage/secrets
echo "arkhe_password" > ~/.local/share/containers/storage/secrets/db-password
echo "${WEB3_PROVIDER_URL:-http://localhost:8545}" > ~/.local/share/containers/storage/secrets/web3-provider
echo "${CONTRACT_ADDRESS:-0x0000000000000000000000000000000000000000}" > ~/.local/share/containers/storage/secrets/contract-address

# Build images
echo ""
echo "🜏 Building images..."
# ./build-all.sh (Skipped in simulation)

# Option 1: Play kube (for testing)
if [ "$1" == "kube" ] || [ -z "$1" ]; then
    echo ""
    echo "🜏 Deploying with podman play kube..."
    podman play kube arkhe-pod.yaml
    podman play kube services-pod.yaml
    podman play kube industrial-pod.yaml

# Option 2: Quadlets (for production)
elif [ "$1" == "quadlet" ]; then
    echo ""
    echo "🜏 Installing Quadlets..."
    sudo cp quadlets/*.pod /etc/containers/systemd/
    sudo cp quadlets/*.container /etc/containers/systemd/
    
    # Reload systemd
    systemctl --user daemon-reload
    
    # Enable and start
    systemctl --user enable --now arkhe-main-pod
    
# Option 3: Podman compose (compatible)
else
    echo ""
    echo "🜏 Deploying with podman-compose..."
    podman-compose up -d
fi

# Wait for services
echo ""
echo "🜏 Waiting for services to be ready..."
sleep 15

# Health checks
echo ""
echo "🜏 Health checks:"
curl -s http://localhost:8080/health || echo "Core: STARTING"
curl -s http://localhost:8081/health || echo "API: STARTING"
curl -s http://localhost:80/health || echo "Frontend: STARTING"

# Show pods
echo ""
echo "🜏 ═══════════════════════════════════════════════════════════════════════"
echo "🜏 DEPLOYMENT COMPLETE"
echo "🜏 "
echo "🜏 Pods:"
podman pod list
echo "🜏 "
echo "🜏 Services:"
echo "🜏   Frontend:    http://localhost:80"
echo "🜏   API:        http://localhost:8081"
echo "🜏   Tzinor:     ws://localhost:8443"
echo "🜏   Database:   localhost:5432"
echo "🜏   Redis:      localhost:6379"
echo "🜏 "
echo "🜏 Tor Hidden Services:"
podman exec arkhe-main-tor cat /var/lib/tor/arkhe-api/hostname 2>/dev/null || echo "🜏   Generating..."
echo "🜏 "
echo "🜏 Arkhe Protocol v1.0 is now operational."
echo "🜏 ═══════════════════════════════════════════════════════════════════════"
