// src/logging/TemporalLogger.ts
export class TemporalLogger {
    public nodeId: string;
    public startTime: number = Date.now();

    constructor(options: { nodeId: string }) {
        this.nodeId = options.nodeId;
    }

    info(message: string, context?: any) {
        console.log(`[INFO] [${this.nodeId}] ${message}`, context ? JSON.stringify(context) : '');
    }

    debug(message: string, context?: any) {
        console.debug(`[DEBUG] [${this.nodeId}] ${message}`, context ? JSON.stringify(context) : '');
    }

    warn(message: string, context?: any) {
        console.warn(`[WARN] [${this.nodeId}] ${message}`, context ? JSON.stringify(context) : '');
    }

    error(message: string, context?: any) {
        console.error(`[ERROR] [${this.nodeId}] ${message}`, context ? JSON.stringify(context) : '');
    }

    metrics(name: string, data: any) {
        console.log(`[METRIC] ${name}`, JSON.stringify(data));
    }
}
