import * as tf from '@tensorflow/tfjs';
import { EthicalMetrics, PredictionResult } from '@/types/ethics';

export class EthicalPredictiveModel {
  private model: tf.LayersModel | null = null;
  private isTraining = false;
  private trainingHistory: Array<{ epoch: number; loss: number; valLoss: number }> = [];

  constructor() {
    // Initialization moved to async method
  }

  public async initializeModel(): Promise<void> {
    if (this.model) return;
    // Arquitetura: LSTM + Dense para séries temporais de métricas éticas
    const model = tf.sequential();

    // Camada LSTM para capturar dependências temporais
    model.add(tf.layers.lstm({
      units: 64,
      inputShape: [10, 5], // 10 timesteps, 5 features
      returnSequences: true,
      activation: 'tanh',
      recurrentActivation: 'sigmoid',
      dropout: 0.2,
      recurrentDropout: 0.2,
    }));

    // Segunda LSTM para processamento profundo
    model.add(tf.layers.lstm({
      units: 32,
      returnSequences: false,
      dropout: 0.2,
    }));

    // Camadas densas para predição
    model.add(tf.layers.dense({ units: 16, activation: 'relu' }));
    model.add(tf.layers.dropout({ rate: 0.3 }));
    model.add(tf.layers.dense({ units: 8, activation: 'relu' }));

    // Saída: predição de K_eth + confiança + anomalia score
    model.add(tf.layers.dense({ units: 3, activation: 'sigmoid' }));

    // Compilar com otimizador Adam e loss customizada
    model.compile({
      optimizer: tf.train.adam(0.001),
      loss: this.customEthicalLoss.bind(this),
      metrics: ['mae', 'mse'],
    });

    this.model = model;
    console.log('🧠 Modelo de ética preditiva inicializado');
  }

  // Função de loss customizada que pondera erros em regiões críticas de K_eth
  private customEthicalLoss(yTrue: tf.Tensor, yPred: tf.Tensor): tf.Tensor {
    return tf.tidy(() => {
      // K_eth está na primeira posição do vetor de saída
      const kEthTrue = yTrue.slice([0, 0], [-1, 1]);
      const kEthPred = yPred.slice([0, 0], [-1, 1]);

      // Ponderar mais erros quando K_eth está próximo do threshold crítico (0.85)
      const criticalZone = tf.less(tf.abs(kEthTrue.sub(0.85)), 0.05);
      const weights = tf.where(criticalZone, tf.scalar(2.0), tf.scalar(1.0));

      // MSE ponderado
      const mse = tf.square(kEthTrue.sub(kEthPred)).mul(weights);

      // Adicionar regularização para suavizar predições
      const smoothness = tf.square(kEthPred.slice([1, 0], [-1, 1]).sub(
        kEthPred.slice([0, 0], [-1, 1])
      )).mean();

      return mse.mean().add(smoothness.mul(0.1));
    });
  }

  async train(
    trainingData: { features: number[][][]; labels: number[][] },
    options: { epochs: number; batchSize: number; validationSplit: number }
  ): Promise<void> {
    await this.initializeModel();
    if (this.isTraining || !this.model) return;

    this.isTraining = true;
    const { epochs, batchSize, validationSplit } = options;

    const xs = tf.tensor3d(trainingData.features);
    const ys = tf.tensor2d(trainingData.labels);

    try {
      await this.model!.fit(xs, ys, {
        epochs,
        batchSize,
        validationSplit,
        callbacks: {
          onEpochEnd: async (epoch, logs) => {
            this.trainingHistory.push({
              epoch: epoch + 1,
              loss: logs?.loss || 0,
              valLoss: logs?.val_loss || 0,
            });
            console.log(`Epoch ${epoch + 1}: loss=${logs?.loss?.toFixed(4)}, val_loss=${logs?.val_loss?.toFixed(4)}`);
          },
        },
      });

      console.log('✅ Treinamento concluído');
    } finally {
      xs.dispose();
      ys.dispose();
      this.isTraining = false;
    }
  }

  async predict(metrics: EthicalMetrics): Promise<PredictionResult> {
    await this.initializeModel();
    if (!this.model) throw new Error('Model not initialized');

    // Preparar input: normalizar e formatar para sequência temporal
    const inputSequence = this.prepareInputSequence(metrics);
    const inputTensor = tf.tensor3d([inputSequence], [1, 10, 5]);

    let prediction: tf.Tensor2D | null = null;
    try {
      prediction = this.model.predict(inputTensor) as tf.Tensor2D;
      const [kEthPred, confidence, anomalyScore] = await prediction.data();

      return {
        predictedKEth: Math.max(0, Math.min(1, kEthPred)),
        confidence: Math.max(0, Math.min(1, confidence)),
        anomalyScore: Math.max(0, Math.min(1, anomalyScore)),
        timestamp: Date.now(),
        modelVersion: 'v18.0.0',
      };
    } finally {
      inputTensor.dispose();
      if (prediction) {
        prediction.dispose();
      }
    }
  }

  private prepareInputSequence(currentMetrics: EthicalMetrics): number[][] {
    const sequence: number[][] = [];

    for (let i = 9; i >= 0; i--) {
      const decay = 1 - (i * 0.05);
      const noise = (Math.random() - 0.5) * 0.02;

      sequence.push([
        Math.max(0, Math.min(1, currentMetrics.omega * decay + noise)),
        Math.max(0, Math.min(1, currentMetrics.kEth * decay + noise * 0.8)),
        Math.max(0, Math.min(1, currentMetrics.consensusScore * decay + noise * 0.6)),
        Math.max(0, Math.min(1, (currentMetrics.privacyScore || 0.99) * decay + noise * 0.4)),
        Math.max(0, Math.min(1, (currentMetrics.quantumFidelity || 0.99) * decay + noise * 0.2)),
      ]);
    }

    return sequence;
  }

  getTrainingHistory() {
    return [...this.trainingHistory];
  }

  dispose() {
    if (this.model) {
      this.model.dispose();
      this.model = null;
    }
  }
}

export const ethicalPredictiveModel = new EthicalPredictiveModel();
