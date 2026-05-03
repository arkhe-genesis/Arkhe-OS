#!/bin/bash
# scripts/rotate-certificates.sh
# Rotates TLS certificates for all ARKHE microservices

set -euo pipefail

ROTATION_DAYS=90
CERTS_DIR="certs"
CA_DIR="${CERTS_DIR}/ca"

echo "🔄 Starting certificate rotation (${ROTATION_DAYS}-day validity)"

# Generate new CA if expiring soon (optional)
if openssl x509 -in "${CA_DIR}/ca-cert.pem" -checkend $((ROTATION_DAYS * 86400)) -noout; then
    echo "✅ CA certificate valid for another ${ROTATION_DAYS} days"
else
    echo "⚠️  CA certificate expiring soon; regenerating..."
    # Regenerate CA (requires secure key management)
    # openssl req -new -x509 -days 3650 ... (see generate-tls-certs.sh)
fi

# Rotate service certificates
for service in sophon-network crystal-brain octra; do
    SERVICE_DIR="${CERTS_DIR}/${service}"

    echo "[${service}] Generating new certificate..."

    # Generate new key and CSR
    openssl genrsa -out "${SERVICE_DIR}/server-key-new.pem" 2048
    openssl req -new -key "${SERVICE_DIR}/server-key-new.pem" \
        -out "${SERVICE_DIR}/server-csr-new.pem" \
        -subj "/C=BR/ST=SP/L=SaoPaulo/O=ARKHE OS/OU=Services/CN=arkhe-${service}"

    # Sign with CA
    openssl x509 -req -in "${SERVICE_DIR}/server-csr-new.pem" \
        -CA "${CA_DIR}/ca-cert.pem" -CAkey "${CA_DIR}/ca-key.pem" \
        -CAcreateserial -out "${SERVICE_DIR}/server-cert-new.pem" \
        -days ${ROTATION_DAYS} -sha256 \
        -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1")

    # Create new PKCS12 keystore
    openssl pkcs12 -export \
        -in "${SERVICE_DIR}/server-cert-new.pem" \
        -inkey "${SERVICE_DIR}/server-key-new.pem" \
        -out "${SERVICE_DIR}/server-keystore-new.p12" \
        -name "arkhe-${service}" \
        -passout pass:"${KEYSTORE_PASSWORD}"

    # Backup old certificates
    mv "${SERVICE_DIR}/server-keystore.p12" "${SERVICE_DIR}/server-keystore.p12.bak"
    mv "${SERVICE_DIR}/server-key.pem" "${SERVICE_DIR}/server-key.pem.bak"

    # Activate new certificates
    mv "${SERVICE_DIR}/server-keystore-new.p12" "${SERVICE_DIR}/server-keystore.p12"
    mv "${SERVICE_DIR}/server-key-new.pem" "${SERVICE_DIR}/server-key.pem"

    echo "[${service}] ✅ Certificate rotated"
done

echo "🔄 Certificate rotation complete"
echo ""
echo "📋 Next steps:"
echo "  1. Deploy updated keystores to all pods (rolling update)"
echo "  2. Monitor /actuator/health for TLS handshake errors"
echo "  3. Remove backup files after 24h: find certs -name '*.bak' -mtime +1 -delete"
