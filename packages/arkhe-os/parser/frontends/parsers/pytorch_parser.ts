import { LFIRGraph, LFIRNode, LFIRNodeType } from '../../lfir';

export async function parse(source: Buffer, graph: any, parentId: string, config: any) {
  const node = new LFIRNode('pytorch_model', LFIRNodeType.Operation, 'pytorch');
  node.attributes['framework'] = 'pytorch';
  graph.addNode(node);
  graph.link(parentId, node.id);
}
