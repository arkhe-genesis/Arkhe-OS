// src/daemon/index.ts
import { AGIDaemonController } from './AGIDaemonController';

export async function stop() {
    console.log("Stopping from script...");
    const daemon = new AGIDaemonController({ nodeId: 'stop-script' });
    await daemon.stop();
}

if (require.main === module) {
    const daemon = new AGIDaemonController({ nodeId: 'main-daemon' });
    daemon.initialize().then(() => daemon.run()).catch(console.error);
}
