/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// src/workers/inference.worker.js
// Bloco #304 — O Coração do Prisma (Worker)
// Atualizado para 1-bit WebGPU (Bonsai v2)
import {
  pipeline,
  env,
  TextStreamer,
  DynamicCache,
  InterruptableStoppingCriteria,
} from '@huggingface/transformers';

// Configuração de soberania
env.allowLocalModels = false;

const MODEL_IDS = {
  'bonsai-1.7b': 'onnx-community/Bonsai-1.7B-ONNX',
  'bonsai-4b': 'onnx-community/Bonsai-4B-ONNX',
};

class TextGenerationPipeline {
  static instances = new Map();

  static async getInstance(modelId, progress_callback = null) {
    if (!this.instances.has(modelId)) {
      this.instances.set(
        modelId,
        pipeline('text-generation', modelId, {
          device: 'webgpu',
          dtype: 'q1',
          progress_callback,
        }),
      );
    }
    return this.instances.get(modelId);
  }
}

const stopping_criteria = new InterruptableStoppingCriteria();
let past_key_values_cache = null;
let current_model_id = null;

function disposePastKeyValues() {
  past_key_values_cache?.dispose?.();
  past_key_values_cache = null;
}

self.onmessage = async (e) => {
  const { type, data } = e.data;

  switch (type) {
    case 'load': {
      try {
        if (current_model_id && current_model_id !== data) {
          disposePastKeyValues();
        }
        current_model_id = data;

        self.postMessage({ status: 'loading', phase: 'checking_vault' });

        const modelRepo = MODEL_IDS[data] || data;
        const generator = await TextGenerationPipeline.getInstance(
          modelRepo,
          (info) => {
            if (info.status === 'progress' || info.status === 'progress_total') {
               self.postMessage({
                status: 'ritual_progress',
                progress: Number(info.progress ?? 0),
                loaded: Number(info.loaded ?? 0),
                total: Number(info.total ?? 0)
              });
            }
          }
        );

        self.postMessage({ status: 'loading', phase: 'instantiating' });

        // Warm-up: Otimização do modelo para execução 1-bit no WebGPU
        const inputs = generator.tokenizer('a');
        await generator.model.generate({ ...inputs, max_new_tokens: 1 });

        self.postMessage({ status: 'ready', model: data });
      } catch (err) {
        console.error('[λPU] Falha de inicialização:', err);
        self.postMessage({ status: 'error', error: err.message });
      }
      break;
    }

    case 'generate': {
      if (!current_model_id) {
        self.postMessage({ status: 'error', error: 'Oráculo não inicializado' });
        return;
      }

      try {
        const modelRepo = MODEL_IDS[current_model_id] || current_model_id;
        const generator = await TextGenerationPipeline.getInstance(modelRepo);

        let startTime = performance.now();
        let numTokens = 0;
        let tps = 0;

        const streamer = new TextStreamer(generator.tokenizer, {
          skip_prompt: true,
          skip_special_tokens: true,
          callback_function: (token) => {
            self.postMessage({
              status: 'token',
              token,
              tps,
              numTokens
            });
          },
          token_callback_function: () => {
            startTime ??= performance.now();
            if (numTokens++ > 0) {
              tps = (numTokens / (performance.now() - startTime)) * 1000;
            }
          }
        });

        past_key_values_cache ??= new DynamicCache();

        const output = await generator(data.prompt, {
          max_new_tokens: data.max_new_tokens || 512,
          do_sample: false,
          temperature: data.temperature || 0.7,
          streamer,
          stopping_criteria,
          past_key_values: past_key_values_cache,
          return_full_text: false
        });

        self.postMessage({
          status: 'complete',
          output: Array.isArray(output) ? output[0].generated_text : output,
          total_tokens: numTokens,
          total_time: performance.now() - startTime
        });

      } catch (err) {
        console.error('[λPU] Erro na geração:', err);
        self.postMessage({ status: 'error', error: err.message });
      }
      break;
    }

    case 'interrupt': {
      stopping_criteria.interrupt();
      self.postMessage({ status: 'interrupted' });
      break;
    }

    case 'reset': {
      disposePastKeyValues();
      stopping_criteria.reset();
      break;
    }

    default:
      self.postMessage({ status: 'error', error: `Comando desconhecido: ${type}` });
  }
};
