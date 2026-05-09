// arkhe-os/parser/frontends/owl_frontend.ts
// @ts-ignore
import { Reasoner, Configuration as ReasonerConfig } from 'owl-reasoner-lite';
import { LFIRGraph, LFIRNode, ParseResult as BaseParseResult, LFIRNodeType } from '../lfir';
// @ts-ignore
import * as N3 from 'n3';

export interface OWLParseResult extends BaseParseResult {
  graph: LFIRGraph;
  errors: any[];
  warnings: any[];
}

export class OWLFrontend {
  private reasoner: Reasoner | null = null;

  constructor(private reasonerConfig?: ReasonerConfig) {
    if (reasonerConfig?.enableReasoning) {
      this.reasoner = new Reasoner(reasonerConfig);
    }
  }

  // Base parsing mocked out as per requirements/capabilities
  protected async baseParse(source: string | Buffer, filename: string): Promise<OWLParseResult> {
    const graph = new LFIRGraph();
    const rootNode: LFIRNode = {
      id: `ontology/${filename}`,
      type: LFIRNodeType.Module,
      sourceLang: 'owl',
      attributes: {
        coherence_score: 1.0,
      }
    };
    graph.addNode(rootNode);
    graph.rootNodes.push(rootNode.id);

    const parser = new N3.Parser();
    const sourceString = typeof source === 'string' ? source : source.toString('utf-8');

    let errors: any[] = [];
    try {
      const quads = parser.parse(sourceString);
      rootNode.attributes['parsed_quads'] = quads.length;
    } catch (e: any) {
      errors.push({ code: 'RDF_PARSE_ERROR', message: e.message, severity: 'fatal' });
    }

    return {
      success: errors.length === 0,
      graph,
      errors,
      warnings: [],
      metrics: {
        parseTimeMs: 10,
        nodesCreated: 1,
        edgesCreated: 0,
        maxDepth: 1,
        coherenceScore: 1.0
      }
    };
  }

  protected encodeIRI(iri: string): string {
    return encodeURIComponent(iri);
  }

  async parse(source: string | Buffer, filename: string): Promise<OWLParseResult> {
    const result = await this.baseParse(source, filename);

    // Reasoning pós-parse se habilitado
    if (this.reasoner && result.success) {
      const reasoningResult = await this.reasoner.checkConsistency(result.graph);

      if (!reasoningResult.consistent) {
        result.warnings.push({
          code: 'ONTOLOGY_INCONSISTENCY',
          message: `Inconsistências detectadas: ${reasoningResult.explanations.join('; ')}`,
          severity: 'warning'
        });
        // Ajustar coerência para refletir inconsistência
        result.graph.nodes.find((n: LFIRNode) => n.id === result.graph.rootNodes[0])!.attributes['coherence_score'] *= 0.5;
      }

      // Inferir subsumptions não explícitas
      const inferredSubs = await this.reasoner.inferSubClassOf(result.graph);
      for (const { sub, sup } of inferredSubs) {
        result.graph.edges.push({
          from: `class/${this.encodeIRI(sub)}`,
          to: `class/${this.encodeIRI(sup)}`,
          // @ts-ignore - appending relations specific to owl edge type extensions
          relation: 'subClassOf',
          weight: 0.6, // Peso menor para inferidas vs. explícitas
          inferred: true
        });
      }
    }

    return result;
  }
}
