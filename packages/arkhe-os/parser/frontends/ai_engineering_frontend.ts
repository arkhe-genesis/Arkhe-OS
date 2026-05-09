// arkhe-os/parser/frontends/ai_engineering_frontend.ts
import { LFIRGraph, LFIRNode, LFIRNodeType, LFIREdge, ParseResult, ParseMetrics } from '../lfir';
import { parse as parsePyTorch } from './parsers/pytorch_parser';
import { parse as parseTensorFlow } from './parsers/tensorflow_parser';
import { parse as parseONNX } from './parsers/onnx_parser';
import { parse as parseTrainingLog } from './parsers/training_log_parser';
import { parse as parseConfig } from './parsers/config_parser';
import { parse as parseDatasetSchema } from './parsers/dataset_parser';

export interface AIEngineeringParserConfig {
  enableCoherenceMapping: boolean;
  enableEnergyEstimation: boolean;
  enableBiasDetection: boolean;
  maxModelSizeMB: number;
  supportedFrameworks: string[];
}

export class AIEngineeringFrontend {
  private config: AIEngineeringParserConfig;

  constructor(config: Partial<AIEngineeringParserConfig> = {}) {
    this.config = {
      enableCoherenceMapping: true,
      enableEnergyEstimation: true,
      enableBiasDetection: true,
      maxModelSizeMB: 1024,
      supportedFrameworks: ['pytorch', 'tensorflow', 'onnx', 'jax', 'sklearn'],
      ...config
    };
  }

  getLanguage(): string { return 'ai-engineering'; }

  getExtensions(): string[] {
    return [
      '.pt', '.pth', '.bin',      // PyTorch
      '.h5', '.keras', '.pb',     // TensorFlow/Keras
      '.onnx',                    // ONNX
      '.json', '.yaml', '.yml',   // Configs
      '.log', '.txt',             // Training logs
      '.parquet', '.csv', '.tfrecord' // Datasets
    ];
  }

  async parse(source: Buffer | string, filename: string, metadata?: Record<string, unknown>): Promise<ParseResult> {
    const graph = new LFIRGraph();
    const startTime = Date.now();
    const errors: Array<{code: string; message: string; severity: 'error'|'fatal'}> = [];
    const warnings: Array<{code: string; message: string; suggestion: string}> = [];

    try {
      const ext = filename.split('.').pop()?.toLowerCase();
      const rootId = `ai_artifact/${filename.replace(/\W+/g, '_')}`;

      const rootNode = new LFIRNode(rootId, LFIRNodeType.Module, 'ai-engineering');
      rootNode.attributes['filename'] = filename;
      rootNode.attributes['parsed_at'] = new Date().toISOString();
      if (metadata) {
        for (const [k, v] of Object.entries(metadata)) {
          rootNode.attributes[k] = v;
        }
      }
      graph.addNode(rootNode);
      graph.rootNodes.push(rootNode.id);

      switch (ext) {
        case 'pt':
        case 'pth':
        case 'bin':
          await parsePyTorch(source as Buffer, graph, rootNode.id, this.config);
          break;
        case 'h5':
        case 'keras':
        case 'pb':
          await parseTensorFlow(source as Buffer, graph, rootNode.id, this.config);
          break;
        case 'onnx':
          await parseONNX(source as Buffer, graph, rootNode.id, this.config);
          break;
        case 'yaml':
        case 'yml':
        case 'json':
          await parseConfig(source as string, graph, rootNode.id, this.config);
          break;
        case 'log':
        case 'txt':
          await parseTrainingLog(source as string, graph, rootNode.id, this.config);
          break;
        case 'parquet':
        case 'csv':
        case 'tfrecord':
          await parseDatasetSchema(source as Buffer | string, graph, rootNode.id, this.config);
          break;
        default:
          warnings.push({
            code: 'UNSUPPORTED_EXTENSION',
            message: `Extension .${ext} not fully supported`,
            suggestion: 'Try converting to ONNX or providing metadata via config'
          });
          // Attempt generic parsing
          this.parseGenericArtifact(source, graph, rootNode.id);
      }

      // Calcular coerência se habilitado
      if (this.config.enableCoherenceMapping) {
        const coherence = this.computeAICoherence(graph);
        rootNode.attributes['coherence_score'] = coherence.score;
        rootNode.attributes['coherence_components'] = coherence.components;
      }

      const parseTime = Date.now() - startTime;
      const metrics: ParseMetrics = {
        parseTimeMs: parseTime,
        nodesCreated: graph.nodes.length,
        edgesCreated: graph.edges.length,
        maxDepth: this.computeMaxDepth(graph),
        coherenceScore: rootNode.attributes['coherence_score'] as number || 0
      };

      return {
        success: errors.filter(e => e.severity === 'fatal').length === 0,
        graph,
        errors,
        warnings,
        metrics
      };

    } catch (err) {
      errors.push({
        code: 'PARSE_EXCEPTION',
        message: err instanceof Error ? err.message : 'Unknown error',
        severity: 'fatal'
      });
      return {
        success: false,
        graph: null,
        errors,
        warnings,
        metrics: {
          parseTimeMs: Date.now() - startTime,
          nodesCreated: 0,
          edgesCreated: 0,
          maxDepth: 0,
          coherenceScore: 0
        }
      };
    }
  }

