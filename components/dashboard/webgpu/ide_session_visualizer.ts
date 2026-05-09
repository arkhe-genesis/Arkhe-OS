import { LFIRGraph, LFIRNode } from '../../arkhe-os/parser/lfir';

type vec3 = [number, number, number];

export interface VisualizerConfig {
    animationSpeed: number;
}

// Stubbing external dependencies
export class Renderer {
    addNode(nodeData: any) {}
}

export class LayoutManager {
    computePosition(node: LFIRNode): [number, number] { return [0, 0]; }
}

export class IDESessionVisualizer {
  constructor(private renderer: Renderer, private layout: LayoutManager) {}

  renderSessionGraph(sessionGraph: LFIRGraph, config: VisualizerConfig): void {
    // Mapear tipos de evento para cores perceptuais
    const eventColorMap: Record<string, vec3> = {
      'edit': [0.2, 0.6, 0.9],      // azul
      'save': [0.3, 0.8, 0.3],      // verde
      'completion_accept': [0.9, 0.7, 0.2], // laranja
      'completion_reject': [0.9, 0.3, 0.3], // vermelho
      'agent_action': [0.7, 0.4, 0.9], // roxo
      'diagnostic_error': [1.0, 0.2, 0.2], // vermelho forte
      'diagnostic_fix': [0.2, 0.9, 0.4] // verde claro
    };

    // Renderizar nós com cores baseadas em tipo de evento
    for (const node of sessionGraph.nodes) {
      const eventType = node.attributes['event_type'] as string;
      const baseColor = eventColorMap[eventType] || [0.5, 0.5, 0.5];

      // Modificar brilho baseado em coerência do evento (se disponível)
      const coherence = node.attributes['event_coherence'] as number || 0.5;
      const finalColor = baseColor.map(c => c * (0.5 + coherence * 0.5)) as vec3;

      this.renderer.addNode({
        id: node.id,
        position: this.layout.computePosition(node),
        color: finalColor,
        size: this.computeNodeSize(node),
        tooltip: this.generateTooltip(node)
      });
    }

    // Animar fluxo temporal: partículas percorrendo arestas na ordem dos eventos
    this.animateEventFlow(sessionGraph.edges, config.animationSpeed);
  }

  private computeNodeSize(node: LFIRNode): number {
      return 10; // default size
  }

  private animateEventFlow(edges: any[], speed: number): void {
      // Stub
  }

  private generateTooltip(node: LFIRNode): string {
    return `
      <strong>${node.attributes['event_type']}</strong><br/>
      Arquivo: ${node.attributes['file_path']}<br/>
      Tempo: ${new Date(node.attributes['timestamp']).toLocaleTimeString()}<br/>
      Coerência: ${(node.attributes['event_coherence'] || 0).toFixed(2)}<br/>
      ${node.attributes['content'] ? `<pre>${node.attributes['content']}</pre>` : ''}
    `;
  }
}
