// arkhe_worker.js — Web Worker que executa o módulo WASM e gerencia operações.

importScripts('arkhe_runtime.js'); // Arkhe compilado para WASM via emscripten/wasm-pack

let arkheModule = null;

self.onmessage = async (e) => {
    const { type, id, wasmUrl, path, payload } = e.data;

    try {
        if (type === 'init') {
            arkheModule = await Module({ locateFile: (f) => wasmUrl + f });
            self.postMessage({ type: 'ready' });
        }
        else if (type === 'quantum_execute') {
            const result = await arkheModule.ccall('execute_quantum', 'string', ['string'], [JSON.stringify(payload)]);
            self.postMessage({ id, result: JSON.parse(result) });
        }
        else if (type === 'file_access') {
            // Acessar IndexedDB
            const db = await openDB();
            const tx = db.transaction('files', 'readwrite');
            const store = tx.objectStore('files');
            const content = await store.get(path);
            self.postMessage({ id, result: { success: true, exists: !!content, data: content } });
        }
    } catch (err) {
        self.postMessage({ type: 'error', error: err.message });
    }
};

async function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('arkhe_wasm_store', 1);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
        request.onupgradeneeded = (e) => {
            e.target.result.createObjectStore('files', { keyPath: 'path' });
        };
    });
}