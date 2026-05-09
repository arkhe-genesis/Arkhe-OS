// src/daemon/index.ts
import { AGIDaemonController } from './AGIDaemonController';
import { TemporalLogger } from '../logging/TemporalLogger';

export { AGIDaemonController } from './AGIDaemonController';

export async function stop() {
  const daemon = new AGIDaemonController({ nodeId: 'stop-script', logger: new TemporalLogger({nodeId: 'stop'}) });
  await daemon.stop({ reason: 'npm-stop' });
}

if (require.main === module) {
  const daemon = new AGIDaemonController({ nodeId: process.env.ARKHE_NODE_ID || 'default-node' });
  daemon.initialize().then(success => {
    if (success) {
      daemon.run().catch(console.error);
    } else {
      process.exit(1);
    }
  }).catch(console.error);

export async function stop() {
    console.log("Stopping from script...");
    const daemon = new AGIDaemonController({ nodeId: 'stop-script' });
    await daemon.stop();
}

if (require.main === module) {
    const daemon = new AGIDaemonController({ nodeId: 'main-daemon' });
    daemon.initialize().then(() => daemon.run()).catch(console.error);
}
