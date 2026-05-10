import { LFIRGraph, LFIRNode, LFIRNodeType } from '../../lfir';

export async function parse(source: Buffer, graph: any, parentId: string, config: any) {
  const node = new LFIRNode('onnx_model', LFIRNodeType.Operation, 'onnx');
  node.attributes['framework'] = 'onnx';
  graph.addNode(node);
  graph.link(parentId, node.id);
}
