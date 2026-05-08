// Graceful shutdown script
import { AGIDaemonController } from '../src/daemon/AGIDaemonController';
import { TemporalLogger } from '../src/logging/TemporalLogger';

async function main() {
  const daemon = new AGIDaemonController({ nodeId: 'shutdown-script', logger: new TemporalLogger({nodeId: 'shutdown'}) });
  await daemon.stop({ reason: 'manual-shutdown' });
}
main().catch(console.error);
// scripts/graceful-shutdown.ts
console.log('Executing graceful shutdown sequence...');
process.exit(0);
