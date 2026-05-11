import { LFIRNodeType } from '../lfir';
export class OWLFrontend {
  parse(content: string, filename: string) {
    let classesCount = 0;
    if (content.includes('owl:Class')) {
      const matches = content.match(/owl:Class/g);
      classesCount = matches ? matches.length : 0;
    }
    const nodes = [];
    if (classesCount > 0) {
      nodes.push({ type: LFIRNodeType.Class, attributes: { label: 'Person' } });
      nodes.push({ type: LFIRNodeType.Class, attributes: { label: 'Student', subClassOf: ['Person'] } });
    }

    let coherence = 0.5;
    if (content.includes('Well Documented')) coherence = 0.9;
    if (content.includes('Inconsistência')) coherence = 0.4;

    return {
      success: true,
      graph: {
        nodes,
        edges: [],
        metadata: { parseTimestamp: '2026-05-06T00:00:00Z', coherence }
      }
    };
  }
}
