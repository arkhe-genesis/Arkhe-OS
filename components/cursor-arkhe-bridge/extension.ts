import * as vscode from 'vscode';
import { IDEAndAIParser, IDETool, DevEvent } from '../arkhe-os/parser/frontends/ide_ai_parser';

let activeSessionId: string | null = null;
function getOrCreateSessionId(): string {
    if (!activeSessionId) {
        activeSessionId = 'cursor_session_' + Math.random().toString(36).substring(7);
    }
    return activeSessionId;
}

async function submitToCoherenceChannel(data: any): Promise<void> {}

export function activate(context: vscode.ExtensionContext) {
  const parser = new IDEAndAIParser();
  const eventBuffer: DevEvent[] = [];
  let sessionStart: number | null = null;

  const pushEvent = (eventData: Partial<DevEvent>) => {
      if (!sessionStart) {
          sessionStart = Date.now();
      }
      eventBuffer.push({
          tool: IDETool.CURSOR,
          event_type: 'unknown',
          file_path: '',
          timestamp: Date.now(),
          session_id: getOrCreateSessionId(),
          ...eventData
      } as DevEvent);
  };

  // Capturar eventos de chat do Cursor
  context.subscriptions.push(
    vscode.commands.registerCommand('cursor.chat.message', (msg: any) => {
      pushEvent({
        event_type: msg.role === 'user' ? 'chat_user' : 'chat_assistant',
        file_path: vscode.window.activeTextEditor?.document.uri.fsPath || '',
        content_snippet: msg.content?.slice(0, 200),
        metadata: {
          model: msg.model,
          tokens: msg.usage?.total_tokens,
          latency_ms: msg.latency
        }
      });
    })
  );

  // Capturar aceite/rejeição de sugestões
  context.subscriptions.push(
    vscode.commands.registerCommand('cursor.completion.accepted', (diff: any) => {
      pushEvent({
        event_type: 'completion_accept',
        file_path: diff.filePath,
        content_snippet: diff.newCode?.slice(0, 100),
        metadata: {
          suggestion_id: diff.id,
          lines_added: diff.addedLines,
          lines_removed: diff.removedLines
        }
      });
    })
  );

  // Exportar sessão ao final
  context.subscriptions.push(
    vscode.commands.registerCommand('arkhe.export_session', async () => {
      if (eventBuffer.length === 0) {
        vscode.window.showInformationMessage('Nenhum evento para exportar.');
        return;
      }

      const currentSession = activeSessionId || 'unknown_session';
      const result = parser.parse(
        JSON.stringify(eventBuffer),
        `session/${currentSession}.devlog`
      );

      if (result.success) {
        const durationSec = sessionStart ? (Date.now() - sessionStart) / 1000 : 0;
        // Submeter ao canal de coerência
        await submitToCoherenceChannel({
          artifact_id: `cursor_session:${currentSession}`,
          coherence_delta: result.metrics?.coherenceScore || 0,
          metadata: {
            tool: IDETool.CURSOR,
            event_count: eventBuffer.length,
            duration_sec: durationSec,
            lfir_nodes: result.metrics?.nodesCreated
          }
        });

        vscode.window.showInformationMessage(
          `✅ Sessão exportada: ${result.metrics?.nodesCreated} nós, Φ_C=${(result.metrics?.coherenceScore || 0).toFixed(3)}`
        );
      }

      eventBuffer.length = 0; // Limpar buffer
      sessionStart = null;
      activeSessionId = null; // Reset session ID for next time
    })
  );
}
