import { OWLFrontend } from './owl_frontend';
import { OWLCoherenceMapper } from './owl_coherence_mapper';
import { LFIRGraph, LFIRNode, LFIREdge, LFIRNodeType } from './ai_engineering_frontend';
import { ontologySemanticDistance } from './ontology_diff_tool';
import { proveOntologyConsistency } from './prove_ontology_consistency';

describe('OWL Ontology Parser (Substrate 253)', () => {
  it('should parse OWL ontology into LFIR graph', async () => {
    const frontend = new OWLFrontend({ enableReasoning: true });
    const result = await frontend.parse('dummy rdf data', 'test.ttl');

    expect(result.success).toBe(true);
    expect(result.graph.nodes.length).toBeGreaterThan(0);
    expect(result.graph.rootNodes.length).toBeGreaterThan(0);
    expect(result.graph.nodes[0].attributes.coherence_score).toBe(0.85);
  });

  it('should compute axiom gradients correctly', async () => {
    const mapper = new OWLCoherenceMapper();
    const graph = new LFIRGraph();
    const node: LFIRNode = {
      id: 'ontology_root',
      type: 'Ontology',
      namespace: 'owl',
      attributes: {
        coherence_score: 0.9
      }
    };
    graph.addNode(node);

    const mockEdge = {
      from: 'A',
      to: 'B',
      relation: 'EquivalentClass'
    };

    graph.edges.push(mockEdge);

    expect(mapper.computeAxiomGradient(mockEdge)).toBe(0.10);

    // Test processing
    await expect(mapper.processOntology(graph, 'ontology_1')).resolves.not.toThrow();
  });

  it('should prove ontology consistency', async () => {
    const result = await proveOntologyConsistency('test.ttl');
    expect(result.consistent).toBe(true);
    expect(result.coherenceScore).toBe(0.85);
  });

  it('should calculate semantic distance between two ontologies', async () => {
    const g1 = new LFIRGraph();
    g1.addNode({ id: '1', type: 'Class', namespace: '', attributes: { label: 'A', comment: 'B' }});
    const g2 = new LFIRGraph();
    g2.addNode({ id: '2', type: 'Class', namespace: '', attributes: { label: 'A', comment: 'B' }});

    const embeddingModel = {
      encode: async () => [0.1, 0.2]
    };

    const distance = await ontologySemanticDistance(g1, g2, embeddingModel);
    expect(distance).toBeGreaterThanOrEqual(0);
    expect(distance).toBeLessThanOrEqual(1);
  });
});
