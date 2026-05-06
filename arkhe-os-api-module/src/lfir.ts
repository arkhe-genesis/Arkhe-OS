export enum LFIRNodeType {
    MODULE = 'LFIRModule',
    OPERATION = 'LFIROperation',
    TYPE = 'LFIRType',
    METADATA = 'LFIRMetadata',
    ENDPOINT = 'endpoint',
    FUNCTION = 'function',
    BLOCK = 'block'
}

export class LFIRNode {
    id: string;
    type: LFIRNodeType;
    name: string;
    namespace: string;
    attributes: Record<string, any>;

    constructor(id: string, type: LFIRNodeType, namespace: string) {
        this.id = id;
        this.type = type;
        this.name = id;
        this.namespace = namespace;
        this.attributes = {};
    }
}

export class LFIRGraph {
    nodes: LFIRNode[];
    edges: { source: string, target: string, relation: string }[];
    rootNodes: string[];
    metadata: { coherence?: number, parseTimestamp?: Date };

    constructor() {
        this.nodes = [];
        this.edges = [];
        this.rootNodes = [];
        this.metadata = {};
    }

    addNode(node: LFIRNode) {
        this.nodes.push(node);
    }
}
