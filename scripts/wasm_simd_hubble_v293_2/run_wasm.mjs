/*
 * Copyright (c) Arkhe Network. All rights reserved.
 * Licensed under the MIT License. See LICENSE in the project root for license information.
 */


/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import fs from 'node:fs';
import os from 'node:os';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Worker, isMainThread, parentPort } from 'node:worker_threads';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

if (isMainThread) {
    // Carregar WASM sincronicamente para simplificar no script Node.js
    const wasmBuffer = fs.readFileSync(__dirname + '/arkhe_hubble_kernel.wasm');

    class HubbleWasmEngine {
        constructor() {
            this.workers = [];
            this.ready = false;
            this.wasmModule = null;
            // Node.js fallback for navigator
            this.numThreads = os.cpus().length || 4;
        }

        async init() {
            // Compilar e instanciar o módulo WASM
            this.wasmModule = await WebAssembly.compile(wasmBuffer);

            // Criar workers com módulo WASM compilado
            for (let i = 0; i < this.numThreads; i++) {
                const worker = new Worker(__filename);
                worker.postMessage({ type: 'init', wasmModule: this.wasmModule });
                this.workers.push(worker);
            }
            this.ready = true;
            console.log(`🔺 Fornalha WASM-SIMD iniciada com ${this.numThreads} threads.`);
        }

        computeGlobalCoherence(nodesData) {
            return new Promise((resolve) => {
                // Criar SharedArrayBuffer para a matriz de correlação
                const N = nodesData.length / 5; // 5 floats por nó: lat, lon, phase, coherence, kappa
                const sharedBuffer = new SharedArrayBuffer(N * N * 4); // float32
                const coherenceMatrix = new Float32Array(sharedBuffer);

                let completed = 0;
                const nodesPerThread = Math.ceil(N / this.numThreads);

                // Distribuir trabalho pelas threads
                for (let i = 0; i < this.numThreads; i++) {
                    const worker = this.workers[i];
                    const start = i * nodesPerThread;
                    const end = Math.min(start + nodesPerThread, N);

                    worker.on('message', (e) => {
                        completed++;
                        if (completed === this.numThreads) {
                            // Todas as threads completaram: agregar resultados
                            const m_global = this.aggregateCoherence(coherenceMatrix, N);
                            resolve(m_global);

                            // Cleanup
                            for (const w of this.workers) {
                                w.terminate();
                            }
                        }
                    });

                    worker.postMessage({
                        type: 'compute',
                        start, end,
                        nodesData: nodesData.buffer, // Enviar buffer em vez de Float32Array
                        coherenceMatrix: coherenceMatrix.buffer,
                    });
                }
            });
        }

        aggregateCoherence(matrix, N) {
            // Calcula M_global como a média da matriz de correlação + coerências locais
            let sum = 0;
            for (let i = 0; i < N; i++) {
                for (let j = i + 1; j < N; j++) {
                    sum += matrix[i * N + j];
                }
            }
            const avgCorrelation = sum / (N * (N - 1) / 2);
            // M_global combina a correlação média com a média das coerências locais
            return Math.min(1.0, avgCorrelation + 0.1); // Placeholder para a lógica completa
        }
    }

    async function run() {
        // Exemplo de uso com o ArkheCanvas
        const engine = new HubbleWasmEngine();
        await engine.init();

        // Obter dados dos 1024 nós
        const nodesData = new Float32Array(1024 * 5); // lat, lon, phase, coherence, kappa
        // Inicializar com alguns valores aleatórios
        for(let i=0; i<nodesData.length; i++) {
            if (i % 5 === 0) {nodesData[i] = Math.random() * 180 - 90;} // lat
            if (i % 5 === 1) {nodesData[i] = Math.random() * 360 - 180;} // lon
            if (i % 5 === 2) {nodesData[i] = Math.random() * Math.PI * 2;} // phase
        }

        const mGlobal = await engine.computeGlobalCoherence(nodesData);
        console.log(`🌌 Coerência de Hubble (WASM-SIMD): ${mGlobal.toFixed(6)}`);
        console.log("arkhe > 293_2_SUBSTRATE_CANONIZED: WASM_SIMD_MULTITHREADED_HUBBLE_ENGINE");
    }

    run().catch(console.error);

} else {
    // Worker code
    let wasmInstance = null;

    parentPort.on('message', async (e) => {
        if (e.type === 'init') {
            const memory = new WebAssembly.Memory({ initial: 256, maximum: 256, shared: true });
            wasmInstance = await WebAssembly.instantiate(e.wasmModule, {
                env: {
                    memory: memory
                }
            });
        } else if (e.type === 'compute') {
            const nodesData = new Float32Array(e.nodesData);
            const coherenceMatrix = new Float32Array(e.coherenceMatrix);

            // Alojar memória no WASM
            const wasmMemory = new Float32Array(wasmInstance.exports.memory.buffer);

            // Copiar nodesData para WASM
            const nodesPtr = wasmInstance.exports.malloc(nodesData.length * 4);
            wasmMemory.set(nodesData, nodesPtr / 4);

            // Alocar matriz de coerência no WASM (tamanho N*N)
            const N = nodesData.length / 5;
            const matrixPtr = wasmInstance.exports.malloc(N * N * 4);

            // Executar cálculo
            wasmInstance.exports.compute_global_coherence_matrix(e.start, e.end, nodesPtr, matrixPtr);

            // Copiar resultado de volta para o SharedArrayBuffer
            // NOTA: Em um caso real, iteraríamos apenas sobre a parte computada por este worker,
            // mas para este teste simples copiamos tudo.
            for (let i = e.start; i < e.end; i++) {
                for (let j = i + 1; j < N; j++) {
                     coherenceMatrix[i * N + j] = wasmMemory[matrixPtr / 4 + i * N + j];
                     coherenceMatrix[j * N + i] = coherenceMatrix[i * N + j];
                }
            }

            // Libertar memória
            wasmInstance.exports.free(nodesPtr);
            wasmInstance.exports.free(matrixPtr);

            parentPort.postMessage({ done: true });
        }
    });
}
