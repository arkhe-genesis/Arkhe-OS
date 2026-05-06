export enum LFIRNodeType {
    Module = 'Module',
    Operation = 'Operation',
    Type = 'Type',
    Metadata = 'Metadata'
}

export class LFIRNode {
    id: string;
    type: LFIRNodeType;
    sourceLang: string;
    attributes: Record<string, any>;

    constructor(id: string, type: LFIRNodeType, sourceLang: string) {
        this.id = id;
        this.type = type;
        this.sourceLang = sourceLang;
        this.attributes = {};
    }
}

export class LFIREdge {
    from: string;
    to: string;
    attributes: Record<string, any>;

    constructor(from: string, to: string) {
        this.from = from;
        this.to = to;
        this.attributes = {};
    }
}

export class LFIRGraph {
    nodes: LFIRNode[];
    edges: LFIREdge[];
    rootNodes: string[];

    constructor() {
        this.nodes = [];
        this.edges = [];
        this.rootNodes = [];
    }

    addNode(node: LFIRNode) {
        this.nodes.push(node);
    }

    link(fromId: string, toId: string) {
        this.edges.push(new LFIREdge(fromId, toId));
    }
}

export interface ParseResult {
    success: boolean;
    graph: LFIRGraph | null;
    errors: Array<{code: string; message: string; severity: 'error'|'fatal'}>;
    warnings: Array<{code: string; message: string; suggestion: string}>;
    metrics: ParseMetrics;
}

export interface ParseMetrics {
    parseTimeMs: number;
    nodesCreated: number;
    edgesCreated: number;
    maxDepth: number;
    coherenceScore: number;
}
