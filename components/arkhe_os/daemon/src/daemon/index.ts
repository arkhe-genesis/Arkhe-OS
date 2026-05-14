// src/daemon/index.ts
import { AGIDaemonController } from './AGIDaemonController';
import { TemporalLogger } from '../logging/TemporalLogger';

export { AGIDaemonController } from './AGIDaemonController';

export async function stop() {
  const daemon = new AGIDaemonController({ nodeId: 'stop-script', logger: new TemporalLogger({nodeId: 'stop'}) });
  await daemon.stop({ reason: 'npm-stop' });
}

export async function stop() {
    console.log("Stopping from script...");
    const daemon = new AGIDaemonController({ nodeId: 'stop-script' });
    await daemon.stop();
}

if (require.main === module) {
    const daemon = new AGIDaemonController({ nodeId: 'main-daemon' });
    daemon.initialize().then(() => daemon.run()).catch(console.error);
}
