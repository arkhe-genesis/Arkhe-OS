export class TemporalLogger {
  public nodeId: string;
  public startTime: number = Date.now();

  constructor(options: { nodeId: string }) {
    this.nodeId = options.nodeId;
  }

  info(msg: string, meta?: any): void { console.log(`INFO: ${msg}`, meta); }
  debug(msg: string, meta?: any): void { console.log(`DEBUG: ${msg}`, meta); }
  warn(msg: string, meta?: any): void { console.log(`WARN: ${msg}`, meta); }
  error(msg: string, meta?: any): void { console.log(`ERROR: ${msg}`, meta); }
  metrics(name: string, meta?: any): void { console.log(`METRIC [${name}]:`, meta); }
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
