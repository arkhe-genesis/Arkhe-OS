import { LFIRGraph, LFIRNode, LFIRNodeType } from '../../lfir';

export async function parse(source: Buffer, graph: any, parentId: string, config: any) {
  const node = new LFIRNode('tensorflow_model', LFIRNodeType.Operation, 'tensorflow');
  node.attributes['framework'] = 'tensorflow';
  graph.addNode(node);
  graph.link(parentId, node.id);
}
