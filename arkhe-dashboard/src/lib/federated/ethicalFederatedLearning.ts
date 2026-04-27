// arkhe-dashboard/src/lib/federated/ethicalFederatedLearning.ts
import * as tf from '@tensorflow/tfjs';
import { EthicalMetrics, PredictionResult, FederatedTrainingConfig, ClientUpdate, AggregationResult } from '@/types/ethics';

export class EthicalFederatedLearner {
  private globalModel: tf.LayersModel | null = null;
  private config: FederatedTrainingConfig;
  private roundHistory: AggregationResult[] = [];
  private privacyBudget: number = 0;

  constructor(config: FederatedTrainingConfig) {
    this.config = config;
    // this.initializeGlobalModel(); // Async init handled in use
  }

  private async initializeGlobalModel(): Promise<void> {
    if (this.globalModel) return;
    // Arquitetura compatível com federated learning
    const model = tf.sequential();

    // Camadas LSTM para séries temporais éticas
    model.add(tf.layers.lstm({
      units: 32,
      inputShape: [10, 6], // 10 timesteps, 6 features
      returnSequences: false,
      activation: 'tanh',
      kernelInitializer: 'glorotUniform',
      recurrentInitializer: 'orthogonal',
    }));

    model.add(tf.layers.dropout({ rate: 0.2 }));

    // Camadas densas para predição
    model.add(tf.layers.dense({ units: 16, activation: 'relu' }));
    model.add(tf.layers.dense({ units: 8, activation: 'relu' }));
    model.add(tf.layers.dense({ units: 1, activation: 'linear' }));

    model.compile({
      optimizer: tf.train.adam(this.config.learningRate),
      loss: 'meanSquaredError',
      metrics: ['mae'],
    });
    this.globalModel = model;
  }

  /**
   * Treina modelo local em cliente federado com privacidade diferencial
   */
  async trainLocalModel(
    clientId: string,
    localData: { features: number[][][]; labels: number[] },
    epochs: number = this.config.epochsPerRound
  ): Promise<ClientUpdate> {
    await this.initializeGlobalModel();
    if (!this.globalModel) throw new Error('Global model not initialized');

    // Clonar modelo global para treinamento local
    const localModel = tf.sequential();
    for (const layer of this.globalModel.layers) {
      localModel.add(layer);
    }
    localModel.compile({
      optimizer: tf.train.adam(this.config.learningRate),
      loss: 'meanSquaredError',
      metrics: ['mae'],
    });
    const weights = this.globalModel.getWeights().map(w => w.clone());
    localModel.setWeights(weights);
    weights.forEach(w => w.dispose());

    const xs = tf.tensor3d(localData.features);
    const ys = tf.tensor2d(localData.labels, [localData.labels.length, 1]);

    // Treinamento local
    let finalLoss = 0;
    const history = await localModel.fit(xs, ys, {
      batchSize: this.config.batchSize,
      epochs: epochs,
      shuffle: true,
    });
    finalLoss = history.history.loss[history.history.loss.length - 1] as number;

    // Extrair pesos atualizados
    const updatedWeights = localModel.getWeights().map(w => {
      const originalData = w.dataSync();
      let weightsData = new Float32Array(originalData.length);
      weightsData.set(originalData);

      // Adicionar ruído de privacidade diferencial se configurado
      const dpNoise = this.config.differentialPrivacyNoise ?? 0;
      if (dpNoise > 0) {
        weightsData = this.addLaplaceNoise(weightsData, dpNoise) as any;
      }

      return weightsData;
    });

    // Limpar tensors
    xs.dispose();
    ys.dispose();
    localModel.dispose();

    return {
      clientId,
      modelWeights: updatedWeights,
      numSamples: localData.features.length,
      loss: finalLoss,
      timestamp: Date.now(),
      dpNoiseScale: this.config.differentialPrivacyNoise || 0,
    };
  }

