#!/bin/bash
# Deploy canário para 5% dos shards Vera Rubin
kubectl set image statefulset/arkhe-vera-rubin \
  continental-mind=arkhe/continental-mind:${VERSION} \
  -n orbital-mesh

# Aguardar health check
sleep 300
kubectl exec -n orbital-mesh deploy/health-checker -- \
  arkhe verify-mesh --min-fidelity 0.999
