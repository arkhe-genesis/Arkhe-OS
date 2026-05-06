// src/core/parser.ts — IDEAndAIParser Minimal para MVP
import * as vscode from 'vscode';
import { DevEvent, IDETool, LFIRGraph, LFIRNode } from '../types/lfir';
import { redactSecrets, hashPath } from './privacy';

export class MinimalIDEParser {
  private config: ParserConfig;
  private eventBuffer: DevEvent[] = [];
  private sessionStart: number | null = null;

  constructor(config: Partial<ParserConfig> = {}) {
    this.config = {
      redact_content: true,
      hash_file_paths: true,
      sample_rate: 1.0,
      retention_days: 7,
      opt_out_events: [],
      ...config
    };
  }

  /**
   * Captura evento de edição/save com privacidade por padrão
   */
  async captureEvent(
    event: vscode.TextDocumentChangeEvent | vscode.TextDocument,
    eventType: 'edit' | 'save' | 'completion_accept' | 'diagnostic_fix'
  ): Promise<DevEvent | null> {
    const doc = 'document' in event ? event.document : event;

    // Verificar opt-out por tipo de evento
    if (this.config.opt_out_events?.includes(eventType)) {
      return null;
    }

    // Redação automática de conteúdo sensível
    const content = this.config.redact_content
      ? await redactSecrets(doc.getText())
      : doc.getText().slice(0, 200); // Limitar snippet

    // Hash de path para privacidade
    const fileRef = this.config.hash_file_paths
      ? await hashPath(doc.uri.fsPath)
      : doc.uri.fsPath;

    const devEvent: DevEvent = {
      tool: IDETool.VS_CODE,
      event_type: eventType,
      file_path: fileRef,
      content_snippet: content,
      timestamp: Date.now(),
      session_id: this.getSessionId(),
      metadata: {
        language: doc.languageId,
        line_count: doc.lineCount,
        event_source: 'vscode_extension_mvp'
      }
    };

    // Buffer em memória com flush periódico
    this.eventBuffer.push(devEvent);
    if (this.eventBuffer.length >= 50) {
      await this.flushBuffer();
    } else if (this.eventBuffer.length === 1) {
      // Start 30 seconds timer if it's the first event in the buffer
      setTimeout(() => {
        this.flushBuffer();
      }, 30000);
    }

    return devEvent;
  }

  /**
   * Converte evento para nó LFIR minimal
   */
  toLFIRNode(event: DevEvent): LFIRNode {
    return {
      id: `evt_${event.timestamp}_${event.event_type}`,
      type: 'DevEvent',
      attributes: {
        tool: event.tool,
        event_type: event.event_type,
        file_ref: event.file_path,
        timestamp: event.timestamp,
        session_id: event.session_id,
        // Coerência local simplificada para MVP
        local_coherence: this.computeLocalCoherence(event)
      },
      edges: []
    };
  }

  /**
   * Cálculo simplificado de coerência para MVP
   * - save > edit (intenção consolidada)
   * - completion_accept > completion_reject (IA útil)
   * - diagnostic_fix > diagnostic_error (progresso)
   */
  private computeLocalCoherence(event: DevEvent): number {
    const weights: Record<string, number> = {
      'save': 0.8,
      'edit': 0.3,
      'completion_accept': 0.7,
      'completion_reject': 0.1,
      'diagnostic_fix': 0.9,
      'diagnostic_error': 0.2
    };
    return weights[event.event_type] ?? 0.5;
  }

  /**
   * Flush do buffer para o endpoint configurado
   */
  private async flushBuffer(): Promise<void> {
    if (this.eventBuffer.length === 0) return;

    const endpoint = vscode.workspace.getConfiguration('arkhe.ide_parser')
      .get('endpoint', 'ws://localhost:8080/ide-events');

    try {
      // Enviar via WebSocket ou fallback HTTP
      await this.sendEvents(this.eventBuffer, endpoint as string);
      this.eventBuffer = [];
    } catch (error) {
      // Log local sem bloquear a experiência do desenvolvedor
      console.warn('[ARKHE] Failed to flush events:', error);
    }
  }

  private getSessionId(): string {
    if (!this.sessionStart) {
      this.sessionStart = Date.now();
    }
    return `vscode_session_${this.sessionStart}_${process.pid}`;
  }

  private async sendEvents(events: DevEvent[], endpoint: string): Promise<void> {
    // Implementação WebSocket minimal para MVP
    return new Promise((resolve) => {
      // Em produção: usar cliente WebSocket robusto com reconexão
      resolve();
    });
  }
}

interface ParserConfig {
  redact_content: boolean;
  hash_file_paths: boolean;
  sample_rate: number;
  retention_days: number;
  opt_out_events?: string[];
}
