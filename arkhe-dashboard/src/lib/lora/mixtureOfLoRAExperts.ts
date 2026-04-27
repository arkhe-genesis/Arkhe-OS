// arkhe-dashboard/src/lib/lora/mixtureOfLoRAExperts.ts
import * as tf from '@tensorflow/tfjs';

export interface LoRAExpert {
  name: string;
  A: tf.Tensor2D;
  B: tf.Tensor2D;
}

export class MixtureOfLoRAExperts {
  private experts: LoRAExpert[] = [];
  private gatingModel: tf.Sequential;

  constructor() {
    this.gatingModel = tf.sequential({
      layers: [
        tf.layers.dense({ units: 16, activation: 'relu', inputShape: [32] }),
        tf.layers.dense({ units: 8, activation: 'softmax' }),
      ]
    });
  }

  async combineLayers(contextVector: tf.Tensor1D) {
    if (this.experts.length === 0) return { deltaWeight: tf.zeros([768, 768]) };

    return tf.tidy(() => {
      let delta = tf.zeros([768, 768]);
      this.experts.forEach((expert) => {
        delta = delta.add(expert.B.matMul(expert.A));
      });
      return { deltaWeight: delta as tf.Tensor2D };
    });
  }
}
