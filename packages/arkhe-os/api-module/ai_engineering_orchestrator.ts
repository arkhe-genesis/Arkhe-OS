import { AIEngineeringFrontend, AIEngineeringParserConfig, LFIRGraph } from './ai_engineering_frontend';
import { AICoherenceMapper, AICoherenceMapperConfig, CoherenceGradientChannel } from './ai_coherence_mapper';

export interface AIEngineeringOrchestratorConfig {
  scanIntervalSec: number;
  enableCoherenceMapping: boolean;
  enableAutoML: boolean;
  coherenceThreshold: number;
  parserConfig: Partial<AIEngineeringParserConfig>;
  mapperConfig: Partial<AICoherenceMapperConfig>;
}

export interface IntegrationEvent {
  eventType: string;
  artifactPath: string;
  data: Record<string, unknown>;
  timestamp: Date;
}

export class AutoMLEvolutionAdapter {
    constructor(public id: string, public channel: CoherenceGradientChannel) {}

    async suggestArchitectureEvolution(graph: LFIRGraph) {
        // mock logic
    }

    getMetrics() {
        return { suggestions: 0 };
    }
}

export class AIEngineeringOrchestrator {
  private parser: AIEngineeringFrontend;
  private coherenceMapper: AICoherenceMapper | null = null;
  private autoMLAdapter: AutoMLEvolutionAdapter | null = null;
  private config: AIEngineeringOrchestratorConfig;
  private processedArtifacts = new Set<string>();
  private callbacks: Array<(event: IntegrationEvent) => void> = [];
  private lastScanTime: Date | null = null;

  constructor(
    private artifactRoot: string,
    config: Partial<AIEngineeringOrchestratorConfig>,
    gradientChannel: CoherenceGradientChannel
  ) {
    this.config = {
      scanIntervalSec: 300,
      enableCoherenceMapping: true,
      enableAutoML: true,
      coherenceThreshold: 0.70,
      parserConfig: {},
      mapperConfig: {},
      ...config
    };

    this.parser = new AIEngineeringFrontend(this.config.parserConfig);

    if (this.config.enableCoherenceMapping) {
      this.coherenceMapper = new AICoherenceMapper(
        this.config.mapperConfig,
        gradientChannel
      );
    }

    if (this.config.enableAutoML) {
      this.autoMLAdapter = new AutoMLEvolutionAdapter(
        'auto_ml_adapter_001',
        gradientChannel
      );
    }
  }

  async scanArtifact(artifactPath: string): Promise<void> {
    if (this.processedArtifacts.has(artifactPath)) {
      return;
    }

    // Ler arquivo
    const source = await this.readFile(artifactPath);
    const filename = artifactPath.split('/').pop() || 'unknown';

    // Parse para LFIR
    const result = await this.parser.parse(source, filename, {
      artifact_path: artifactPath,
      scanned_at: new Date().toISOString()
    });

    if (!result.success) {
      console.warn(`⚠️ Failed to parse ${artifactPath}:`, result.errors);
      return;
    }

    // Mapear para coerência se habilitado
    if (this.coherenceMapper && result.graph) {
      await this.coherenceMapper.processLFIRGraph(result.graph);
    }

    // Auto-ML evolution se habilitado e coerência alta
    if (this.autoMLAdapter && result.graph) {
      const coherence = result.graph.rootNodes
        .map(id => result.graph?.nodes.find(n => n.id === id)?.attributes['coherence_score'])
        .filter((c): c is number => typeof c === 'number');

      if (coherence.some(c => c >= this.config.coherenceThreshold)) {
        await this.autoMLAdapter.suggestArchitectureEvolution(result.graph);
      }
    }

    // Registrar como processado
    this.processedArtifacts.add(artifactPath);
    this.lastScanTime = new Date();

    // Notificar callbacks
    for (const cb of this.callbacks) {
      cb({
        eventType: 'artifact_processed',
        artifactPath,
        data: {
          nodes_created: result.graph?.nodes.length,
          coherence: result.graph?.rootNodes
            .map(id => result.graph?.nodes.find(n => n.id === id)?.attributes['coherence_score'])
            .filter((c): c is number => typeof c === 'number')[0]
        },
        timestamp: new Date()
      });
    }
  }

  registerCallback(cb: (event: IntegrationEvent) => void): void {
    this.callbacks.push(cb);
  }

  getMetrics() {
    return {
      artifactsProcessed: this.processedArtifacts.size,
      lastScanTime: this.lastScanTime,
      mapperMetrics: this.coherenceMapper?.getMetrics(),
      autoMLMetrics: this.autoMLAdapter?.getMetrics()
    };
  }

  private async readFile(path: string): Promise<Buffer | string> {
    return "mocked buffer content";
  }
}
