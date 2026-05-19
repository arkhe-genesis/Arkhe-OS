#!/bin/bash
# Script para executar arkheReleaseReadiness dentro do OpenShell para validacao Android/iOS/FIPS
set -e

echo "Criando sandbox OpenShell com egress controlado..."
openshell sandbox create --name arkhe-release --policy arkhe-release-readiness.policy.yaml

echo "Executando validação Python P1-P7..."
openshell sandbox exec arkhe-release -- bash -c "python3 validate_public_policy.py"

echo "Executando validação Gradle Android/iOS/FIPS..."
openshell sandbox exec arkhe-release -- bash -c "./gradlew build -Pvalidation=Android,iOS,FIPS"

echo "Coletando relatórios de validação..."
mkdir -p ./reports
openshell sandbox pull arkhe-release /app/build/reports ./reports
openshell sandbox pull arkhe-release /app/validation_results.json ./reports/ 2>/dev/null || true

echo "Validação concluída com sucesso."
