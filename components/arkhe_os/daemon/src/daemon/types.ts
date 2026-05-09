export type LifecycleState = 'initializing' | 'running' | 'degraded' | 'stopping' | 'stopped' | 'error';

export enum LifecycleEvent {
  INITIALIZING = 'INITIALIZING',
  RUNNING = 'RUNNING',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
  ERROR = 'ERROR'
}
