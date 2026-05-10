import { IDEAndAIParser, DevEvent } from '../parser/frontends/ide_ai_parser';
// Stubbing GitCoherenceMapper and submitToCoherenceChannel for compilation based on prompt schema
export class GitCoherenceMapper {
    async parseFileHistory(repoPath: string, file: string): Promise<{coherence: number, commits: any[]}> {
        return { coherence: 0.8, commits: [] };
    }
}
async function submitToCoherenceChannel(data: any): Promise<void> {}

export class IDEGitBridge {
  constructor(
    private ideParser: IDEAndAIParser,
    private gitMapper: GitCoherenceMapper
  ) {}

  async onSessionEnd(sessionEvents: DevEvent[], repoPath: string): Promise<void> {
    if (!sessionEvents || sessionEvents.length === 0) return;

    // 1. Parse sessão IDE -> LFIR
    const result = this.ideParser.parse(
      JSON.stringify(sessionEvents),
      `session/${sessionEvents[0].session_id}`
    );

    if (!result.success || !result.graph) return;
    const ideGraph = result.graph;

    // 2. Extrair arquivos modificados da sessão
    const modifiedFiles = new Set<string>(
      sessionEvents
        .filter(e => e.event_type === 'save' || e.event_type === 'edit')
        .map(e => e.file_path)
    );

    // 3. Para cada arquivo, mapear commits recentes -> coerência Git
    for (const file of modifiedFiles) {
      const gitGraph = await this.gitMapper.parseFileHistory(repoPath, file);

      // 4. Calcular delta de coerência: IDE session vs Git history
      const ideCoherence = ideGraph.nodes[0]?.attributes['coherence_score'] || 0;
      const gitCoherence = gitGraph.coherence || 0;
      const delta = ideCoherence - gitCoherence;

      // 5. Submeter ao canal de coerência se delta significativo
      if (Math.abs(delta) > 0.05) {
        await submitToCoherenceChannel({
          artifact_id: `session:${sessionEvents[0].session_id}:file:${file}`,
          coherence_delta: delta,
          metadata: {
            ide_tool: sessionEvents[0].tool,
            event_count: sessionEvents.length,
            git_commits: gitGraph.commits?.length || 0,
            timestamp: Date.now()
          }
        });
      }
    }
  }
}
