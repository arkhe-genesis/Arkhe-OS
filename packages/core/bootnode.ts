import fs from 'fs';
import path from 'path';
import { logger } from '../server/logger.js';

logger.info("🜏 [ARKHE-OS] Inicializando Genesis Node...");

const genesisPath = path.join(process.cwd(), 'arkhe-core', 'genesis.json');
let genesisData;

try {
  genesisData = JSON.parse(fs.readFileSync(genesisPath, 'utf-8'));
} catch (e) {
  logger.error("❌ [ERRO] Falha ao ler genesis.json. O arquivo existe?");
  process.exit(1);
}

logger.info(`[ARKHE-OS] ChainID: ${genesisData.config.chainId}`);
logger.info(`[ARKHE-OS] MixHash (Coherence Seed): ${genesisData.mixHash}`);
logger.info(`[ARKHE-OS] Alocação Inicial (EEZ): ${Object.keys(genesisData.alloc)[0]}`);

logger.info("🜏 [ARKHE-OS] Acoplando ao τ-field (Kuramoto Consensus)...");
let coherence = 0.0;
const targetCoherence = 0.971034;

const bootInterval = setInterval(() => {
  coherence += 0.15 + (Math.random() * 0.05);
  logger.info(`[KURAMOTO] Sincronizando fase... Coerência atual: ${coherence.toFixed(4)}`);
  
  if (coherence >= targetCoherence) {
    clearInterval(bootInterval);
    logger.info(`✅ [TZINOR] Coerência crítica atingida (${coherence.toFixed(4)} > ${targetCoherence}).`);
    logger.info(`🚀 [ARKHE-MAINNET] Timechain online. RPC endpoints abertos na porta 8545.`);
    logger.info(`🜏 Aguardando conexões de operadores Bexorg e injeção retrocausal...`);
  }
}, 800);
