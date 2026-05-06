// tests/parsers/owl.test.ts
import { OWLFrontend } from '@/parser/frontends/owl_frontend';
import { LFIRNodeType } from '@/parser/lfir';

describe('OWLFrontend', () => {
  let parser: OWLFrontend;

  beforeEach(() => {
    parser = new OWLFrontend();
  });

  test('✅ Should parse OWL class hierarchy', () => {
    const turtle = `
      @prefix owl: <http://www.w3.org/2002/07/owl#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

      :Person a owl:Class .
      :Student rdfs:subClassOf :Person .
    `;
    const result = parser.parse(turtle, 'test.owl');

    expect(result.success).toBe(true);
    const classes = result.graph!.nodes.filter(n => n.type === LFIRNodeType.Class);
    expect(classes).toHaveLength(2);
    expect(classes.find(c => c.attributes['label'] === 'Student')?.attributes['subClassOf'])
      .toContain('Person');
  });

  test('✅ Should compute coherence for well-documented ontology', () => {
    const turtle = `
      :WellDocumented a owl:Class ;
        rdfs:label "Well Documented"@en ;
        rdfs:comment "This class has documentation"@en .
    `;
    const result = parser.parse(turtle, 'doc.owl');
    expect(result.graph!.metadata.coherence).toBeGreaterThan(0.8);
  });

  test('❌ Should detect inconsistent ontology via reasoner', () => {
    const turtle = `
      :A a owl:Class .
      :B a owl:Class .
      :A owl:disjointWith :B .
      :x a :A, :B .  # Inconsistência: x não pode ser A e B se são disjuntos
    `;
    const result = parser.parse(turtle, 'inconsistent.owl');
    // Em produção: reasoner detectaria inconsistência e reduziria coerência
    expect(result.graph!.metadata.coherence).toBeLessThan(0.5);
  });

  test('📸 Snapshot of parsed ontology LFIR', () => {
    const turtle = `
      :API a owl:Class ;
        rdfs:label "API" ;
        rdfs:comment "Application Programming Interface" .
    `;
    const result = parser.parse(turtle, 'api.owl');
    expect(result.graph).toMatchSnapshot({
      metadata: {
        parseTimestamp: expect.any(String),
        coherence: expect.any(Number),
      },
    });
  });
});
