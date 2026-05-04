// dashboard.js
let session = null;
let manifoldChart = null;

// Inicializar gráfico do manifold
function initChart() {
  const ctx = document.getElementById('manifoldChart').getContext('2d');
  manifoldChart = new Chart(ctx, {
    type: 'scatter',
    data: { datasets: [{ label: 'Crystal States', data: [], backgroundColor: 'rgba(125,223,255,0.6)' }] },
    options: {
      responsive: true,
      scales: {
        x: { title: { display: true, text: 'Dim 1' }, min: -2, max: 2 },
        y: { title: { display: true, text: 'Dim 2' }, min: -2, max: 2 }
      }
    }
  });
}

// Carregar modelo ONNX do arquivo local
async function loadModel() {
  const file = document.getElementById('modelInput').files[0];
  if (!file) { alert('Selecione um arquivo .onnx'); return; }

  document.getElementById('modelStatus').textContent = 'Carregando...';

  try {
    const arrayBuffer = await file.arrayBuffer();
    session = await ort.InferenceSession.create(arrayBuffer, {
      executionProviders: ['webgl'], // Usar GPU via WebGL se disponível
      graphOptimizationLevel: 'all'
    });

    document.getElementById('modelStatus').textContent = `✅ ${file.name} carregado`;
    console.log('Model inputs:', session.inputNames);
    console.log('Model outputs:', session.outputNames);
  } catch (err) {
    console.error('Erro ao carregar modelo:', err);
    document.getElementById('modelStatus').textContent = `❌ Erro: ${err.message}`;
  }
}

// Gerar fases sintéticas do Crystal Brain para inferência
function generatePhases(batchSize, kappa) {
  const phases = new Float32Array(batchSize * 768);
  const syncPhase = 0.58 * Math.PI; // Fingerprint ARKHE

  for (let b = 0; b < batchSize; b++) {
    for (let i = 0; i < 768; i++) {
      // Fases com coerência modulada por κ
      const noise = (Math.random() - 0.5) * 0.3;
      phases[b * 768 + i] = (syncPhase + noise * (2 - kappa)) % (2 * Math.PI);
    }
  }
  return phases;
}

// Executar inferência no modelo ONNX
async function runInference() {
  if (!session) { alert('Carregue um modelo primeiro'); return; }

  const batchSize = parseInt(document.getElementById('batchSize').value);
  const kappa = parseFloat(document.getElementById('kappa').value);
  document.getElementById('kappaValue').textContent = kappa.toFixed(2);

  const startTime = performance.now();

  // Preparar tensor de entrada
  const phases = generatePhases(batchSize, kappa);
  const inputTensor = new ort.Tensor('float32', phases, [batchSize, 768]);

  try {
    // Executar inferência
    const outputs = await session.run({ phases: inputTensor });

    const latency = performance.now() - startTime;
    document.getElementById('latencyMetric').textContent = latency.toFixed(1);

    // Extrair resultados
    const reconstructed = outputs.reconstructed.data;
    const latentCode = outputs.latent_code.data;

    // Calcular métricas
    const captureFraction = computeCaptureFraction(latentCode, batchSize);
    const coherence = computeCoherence(reconstructed, batchSize);

    document.getElementById('captureMetric').textContent = `${(captureFraction * 100).toFixed(1)}%`;
    document.getElementById('coherenceMetric').textContent = coherence.toFixed(3);

    // Atualizar visualização do manifold (projeção 2D via PCA simplificada)
    updateManifoldChart(latentCode, batchSize);

    // Mostrar código latente sparse (primeiros 64 valores)
    const sparsePreview = Array.from(latentCode.slice(0, 64))
      .map(v => v > 0.01 ? v.toFixed(3) : '0')
      .join(' ');
    document.getElementById('latentCode').textContent = sparsePreview + ' ...';

  } catch (err) {
    console.error('Erro na inferência:', err);
    alert(`Erro: ${err.message}`);
  }
}

// Calcular fração CAPTURE a partir do código latente
function computeCaptureFraction(latentCode, batchSize) {
  let active = 0;
  const threshold = 0.01;
  for (let i = 0; i < latentCode.length; i++) {
    if (latentCode[i] > threshold) active++;
  }
  return active / (batchSize * 768);
}

// Calcular parâmetro de ordem de coerência
function computeCoherence(reconstructed, batchSize) {
  let sumRe = 0, sumIm = 0;
  for (let i = 0; i < reconstructed.length; i++) {
    const phase = reconstructed[i];
    sumRe += Math.cos(phase);
    sumIm += Math.sin(phase);
  }
  return Math.sqrt(sumRe**2 + sumIm**2) / reconstructed.length;
}

// Atualizar gráfico do manifold com projeção 2D simplificada
function updateManifoldChart(latentCode, batchSize) {
  const points = [];
  const step = Math.max(1, Math.floor(768 / 2)); // Amostrar dimensões

  for (let b = 0; b < Math.min(batchSize, 100); b++) {
    // Projeção simples: média ponderada de dimensões
    let x = 0, y = 0;
    for (let d = 0; d < 768; d += step) {
      const idx = b * 768 + d;
      x += latentCode[idx] * Math.cos(d * 0.1);
      y += latentCode[idx] * Math.sin(d * 0.1);
    }
    x /= (768 / step); y /= (768 / step);
    points.push({ x, y });
  }

  manifoldChart.data.datasets[0].data = points;
  manifoldChart.update('none'); // Atualização suave
}

// Atualizar slider de κ
document.getElementById('kappa').addEventListener('input', (e) => {
  document.getElementById('kappaValue').textContent = parseFloat(e.target.value).toFixed(2);
});

// Inicializar ao carregar página
window.addEventListener('load', () => {
  initChart();
  console.log('🔮 ARKHE Dashboard initialized');
});
