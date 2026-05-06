import { LFIRGraph, LFIRNode, LFIRNodeType, ParseResult, ParseMetrics } from '../lfir.js';

export enum IDETool {
  VS_CODE = 'vscode',
  CURSOR = 'cursor',
  ANTIGRAVITY = 'antigravity',
  CLAUDE_CODE = 'claude_code'
}

export interface DevEvent {
  tool: IDETool;
  event_type: string;      // "edit", "save", "completion_accept", "agent_action", ...
  file_path: string;
  content_snippet?: string;
  timestamp: number;
  session_id: string;
  metadata?: Record<string, unknown>;
}

export class IDEAndAIParser {
  getLanguage(): string { return 'dev-tools'; }
  getExtensions(): string[] { return ['.devlog', '.session', '.agent-trace']; }

  parse(source: string, filename: string): ParseResult {
    const graph = new LFIRGraph();
    const startTime = Date.now();

    try {
      // Detecta formato baseado no conteúdo ou extensão
      const payload = JSON.parse(source);
      const events: DevEvent[] = Array.isArray(payload) ? payload : payload.events;

      const sessionNode = new LFIRNode(
        `session/${payload.session_id || filename}`,
        LFIRNodeType.Module,
        'dev-tools'
      );
      sessionNode.attributes['tool'] = detectTool(events);
      sessionNode.attributes['event_count'] = events.length;
      sessionNode.attributes['duration_sec'] = events.length > 1
        ? (events[events.length - 1].timestamp - events[0].timestamp) / 1000 : 0;
      graph.addNode(sessionNode);
      graph.rootNodes.push(sessionNode.id);

      // Criar nós para cada evento
      let lastNodeId = sessionNode.id;
      for (const event of events) {
        const eventNode = new LFIRNode(
          `event/${event.session_id}_${event.timestamp}`,
          mapEventToLFIRType(event.event_type),
          event.tool
        );
        eventNode.attributes['event_type'] = event.event_type;
        eventNode.attributes['file_path'] = event.file_path;
        eventNode.attributes['timestamp'] = event.timestamp;
        if (event.content_snippet) eventNode.attributes['content'] = event.content_snippet.slice(0, 100);
        if (event.metadata) Object.assign(eventNode.attributes, event.metadata);
        graph.addNode(eventNode);
        graph.link(lastNodeId, eventNode.id);
        lastNodeId = eventNode.id;
      }

      // Calcular coerência da sessão
      const coherence = this.computeSessionCoherence(events);
      sessionNode.attributes['coherence_score'] = coherence;

      return {
        success: true,
        graph,
        errors: [],
        warnings: [],
        metrics: {
          parseTimeMs: Date.now() - startTime,
          nodesCreated: graph.nodes.length,
          edgesCreated: graph.edges.length,
          maxDepth: graph.nodes.length + 1,
          coherenceScore: coherence
        }
      };

    } catch (err) {
      return {
        success: false,
        graph: null,
        errors: [{ code: 'PARSE_ERROR', message: String(err), severity: 'fatal' }],
        warnings: [],
        metrics: { parseTimeMs: Date.now() - startTime, nodesCreated: 0, edgesCreated: 0, maxDepth: 0, coherenceScore: 0 }
      };
    }
  }

  private computeSessionCoherence(events: DevEvent[]): number {
    if (events.length === 0) return 0;
    let score = 0;
    const weights: Record<string, number> = {
      'edit': 0.5, 'save': 0.8, 'completion_accept': 0.7,
      'completion_reject': -0.2, 'agent_action': 0.9,
      'diagnostic_error': -0.5, 'diagnostic_fix': 0.6
    };
    for (const event of events) {
      score += weights[event.event_type] || 0.1;
    }
    return Math.max(0, Math.min(1, score / events.length + 0.3));
  }
}

function detectTool(events: DevEvent[]): IDETool {
  if (events.length === 0) return IDETool.VS_CODE;
  return events[0].tool;
}

function mapEventToLFIRType(eventType: string): LFIRNodeType {
  switch (eventType) {
    case 'edit': case 'save': return LFIRNodeType.Operation;
    case 'completion_accept': case 'completion_reject': return LFIRNodeType.Operation;
    case 'agent_action': return LFIRNodeType.Module;
    case 'diagnostic_error': case 'diagnostic_fix': return LFIRNodeType.Metadata;
    default: return LFIRNodeType.Type;
  }
}
