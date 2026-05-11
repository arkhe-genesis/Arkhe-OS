// arkhe_os/dashboard/webgpu/main.ts
import { CoherenceGraphRenderer } from './coherence_graph_renderer';
import { InteractiveViewport } from './interactive_viewport';
import { initializeFallbackDashboard } from './fallback_canvas';
import { VisualizationExporter } from './export';
import { FuzzingResultStream, FuzzingFinding } from './fuzzing';

// Stubs for undeclared types
export interface CoherenceDashboard {
    renderer?: CoherenceGraphRenderer;
    viewport?: InteractiveViewport;
    dataBridge?: any;
    exporter?: VisualizationExporter;
    updateData?: (nodes: any[], edges: any[]) => void;
}

class CoherenceDataBridge {
    constructor(config: any) {}
    on(event: string, callback: (data: any) => void) {}
}

function showNodeDetails(nodeId: string) {}
function navigateToDomain(domain: string, nodeId: string) {}

export async function initializeDashboard(): Promise<CoherenceDashboard> {
  // 1. Solicitar adaptador e dispositivo WebGPU
  if (!navigator.gpu) {
    console.warn('WebGPU não suportado; fallback para Canvas 2D');
    return initializeFallbackDashboard();
  }

  const adapter = await navigator.gpu.requestAdapter({
    powerPreference: 'high-performance',
  });

  if (!adapter) {
    throw new Error('Falha ao obter adaptador WebGPU');
  }

  const device = await adapter.requestDevice({
    requiredFeatures: ['timestamp-query', 'shader-f16' as GPUFeatureName],
  });

  // 2. Configurar canvas e context
  const canvas = document.getElementById('coherence-canvas') as HTMLCanvasElement;
  const context = canvas.getContext('webgpu') as unknown as GPUCanvasContext;

  const presentationFormat = navigator.gpu.getPreferredCanvasFormat();
  context.configure({
    device,
    format: presentationFormat,
    alphaMode: 'premultiplied',
  });

  // 3. Inicializar componentes
  const renderer = new CoherenceGraphRenderer(device, {
    maxNodes: 10000,
    maxEdges: 50000,
    forceRepel: 5000,
    forceAttract: 0.01,
    coherenceFieldStrength: 2.0,
    colorScheme: 'cielab',
    animationFPS: 60,
  });

  const viewport = new InteractiveViewport(canvas, renderer, {
    onSelect: (nodeId) => showNodeDetails(nodeId),
    onDrillDown: (nodeId, domain) => navigateToDomain(domain, nodeId),
  });

  // 4. Conectar a streams de dados
  const dataBridge = new CoherenceDataBridge({
    coherenceChannel: 'ws://localhost:8080/coherence',
    fuzzingChannel: 'ws://localhost:8080/fuzzing',
    auditChannel: 'ws://localhost:8080/audit',
  });

  dataBridge.on('update', (data: any) => renderer.updateData(data.nodes, data.edges));

  const exporter = new VisualizationExporter();

  const fuzzingStream = new FuzzingResultStream();
  fuzzingStream.on('high_value_finding', (finding: FuzzingFinding) => {
    // spawn insight crystal mock
    console.log('Spawning insight crystal for finding:', finding.id);
  });

  // 5. Loop de renderização
  let lastTime = 0;
  function renderLoop(timestamp: number) {
    const deltaTime = (timestamp - lastTime) / 1000;
    lastTime = timestamp;

    viewport.update(deltaTime);

    const commandEncoder = device.createCommandEncoder();
    const textureView = context.getCurrentTexture().createView();

    renderer.render(commandEncoder, textureView);

    device.queue.submit([commandEncoder.finish()]);

    requestAnimationFrame(renderLoop);
  }

  requestAnimationFrame(renderLoop);

  return { renderer, viewport, dataBridge, exporter };
}
