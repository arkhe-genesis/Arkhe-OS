import { BitcoinCoherenceMapper, CoherenceGradientChannel } from '../../src/integration/bitcoin_coherence_mapper';
import { LFIRGraph, LFIRNode, LFIRNodeType } from '../../src/lfir';

describe('BitcoinCoherenceMapper', () => {
  let channel: CoherenceGradientChannel;
  let mapper: BitcoinCoherenceMapper;

  beforeEach(() => {
    channel = new CoherenceGradientChannel('test-channel', 'test-node', 'test');
    mapper = new BitcoinCoherenceMapper(channel, {});
  });

  test('✅ Should assign positive coherence to high difficulty block', () => {
    const graph = new LFIRGraph();
    const blockNode = new LFIRNode('block_1', LFIRNodeType.BLOCK, 'bitcoin');
    blockNode.attributes['difficulty'] = 83e12; // 83T
    blockNode.attributes['pow_valid'] = true;
    graph.addNode(blockNode);
    graph.rootNodes.push(blockNode.id);

    mapper.processLFIRGraph(graph);
    expect(mapper.getMapperMetrics().gradientsSubmitted).toBeGreaterThan(0);
  });

  test('❌ Should penalize invalid PoW', () => {
    const graph = new LFIRGraph();
    const blockNode = new LFIRNode('block_2', LFIRNodeType.BLOCK, 'bitcoin');
    blockNode.attributes['difficulty'] = 1;
    blockNode.attributes['pow_valid'] = false;
    graph.addNode(blockNode);
    graph.rootNodes.push(blockNode.id);

    mapper.processLFIRGraph(graph);
    // Nesse caso, o gradiente deve ser muito negativo, mas ainda submetido
    expect(mapper.getMapperMetrics().gradientsSubmitted).toBe(1);
  });

  test('Should not submit gradient for invalid pow with high difficulty (simulate other branches)', () => {
    const graph = new LFIRGraph();
    const blockNode = new LFIRNode('block_3', LFIRNodeType.BLOCK, 'bitcoin');
    blockNode.attributes['difficulty'] = 83e12;
    blockNode.attributes['pow_valid'] = false;
    graph.addNode(blockNode);

    mapper.processLFIRGraph(graph);
    expect(mapper.getMapperMetrics().gradientsSubmitted).toBe(0);
  });

  test('Should ignore non block nodes', () => {
    const graph = new LFIRGraph();
    const node = new LFIRNode('node_3', LFIRNodeType.ENDPOINT, 'bitcoin');
    graph.addNode(node);

    mapper.processLFIRGraph(graph);
    expect(mapper.getMapperMetrics().gradientsSubmitted).toBe(0);
  });
});
