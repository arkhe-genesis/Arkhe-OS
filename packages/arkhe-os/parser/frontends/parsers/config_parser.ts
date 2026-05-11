import { LFIRGraph, LFIRNode, LFIRNodeType } from '../../lfir';

export async function parse(source: string, graph: any, parentId: string, config: any) {
  const node = new LFIRNode('config', LFIRNodeType.Metadata, 'yaml');
  node.attributes['type'] = 'config';
  graph.addNode(node);
  graph.link(parentId, node.id);
}
