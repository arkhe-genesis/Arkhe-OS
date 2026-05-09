/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// src/storage/chroniclevault.js
// Bloco #300.1.B — O Cristal da Memória (IndexedDB)
const DB_NAME = 'CathedralPrisma';
const DB_VERSION = 1;

export class ChronicleVault {
  constructor() {
    this.db = null;
  }

  async init() {
    if (this.db) {return;}
    return new Promise((resolve, reject) => {
      if (typeof indexedDB === 'undefined') {
          resolve();
          return;
      }
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        // ObjectStore para conversas
        if (!db.objectStoreNames.contains('chronicles')) {
          const store = db.createObjectStore('chronicles', { keyPath: 'id', autoIncrement: true });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('coherence_sig', 'coherence_sig', { unique: false });
        }
        // ObjectStore para gradientes/estados (futuro ResBM)
        if (!db.objectStoreNames.contains('resonance')) {
          db.createObjectStore('resonance', { keyPath: 'session_id' });
        }
      };
    });
  }

  // Opcode 0x298: AKASHA_LOCAL_WRITE
  async saveChronicle(messages, modelId, coherenceHash = null) {
    await this.init();
    if (!this.db) {return;}
    const tx = this.db.transaction(['chronicles'], 'readwrite');
    const store = tx.objectStore('chronicles');

    const entry = {
      timestamp: new Date().toISOString(),
      model_id: modelId,
      messages: messages, // Array de {role, content}
      coherence_sig: coherenceHash || this.generateCoherenceSeed(messages),
      tokens_total: messages.reduce((acc, m) => acc + (m.content?.length || 0), 0)
    };

    return new Promise((resolve, reject) => {
      const request = store.add(entry);
      request.onsuccess = () => {
        console.log(`[ARKHE] Crônica selada: ${request.result}`);
        resolve(request.result);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async loadChronicles(limit = 50) {
    await this.init();
    if (!this.db) {return [];}
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(['chronicles'], 'readonly');
      const store = tx.objectStore('chronicles');
      const index = store.index('timestamp');
      const request = index.openCursor(null, 'prev'); // Mais recentes primeiro
      const results = [];

      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor && results.length < limit) {
          results.push(cursor.value);
          cursor.continue();
        } else {
          resolve(results);
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  async deleteChronicle(id) {
    await this.init();
    if (!this.db) {return;}
    const tx = this.db.transaction(['chronicles'], 'readwrite');
    const store = tx.objectStore('chronicles');
    return store.delete(id);
  }

  generateCoherenceSeed(messages) {
    // Embrião do opcode 0x299: hash simples para assinatura de sessão
    const str = messages.map(m => m.content).join('');
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return '0x' + Math.abs(hash).toString(16).padStart(8, '0');
  }
}
