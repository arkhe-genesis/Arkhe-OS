export var LFIRNodeType;
(function (LFIRNodeType) {
    LFIRNodeType["Module"] = "Module";
    LFIRNodeType["Operation"] = "Operation";
    LFIRNodeType["Type"] = "Type";
    LFIRNodeType["Metadata"] = "Metadata";
})(LFIRNodeType || (LFIRNodeType = {}));
export class LFIRNode {
    id;
    type;
    sourceLang;
    attributes;
    constructor(id, type, sourceLang) {
        this.id = id;
        this.type = type;
        this.sourceLang = sourceLang;
        this.attributes = {};
    }
}
export class LFIREdge {
    from;
    to;
    attributes;
    constructor(from, to) {
        this.from = from;
        this.to = to;
        this.attributes = {};
    }
}
export class LFIRGraph {
    nodes;
    edges;
    rootNodes;
    constructor() {
        this.nodes = [];
        this.edges = [];
        this.rootNodes = [];
    }
    addNode(node) {
        this.nodes.push(node);
    }
    link(fromId, toId) {
        this.edges.push(new LFIREdge(fromId, toId));
    }
}
