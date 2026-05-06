import { LFIRGraph, LFIRNode, LFIRNodeType } from '../../lfir';

export async function parse(source: Buffer | string, graph: any, parentId: string, config: any) {
  const node = new LFIRNode('dataset', LFIRNodeType.Metadata, 'dataset');
  node.attributes['type'] = 'dataset';
  graph.addNode(node);
  graph.link(parentId, node.id);
}
