export enum IDETool {
  VS_CODE = 'VS_CODE'
}

export interface DevEvent {
  tool: IDETool;
  event_type: 'edit' | 'save' | 'completion_accept' | 'diagnostic_fix' | string;
  file_path: string;
  content_snippet: string;
  timestamp: number;
  session_id: string;
  metadata: {
    language: string;
    line_count: number;
    event_source: string;
    [key: string]: any;
  };
}

export interface LFIRNode {
  id: string;
  type: string;
  attributes: Record<string, any>;
  edges: any[];
}

export interface LFIRGraph {
  nodes: LFIRNode[];
  edges: any[];
}
