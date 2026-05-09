import { LFIRGraph, LFIRNode, LFIRNodeType } from '../../lfir';

export async function parse(source: string, graph: any, parentId: string, config: any) {
  const node = new LFIRNode('training_log', LFIRNodeType.Metadata, 'log');
  node.attributes['type'] = 'training_log';
  graph.addNode(node);
  graph.link(parentId, node.id);
}
