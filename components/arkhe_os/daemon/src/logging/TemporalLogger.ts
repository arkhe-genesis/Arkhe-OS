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
}
