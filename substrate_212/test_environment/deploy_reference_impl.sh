#!/bin/bash
# ARKHE OS Substrato 212: Deploy Reference Implementation in Test Environment
# Canon: ∞.Ω.∇+++.212.test.deploy

set -e  # Exit on error

echo "🏛️ ARKHE Ω‑TEMP v∞.Ω — Substrato 212: Test Environment Deploy"
echo "   Deploying COBOL Parser Reference Implementation"
echo "   Target: Docker Compose (Local Test Cluster)"
echo ""

# Configuration
TEST_CLUSTER_NAME="arkhe-cobol-test"
DOCKER_COMPOSE_FILE="substrate_212/test_environment/docker-compose.yml"
ENV_FILE="substrate_212/test_environment/.env.test"

# Validate prerequisites
echo "🔍 Validating prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose not found"; exit 1; }
[ -f "$DOCKER_COMPOSE_FILE" ] || { echo "❌ Docker Compose file not found: $DOCKER_COMPOSE_FILE"; exit 1; }

# Load test environment variables
if [ -f "$ENV_FILE" ]; then
    echo "📦 Loading test environment variables..."
    set -a
    source "$ENV_FILE"
    set +a
fi

# Build and start test cluster
echo "🚀 Building and starting test cluster: $TEST_CLUSTER_NAME"
docker-compose -f "$DOCKER_COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run integration tests
echo "🧪 Running integration tests..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T cobol-parser python3 -m pytest /app/tests/ -v --tb=short

# Run COBOL parser demo
echo "🔍 Running COBOL parser demonstration..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T cobol-parser python3 /app/substrate_212/cobol_parser_canonical.py

# Run Verifier's Loop integration test
echo "🔄 Running Verifier's Loop integration test..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T verifier-loop python3 /app/substrate_202/reference_impl/verifier_loop_poc.py

# Check ERC-8004 contract deployment (if enabled)
if [ "$DEPLOY_ERC8004_CONTRACT" = "true" ]; then
    echo "🔐 Deploying ERC-8004 contract to testnet (Sepolia)..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T erc8004-deployer python3 /app/substrate_134/deploy_erc8004_testnet.py
fi

# Generate test report
echo "📊 Generating test report..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T cobol-parser python3 /app/substrate_212/test_environment/generate_test_report.py

# Output access information
echo ""
echo "✅ Test environment deployed successfully!"
echo ""
echo "🔗 Service Endpoints:"
echo "   • COBOL Parser API: http://localhost:8080"
echo "   • Φ_C Dashboard:    http://localhost:3000"
echo "   • Prometheus:       http://localhost:9090"
echo "   • Grafana:          http://localhost:3001"
echo ""
echo "📋 Test Report: /tmp/arkhe-cobol-test-report-$(date +%Y%m%d).json"
echo ""
echo "🛑 To stop the test environment:"
echo "   docker-compose -f $DOCKER_COMPOSE_FILE down"
