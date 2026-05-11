/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// src/storage/embryovault.js
// Bloco #300.2 — O Cofre do Embrião (CacheStorage)
// Delegado ao cache interno do Transformers.js

export const MODEL_CATALOG = {
  'bonsai-1.7b': 'onnx-community/Bonsai-1.7B-ONNX',
  'bonsai-4b': 'onnx-community/Bonsai-4B-ONNX'
};

export class EmbryoVault {
  async init() {}
  async hasModel(modelId) { return false; }
  async fetchModel(modelId, onProgress) {
    console.log(`[ARKHE] Delegando carregamento de ${modelId} ao λPU (0x296:DELEGATE)`);
  }
  async clear() {
    await caches.delete('transformers-cache');
    console.log('[ARKHE] Cofre purgado');
  }
}
