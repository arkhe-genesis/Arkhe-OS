// arkhe_os/dashboard/webgpu/fuzzing.ts
export interface FuzzingFinding {
  id: string;
  affected_module_position: any;
  severity: number;
  coherence_delta: number;
  metadata: any;
}

export class FuzzingResultStream {
  on(event: string, callback: (finding: FuzzingFinding) => void) {
      // Mock implementation
  }
}
