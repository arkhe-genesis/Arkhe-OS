import * as vscode from 'vscode';
import { MinimalIDEParser } from './core/parser';

export function activate(context: vscode.ExtensionContext) {
  const parser = new MinimalIDEParser();

  // Registrar comando de exportação
  let disposable = vscode.commands.registerCommand('arkhe.export_session', () => {
    vscode.window.showInformationMessage('ARKHE: Exportando sessão de coerência...');
    // A exportação completa será implementada em fases futuras
  });
  context.subscriptions.push(disposable);

  // Escutar eventos de salvamento
  vscode.workspace.onDidSaveTextDocument(async (document) => {
    const config = vscode.workspace.getConfiguration('arkhe.ide_parser');
    if (!config.get('enabled', true)) return;

    const eventsToCapture = config.get<string[]>('events', []);
    if (eventsToCapture.includes('workspace.didSaveTextDocument')) {
      await parser.captureEvent(document, 'save');
    }
  }, null, context.subscriptions);

  // Escutar eventos de completion (aceitação de completion é algo mais complexo no VSCode,
  // mas podemos simular ou usar vscode.workspace.onDidChangeTextDocument como aproximação
  // para o MVP se inline completions estiverem em uso. Como o MVP exige apenas o evento:
  // a forma recomendada em extensões novas é com inlineCompletionProvider se for a própria ext,
  // ou escutando a command palette se a IA expõe um comando).
  // Para MVP vamos deixar o evento preparado e usar document change como trigger de edição normal.
  vscode.workspace.onDidChangeTextDocument(async (event) => {
    const config = vscode.workspace.getConfiguration('arkhe.ide_parser');
    if (!config.get('enabled', true)) return;

    const eventsToCapture = config.get<string[]>('events', []);
    // Tratando como edição normal
    if (eventsToCapture.includes('completion.accepted') && event.contentChanges.length > 0) {
      // Simplificação do MVP: Se uma edição for grande (> 20 chars adicionados de uma vez),
      // classificar como possível completion ou paste
      const isCompletionOrPaste = event.contentChanges.some(c => c.text.length > 20);
      if (isCompletionOrPaste) {
         await parser.captureEvent(event.document, 'completion_accept');
      } else {
         await parser.captureEvent(event.document, 'edit');
      }
    }
  }, null, context.subscriptions);

  console.log('ARKHE OS IDE Parser activated');
}

export function deactivate() {}
