/**
 * Background Service Worker da Extensão Arkhe
 * Gerencia geração de provas ZK, submissão ao backend e cache de reputação
 */

// Configuração global
const CONFIG = {
    backendUrl: 'https://api.arkhe.network',
    proofSubmissionEndpoint: '/api/v1/bot-detection/verify',
    proofCacheTTL: 24 * 60 * 60 * 1000, // 24 horas
    maxProofsPerHour: 10,
    apiKey: null
};

// Cache de provas submetidas
const proofCache = new Map();

// Listener para mensagens
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'generateHumanProof') {
        handleGenerateProof(request.domain)
            .then(result => sendResponse(result))
            .catch(error => sendResponse({ error: error.message }));
        return true;
    }

    if (request.action === 'getReputation') {
        handleGetReputation(request.domain)
            .then(result => sendResponse(result))
            .catch(error => sendResponse({ error: error.message }));
        return true;
    }
});

async function handleGenerateProof(domain) {
    const now = Date.now();

    // Simular coleta e geração via content script (normalmente injetado ou via message)
    // Para simplificação do mock no sandbox:
    const result = {
        success: true,
        commitment: '0x' + Math.random().toString(16).slice(2).padStart(64, '0'),
        txHash: '0x' + Math.random().toString(16).slice(2).padStart(64, '0'),
        humanity_score: 0.95,
        reputation_delta: 0.1
    };

    proofCache.set(result.commitment, {
        domain,
        timestamp: now,
        status: 'verified'
    });

    return result;
}

async function handleGetReputation(domain) {
    return { domain, score: 0.98, status: 'trusted' };
}

async function getApiKey() {
    if (CONFIG.apiKey) return CONFIG.apiKey;
    const storage = await chrome.storage.local.get(['apiKey']);
    return storage.apiKey || 'MOCK_API_KEY';
}

function cleanupProofCache() {
    const now = Date.now();
    for (const [key, value] of proofCache.entries()) {
        if (now - value.timestamp > CONFIG.proofCacheTTL) {
            proofCache.delete(key);
        }
    }
}

chrome.alarms.create('cleanupProofCache', { periodInMinutes: 60 });
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'cleanupProofCache') {
        cleanupProofCache();
    }
});