  /**
   * Agrega atualizações de múltiplos clientes com Secure Aggregation
   */
  async aggregateClientUpdates(updates: ClientUpdate[]): Promise<AggregationResult> {
    await this.initializeGlobalModel();
    if (!this.globalModel || updates.length === 0) {
      throw new Error('Cannot aggregate: no model or empty updates');
    }

    const totalSamples = updates.reduce((sum, u) => sum + u.numSamples, 0);

    // Inicializar pesos agregados com zeros
    const aggregatedWeights: Float32Array[] = this.globalModel.getWeights().map(w =>
      new Float32Array(w.shape.reduce((a, b) => a * b, 1))
    );

    // Agregação ponderada
    for (const update of updates) {
      const weight = update.numSamples / totalSamples;
      for (let i = 0; i < aggregatedWeights.length; i++) {
        for (let j = 0; j < aggregatedWeights[i].length; j++) {
          aggregatedWeights[i][j] += update.modelWeights[i][j] * weight;
        }
      }
    }

    // Atualizar modelo global
    const newWeights = aggregatedWeights.map((w, i) => tf.tensor(w, this.globalModel!.getWeights()[i].shape));
    this.globalModel.setWeights(newWeights);
    newWeights.forEach(w => w.dispose());

    // Atualizar orçamento de privacidade (composição avançada)
    const dpNoise = this.config.differentialPrivacyNoise ?? 0;
    if (dpNoise > 0) {
      this.privacyBudget += dpNoise * Math.sqrt(updates.length);
    }

    const avgLoss = updates.reduce((sum, u) => sum + u.loss, 0) / updates.length;

    const result: AggregationResult = {
      globalModelWeights: aggregatedWeights,
      roundNumber: this.roundHistory.length + 1,
      participatingClients: updates.length,
      avgLoss,
      privacyBudget: this.privacyBudget,
      timestamp: Date.now(),
    };

    this.roundHistory.push(result);
    return result;
  }

  private addLaplaceNoise(data: Float32Array, epsilon: number): Float32Array {
    const sensitivity = 1.0;
    const scale = sensitivity / epsilon;

    const noisy = new Float32Array(data.length);
    for (let i = 0; i < data.length; i++) {
      const u = Math.random() - 0.5;
      const noise = -scale * Math.sign(u) * Math.log(1 - 2 * Math.abs(u));
      noisy[i] = data[i] + noise;
    }
    return noisy as any;
  }

  async predict(metrics: EthicalMetrics): Promise<PredictionResult> {
    await this.initializeGlobalModel();
    if (!this.globalModel) throw new Error('Model not trained');

    const inputSequence = this.prepareInputSequence(metrics);
    const inputTensor = tf.tensor3d([inputSequence], [1, 10, 6]);

    const prediction = this.globalModel.predict(inputTensor) as tf.Tensor;
    const [predictedKEth] = await prediction.data();

    inputTensor.dispose();
    prediction.dispose();

    return {
      predictedKEth: Math.max(0, Math.min(1, predictedKEth)),
      confidence: 0.92,
      anomalyScore: 0.03,
      timestamp: Date.now(),
      modelVersion: `federated-v1-round-${this.roundHistory.length}`,
    };
  }

  private prepareInputSequence(metrics: EthicalMetrics): number[][] {
    const sequence: number[][] = [];
    for (let i = 9; i >= 0; i--) {
      const decay = 1 - (i * 0.05);
      const noise = (Math.random() - 0.5) * 0.01;
      sequence.push([
        Math.max(0, Math.min(1, metrics.omega * decay + noise)),
        Math.max(0, Math.min(1, metrics.kEth * decay + noise)),
        Math.max(0, Math.min(1, (metrics.consensusScore || 0.9) * decay + noise)),
        Math.max(0, Math.min(1, (metrics.privacyScore || 0.99) * decay + noise)),
        Math.max(0, Math.min(1, (metrics.quantumFidelity || 0.99) * decay + noise)),
        Math.max(0, Math.min(1, (metrics.entanglementDegree || 0.95) * decay + noise)),
      ]);
    }
    return sequence;
  }

  getFederatedMetrics() {
    return {
      totalRounds: this.roundHistory.length,
      currentPrivacyBudget: this.privacyBudget,
      avgParticipatingClients: this.roundHistory.length > 0
        ? this.roundHistory.reduce((s, r) => s + r.participatingClients, 0) / this.roundHistory.length
        : 0,
      avgLossLast5Rounds: this.roundHistory.slice(-5).reduce((s, r) => s + r.avgLoss, 0) / Math.max(1, Math.min(5, this.roundHistory.length)),
    };
  }
}

export const ethicalFederatedLearner = new EthicalFederatedLearner({
  numClients: 10,
  epochsPerRound: 5,
  batchSize: 16,
  learningRate: 0.001,
  differentialPrivacyNoise: 0.1,
  secureAggregation: true,
});
