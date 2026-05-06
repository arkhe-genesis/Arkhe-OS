import { LFIRGraph, LFIRNode, LFIRNodeType } from '../../lfir';

export class OpenAPIParser {
    static parse(spec: any): { success: boolean, graph?: LFIRGraph, errors: string[] } {
        if (!spec || !spec.openapi || typeof spec.openapi !== 'string' || !spec.openapi.startsWith('3.')) {
            return { success: false, errors: ['Invalid OpenAPI spec'] };
        }

        const graph = new LFIRGraph();
        graph.metadata.parseTimestamp = new Date();
        graph.metadata.coherence = 0.8;

        if (spec.paths) {
            for (const path of Object.keys(spec.paths)) {
                const pathItem = spec.paths[path];
                for (const method of Object.keys(pathItem)) {
                    const op = pathItem[method];
                    const endpointNode = new LFIRNode(`${method}_${path}`, LFIRNodeType.ENDPOINT, 'openapi');
                    endpointNode.attributes['path'] = path;
                    endpointNode.attributes['method'] = method;
                    graph.addNode(endpointNode);

                    const funcNode = new LFIRNode(`${method}_${path}_func`, LFIRNodeType.FUNCTION, 'openapi');
                    graph.addNode(funcNode);
                    graph.edges.push({ source: endpointNode.id, target: funcNode.id, relation: 'method_of' });
                }
            }
        }

        return { success: true, graph, errors: [] };
    }
}
