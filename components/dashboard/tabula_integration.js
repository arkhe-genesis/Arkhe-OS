// dashboard/tabula_integration.js
// Adicionar ao dashboard existente

async function queryTabulaOracle(nuclearFeatures) {
  try {
    const response = await fetch('http://localhost:8081/predict/iao', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({features: nuclearFeatures})
    });

    if (!response.ok) throw new Error('Tabula API error');

    const result = await response.json();

    // Atualizar UI
    document.getElementById('iaoMetric').textContent = result.iao_pred.toFixed(4);
    document.getElementById('captureStatus').textContent =
      result.capture_likely ? '🟢 CAPTURE-like' : '🔴 Non-CAPTURE';
    document.getElementById('captureStatus').className =
      result.capture_likely ? 'status coherent' : 'status negative';

    // Atualizar gráfico de contribuições
    updateFeatureContributions(result.feature_contributions);

    return result;
  } catch (err) {
    console.warn('Tabula query failed:', err);
    document.getElementById('iaoMetric').textContent = '—';
    return null;
  }
}

// Chamar quando features do Crystal mudarem
function onCrystalFeaturesUpdated(features) {
  queryTabulaOracle(features);
}