// arkhe-os/parser/frontends/owl_coherence_mapper.ts
import { LFIRGraph } from '../lfir';

export const AXIOM_GRADIENTS: Record<string, number> = {
  // Definições positivas (aumentam coerência)
  'SubClassOf': +0.05,           // Hierarquia bem definida
  'EquivalentClass': +0.10,      // Definição completa (bidirecional)
  'DisjointWith': +0.08,         // Separação clara de conceitos
  'FunctionalProperty': +0.04,   // Restrição de unicidade
  'InverseFunctionalProperty': +0.04,
  'TransitiveProperty': +0.03,   // Propagação lógica
  'SymmetricProperty': +0.03,

  // Anotações (contribuição leve mas importante)
  'rdfs:label': +0.02,
  'rdfs:comment': +0.02,
  'skos:definition': +0.03,

  // Importações (reuso de conhecimento)
  'owl:imports': +0.03,

  // Restrições negativas (reduzem coerência se mal aplicadas)
  'InconsistentAxiom': -0.20,    // Detectado por reasoner
  'CyclicSubClassOf': -0.15,     // Hierarquia circular não intencional
  'UnsatisfiableClass': -0.10,   // Classe com restrições contraditórias

  // Neutros (sem impacto direto em Φ_C)
  'AnnotationProperty': 0,
  'Deprecated': 0,
};

export class MockChannel {
  async submitLocalGradient(gradients: number[], p1: number, p2: number, sampleCount: number, p3: number, metadata: any) {
    // Mock submission to coherence channel
  }
}

export class OWLCoherenceMapper {
  private batchBuffer: Array<{ edge: any; gradient: number }> = [];
  private readonly BATCH_SIZE = 50;
  private channel = new MockChannel();

  private computeAxiomGradient(edge: any): number {
    return AXIOM_GRADIENTS[edge.relation] || 0;
  }

  private async submitGlobalCoherence(ontologyId: string, globalCoherence: number): Promise<void> {
    // Mock global coherence submission
  }

  async processOntology(graph: LFIRGraph, ontologyId: string): Promise<void> {
    // Processar axiomas em batch para eficiência
    for (const edge of graph.edges) {
      const gradient = this.computeAxiomGradient(edge);
      if (Math.abs(gradient) >= 0.01) {
        this.batchBuffer.push({ edge, gradient });

        if (this.batchBuffer.length >= this.BATCH_SIZE) {
          await this.flushBatch();
        }
      }
    }

    // Flush final
    await this.flushBatch();

    // Submeter coerência global
    const rootNode = graph.nodes.find(n => graph.rootNodes.includes(n.id));
    const globalCoherence = rootNode?.attributes['coherence_score'] as number || 0;
    if (globalCoherence > 0.8) {
      await this.submitGlobalCoherence(ontologyId, globalCoherence);
    }
  }

  private async flushBatch(): Promise<void> {
    if (this.batchBuffer.length === 0) return;

    // Agrupar por tipo de axioma para compressão
    const grouped = new Map<string, Array<{ edge: any; gradient: number }>>();
    for (const item of this.batchBuffer) {
      const key = item.edge.relation || 'unknown';
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key)!.push(item);
    }

    // Submeter batch por tipo
    for (const [relation, items] of grouped) {
      const totalGradient = items.reduce((sum, i) => sum + i.gradient, 0);
      await this.channel.submitLocalGradient(
        [totalGradient],
        0.9,
        0.5,
        items.length, // sample count
        0,
        {
          source: 'owl_parser',
          axiom_type: relation,
          batch_size: items.length,
          edges: items.map(i => ({ from: i.edge.from, to: i.edge.to }))
        }
      );
    }

    this.batchBuffer = [];
  }
}
