#!/usr/bin/env node
// arkhe_os/core/index.ts
import { GenesisEngine, GenesisConfig } from './bios/GenesisEngine.js';

async function main(): Promise<void> {
  console.log('ARKHE OS - Booting...');

  // Carregar configuração de Gênesis
  const config: GenesisConfig = {
    genesisPath: './config/genesis.yaml',
    hardwareConfig: {
      // Configuração do hardware quântico (Substrato 309)
      // ...
    },
  };

  const genesisEngine = new GenesisEngine();

  // Registrar signal handlers para graceful shutdown
  process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    await genesisEngine.shutdown('SIGTERM');
    process.exit(0);
  });

  process.on('SIGINT', async () => {
    console.log('Received SIGINT, shutting down gracefully...');
    await genesisEngine.shutdown('SIGINT');
    process.exit(0);
  });

  // Bootstrap
  const success = await genesisEngine.bootstrap(config);
  if (!success) {
    console.error('Boot failed');
    process.exit(1);
  }
}

// Only run main if this file is executed directly
import { fileURLToPath } from 'url';
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main();
}
