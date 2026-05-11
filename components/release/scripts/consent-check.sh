#!/bin/bash
echo "[INFO] Verificando consentimento para DID: ${OPERATOR_DID}"
if [[ "${OPERATOR_DID}" == "did:cathedral:maintainer:ferreiro" ]]; then
  echo "✅ Consentimento válido"
else
  echo "❌ Consentimento inválido"
fi
