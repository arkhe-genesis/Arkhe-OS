import { LFIRGraph, LFIRNode } from './ai_engineering_frontend';

export interface CoherenceGradientChannel {
  submitLocalGradient(
    vector: number[],
    coherence: number,
    distance: number,
    samples: number,
    loss: number,
    metadata: Record<string, unknown>
  ): Promise<void>;
}

export interface AICoherenceMapperConfig {
  enableAutoSubmission: boolean;
  performanceWeight: number;
  complexityPenalty: number;
  equityWeight: number;
  efficiencyWeight: number;
  minCoherenceDelta: number;
  enableEnergyEstimation: boolean;
  baselineEnergyPerInference: number; // Joules
}

export interface MapperMetrics {
  artifactsProcessed: number;
  gradientsSubmitted: number;
  avgCoherenceDelta: number;
  modelsMapped: number;
  trainingsMapped: number;
  configsMapped: number;
  datasetsMapped: number;
}

export class AICoherenceMapper {
  private config: AICoherenceMapperConfig;
  private processedArtifacts = new Map<string, boolean>();
  private gradientChannel: CoherenceGradientChannel;
  private metrics: MapperMetrics = {
    artifactsProcessed: 0,
    gradientsSubmitted: 0,
    avgCoherenceDelta: 0,
    modelsMapped: 0,
    trainingsMapped: 0,
    configsMapped: 0,
    datasetsMapped: 0
  };

  constructor(config: Partial<AICoherenceMapperConfig>, gradientChannel: CoherenceGradientChannel) {
    this.config = {
      enableAutoSubmission: true,
      performanceWeight: 0.35,
      complexityPenalty: 0.2,
      equityWeight: 0.15,
      efficiencyWeight: 0.15,
      minCoherenceDelta: 0.01,
      enableEnergyEstimation: true,
      baselineEnergyPerInference: 0.001, // 1 mJ baseline
      ...config
    };
    this.gradientChannel = gradientChannel;
  }

  async processLFIRGraph(graph: LFIRGraph): Promise<void> {
    let submitted = 0;

    for (const node of graph.nodes) {
      const artifactType = node.attributes['artifact_type'] as string;
      const artifactId = node.id;

      if (!artifactType || this.processedArtifacts.has(artifactId)) {
        continue;
      }

      let gradient: number;
      let metadata: Record<string, unknown>;

      switch (artifactType) {
        case 'model':
          [gradient, metadata] = this.computeModelGradient(node);
          this.metrics.modelsMapped++;
          break;
        case 'training_run':
          [gradient, metadata] = this.computeTrainingGradient(node);
          this.metrics.trainingsMapped++;
          break;
        case 'config':
          [gradient, metadata] = this.computeConfigGradient(node);
          this.metrics.configsMapped++;
          break;
        case 'dataset':
          [gradient, metadata] = this.computeDatasetGradient(node);
          this.metrics.datasetsMapped++;
          break;
        case 'serving_endpoint':
          [gradient, metadata] = this.computeServingGradient(node);
          break;
        default:
          continue;
      }

      // Submeter se habilitado e delta significativo
      if (this.config.enableAutoSubmission && Math.abs(gradient) >= this.config.minCoherenceDelta) {
        await this.submitGradient(artifactId, gradient, metadata);
        submitted++;
        this.metrics.gradientsSubmitted++;
      }

      // Atualizar métricas
      this.metrics.artifactsProcessed++;
      this.metrics.avgCoherenceDelta =
        this.metrics.avgCoherenceDelta * 0.99 + Math.abs(gradient) * 0.01;

      this.processedArtifacts.set(artifactId, true);
    }
  }

  private computeModelGradient(node: LFIRNode): [number, Record<string, unknown>] {
    let gradient = 0;
    const metadata: Record<string, unknown> = {
      artifact_type: 'model',
      framework: node.attributes['framework'],
      param_count: node.attributes['param_count']
    };

    // Performance como fator principal
    const valAcc = node.attributes['validation_accuracy'] as number;
    if (valAcc !== undefined) {
      gradient += this.config.performanceWeight * valAcc;
    }

    // Penalidade por complexidade excessiva
    const paramCount = node.attributes['param_count'] as number;
    if (paramCount !== undefined) {
      const complexityPenalty = Math.log1p(paramCount) / 20;
      gradient -= this.config.complexityPenalty * complexityPenalty;
    }

    // Bonus por eficiência energética se habilitado
    if (this.config.enableEnergyEstimation) {
      const energyPerInf = node.attributes['energy_per_inference'] as number;
      if (energyPerInf !== undefined) {
        const efficiency = Math.exp(-0.1 * energyPerInf / this.config.baselineEnergyPerInference);
        gradient += this.config.efficiencyWeight * efficiency;
      }
    }

    // Ajuste por equidade se métrica disponível
    const biasScore = node.attributes['bias_score'] as number;
    if (biasScore !== undefined) {
      gradient += this.config.equityWeight * (1 - Math.abs(biasScore));
    }

    metadata['coherence_delta'] = gradient;
    return [gradient, metadata];
  }