  private computeAICoherence(graph: LFIRGraph): { score: number; components: Record<string, number> } {
    // Heurística simplificada de coerência para artefatos de AI
    const components: Record<string, number> = {};

    // Performance: baseado em métricas de validação se disponíveis
    const valAcc = this.extractMetric(graph, 'validation_accuracy');
    const aucRoc = this.extractMetric(graph, 'auc_roc');
    components.performance = valAcc || aucRoc || 0.5;

    // Complexidade: baseado em número de parâmetros e camadas
    const paramCount = this.extractParamCount(graph);
    const layerCount = this.extractLayerCount(graph);
    components.complexity = Math.min(1.0, Math.log1p(paramCount) / 20 + layerCount / 100);

    // Equidade: baseado em métricas de viés se disponíveis
    const biasScore = this.extractMetric(graph, 'bias_score', 0); // 0 = sem viés
    components.equity = 1.0 - Math.abs(biasScore);

    // Eficiência: baseado em latência estimada ou FLOPS
    const flops = this.extractMetric(graph, 'flops', 1e9);
    components.efficiency = Math.max(0, 1.0 - Math.log10(flops) / 12);

    // Robustez: baseado em métricas de adversarial testing se disponíveis
    const robustness = this.extractMetric(graph, 'robustness_score', 0.5);
    components.robustness = robustness;

    // Combinação ponderada (pesos configuráveis)
    const weights = { performance: 0.35, complexity: -0.2, equity: 0.15, efficiency: 0.15, robustness: 0.15 };
    let score = 0;
    for (const [key, weight] of Object.entries(weights)) {
      score += weight * (components[key] || 0);
    }

    return {
      score: Math.max(0, Math.min(1, score + 0.5)), // Normalizar para [0, 1]
      components
    };
  }

  private extractMetric(graph: LFIRGraph, metricName: string, defaultValue: number = 0): number {
    for (const node of graph.nodes) {
      if (node.attributes[metricName] !== undefined) {
        const val = node.attributes[metricName];
        return typeof val === 'number' ? val : defaultValue;
      }
    }
    return defaultValue;
  }

  private extractParamCount(graph: LFIRGraph): number {
    let total = 0;
    for (const node of graph.nodes) {
      if (node.attributes['param_count'] !== undefined) {
        total += node.attributes['param_count'] as number;
      }
    }
    return total;
  }

  private extractLayerCount(graph: LFIRGraph): number {
    return graph.nodes.filter(n => n.attributes['layer_type'] !== undefined).length;
  }

  private computeMaxDepth(graph: LFIRGraph): number {
    // BFS para calcular profundidade máxima
    const visited = new Set<string>();
    const queue: Array<{id: string; depth: number}> = graph.rootNodes.map(id => ({id, depth: 0}));
    let maxDepth = 0;

    while (queue.length > 0) {
      const {id, depth} = queue.shift()!;
      if (visited.has(id)) continue;
      visited.add(id);
      maxDepth = Math.max(maxDepth, depth);

      const children = graph.edges.filter(e => e.from === id).map(e => e.to);
      for (const child of children) {
        if (!visited.has(child)) {
          queue.push({id: child, depth: depth + 1});
        }
      }
    }
    return maxDepth;
  }

  private parseGenericArtifact(source: Buffer | string, graph: LFIRGraph, parentId: string) {
    // Fallback: criar nó genérico com metadados
    const node = new LFIRNode(`generic/${Date.now()}`, LFIRNodeType.Metadata, 'ai-engineering');
    node.attributes['raw_size'] = typeof source === 'string' ? source.length : source.length;
    node.attributes['content_preview'] = typeof source === 'string'
      ? source.slice(0, 200)
      : source.toString('utf8').slice(0, 200);
    graph.addNode(node);
    graph.link(parentId, node.id);
  }
}