  private computeTrainingGradient(node: LFIRNode): [number, Record<string, unknown>] {
    let gradient = 0;
    const metadata: Record<string, unknown> = {
      artifact_type: 'training_run',
      epochs: node.attributes['epochs']
    };

    // Ganho de validação como sinal de aprendizado coerente
    const valAccStart = node.attributes['val_acc_start'] as number;
    const valAccEnd = node.attributes['val_acc_end'] as number;
    if (valAccStart !== undefined && valAccEnd !== undefined) {
      const gain = valAccEnd - valAccStart;
      gradient += 0.05 * gain; // Bonus por aprendizado
    }

    // Penalidade por overfitting (gap treino/validação)
    const trainAcc = node.attributes['train_acc_final'] as number;
    const valAcc = node.attributes['val_acc_final'] as number;
    if (trainAcc !== undefined && valAcc !== undefined) {
      const gap = trainAcc - valAcc;
      if (gap > 0.1) {
        gradient -= 0.03; // Overfitting detectado
      }
    }

    // Bonus por convergência estável
    const lossCurve = node.attributes['loss_curve'] as number[];
    if (lossCurve && lossCurve.length > 10) {
      const recent = lossCurve.slice(-10);
      const variance = recent.reduce((a, b) => a + Math.pow(b - recent.reduce((s, v) => s + v, 0) / 10, 2), 0) / 10;
      if (variance < 0.01) {
        gradient += 0.02; // Convergência estável
      }
    }

    metadata['coherence_delta'] = gradient;
    return [gradient, metadata];
  }

  private computeConfigGradient(node: LFIRNode): [number, Record<string, unknown>] {
    let gradient = 0;
    const metadata: Record<string, unknown> = {
      artifact_type: 'config'
    };

    // Configurações eficientes contribuem positivamente
    const batchSize = node.attributes['batch_size'] as number;
    const learningRate = node.attributes['learning_rate'] as number;

    // Batch size muito pequeno = ineficiente
    if (batchSize !== undefined && batchSize < 16) {
      gradient -= 0.01;
    }
    // Learning rate muito alto = instável
    if (learningRate !== undefined && learningRate > 0.1) {
      gradient -= 0.02;
    }

    // Bonus por uso de otimizador moderno
    const optimizer = node.attributes['optimizer'] as string;
    if (optimizer && ['adamw', 'adam', 'lion'].includes(optimizer.toLowerCase())) {
      gradient += 0.01;
    }

    metadata['coherence_delta'] = gradient;
    return [gradient, metadata];
  }

  private computeDatasetGradient(node: LFIRNode): [number, Record<string, unknown>] {
    let gradient = 0;
    const metadata: Record<string, unknown> = {
      artifact_type: 'dataset'
    };

    // Balanceamento de classes
    const classBalance = node.attributes['class_balance_score'] as number;
    if (classBalance !== undefined) {
      gradient += 0.03 * classBalance; // 1.0 = perfeitamente balanceado
    }

    // Qualidade dos dados
    const missingRatio = node.attributes['missing_value_ratio'] as number;
    if (missingRatio !== undefined) {
      gradient -= 0.02 * missingRatio; // Penalidade por dados faltantes
    }

    // Representatividade demográfica
    const demographicCoverage = node.attributes['demographic_coverage'] as number;
    if (demographicCoverage !== undefined) {
      gradient += 0.02 * demographicCoverage;
    }

    metadata['coherence_delta'] = gradient;
    return [gradient, metadata];
  }

  private computeServingGradient(node: LFIRNode): [number, Record<string, unknown>] {
    let gradient = 0;
    const metadata: Record<string, unknown> = {
      artifact_type: 'serving_endpoint'
    };

    // Latência baixa = positivo
    const latencyP99 = node.attributes['latency_p99_ms'] as number;
    if (latencyP99 !== undefined) {
      gradient += 0.01 * Math.max(0, 1 - latencyP99 / 1000); // <1s = bom
    }

    // Throughput alto = positivo
    const throughput = node.attributes['throughput_qps'] as number;
    if (throughput !== undefined) {
      gradient += 0.005 * Math.min(1, throughput / 1000);
    }

    // Acurácia em produção
    const prodAcc = node.attributes['production_accuracy'] as number;
    if (prodAcc !== undefined) {
      gradient += 0.03 * prodAcc;
    }

    metadata['coherence_delta'] = gradient;
    return [gradient, metadata];
  }

  private async submitGradient(artifactId: string, coherenceDelta: number, metadata: Record<string, unknown>): Promise<void> {
    const gradientMetadata = {
      source: 'ai_engineering_layer',
      artifact_id: artifactId,
      timestamp: Date.now(),
      coherence_sign: coherenceDelta >= 0 ? 'positive' : 'negative',
      ...metadata
    };

    const gradientVector = [coherenceDelta];
    const coherenceValue = 0.7 + 0.3 * Math.abs(coherenceDelta);

    await this.gradientChannel.submitLocalGradient(
      gradientVector,
      coherenceValue,
      0.5, // distância conceitual
      1,   // sample count
      0.0, // loss
      gradientMetadata
    );
  }

  getMetrics(): MapperMetrics {
    return { ...this.metrics };
  }
}
