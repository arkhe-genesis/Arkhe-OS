import { GitModulesFrontend } from '../parser/frontends/gitmodules_frontend';
import { GitModulesCoherenceMapper } from './gitmodules_coherence_mapper';
import { LFIRNodeType } from '../parser/lfir';

describe('GitModules Integration', () => {
  const sampleGitmodules = `
[submodule "good-module"]
	path = good-module
	url = https://github.com/org/good-module.git
[submodule "old-module"]
	path = old-module
	url = ../old-repo.git
[submodule "ignored-module"]
	path = ignored-module
	url = https://github.com/org/ignore.git
	ignore = all
[submodule "secure-module"]
	path = secure-module
	url = https://token:secret@github.com/org/secure.git
[submodule "escaped-module"]
	path = ../../escaped
	url = https://github.com/org/bad.git
[submodule "broken-module"]
	path = broken-path
	url = https://github.com/org/broken.git
`;

  it('should parse INI syntax correctly, sanitize URLs and prevent path traversal', () => {
    const frontend = new GitModulesFrontend();
    const result = frontend.parse(sampleGitmodules, '.gitmodules', 'https://github.com/super/repo.git');

    expect(result.success).toBe(true);
    expect(result.graph).not.toBeNull();

    const graph = result.graph!;
    const modules = graph.nodes.filter(n => n.type === LFIRNodeType.Module);

    // We expect 5 modules (escaped-module should be skipped due to path traversal error)
    expect(modules.length).toBe(5);

    // Path traversal check
    const escapedModule = modules.find(m => m.id === 'submodule/escaped-module');
    expect(escapedModule).toBeUndefined();
    expect(result.errors.some(e => e.code === 'PATH_TRAVERSAL')).toBe(true);

    // Token redaction check
    const secureModule = modules.find(m => m.id === 'submodule/secure-module');
    expect(secureModule?.attributes['url']).toBe('https://[REDACTED]@github.com/org/secure.git');

    // Relative URL check
    const oldModule = modules.find(m => m.id === 'submodule/old-module');
    expect(oldModule?.attributes['url']).toBe('https://github.com/super/old-repo.git');
  });

  it('should calculate coherence using parallel checks and generate audit logs', async () => {
    const frontend = new GitModulesFrontend();
    const result = frontend.parse(sampleGitmodules, '.gitmodules', 'https://github.com/super/repo.git');
    const graph = result.graph!;

    const mapper = new GitModulesCoherenceMapper();

    // Mock the external calls
    mapper.checkUrlReachabilityFn = async (url: string) => {
      return !url.includes('broken');
    };

    mapper.execCommand = (async (cmd: string): Promise<{ stdout: string, stderr: string }> => {
      if (cmd.includes('broken-path')) {
        throw new Error('git command failed');
      }
      if (cmd.includes('old-module')) {
        // Return 45 days ago
        const ts = Math.floor(Date.now() / 1000) - (45 * 24 * 60 * 60);
        return { stdout: ts.toString(), stderr: '' };
      }
      // Return 5 days ago
      const ts = Math.floor(Date.now() / 1000) - (5 * 24 * 60 * 60);
      return { stdout: ts.toString(), stderr: '' };
    }) as any;

    await mapper.processLFIRGraph(graph);

    const modules = graph.nodes.filter(n => n.type === LFIRNodeType.Module);

    // good-module: healthy
    const goodModule = modules.find(m => m.id === 'submodule/good-module');
    expect(goodModule?.attributes['coherence_score']).toBe(1.0);

    // old-module: drift=45d -> score math.max(0.2, 1.0 - 0.45) = 0.55
    const oldModule = modules.find(m => m.id === 'submodule/old-module');
    expect(oldModule?.attributes['coherence_score']).toBeCloseTo(0.55);

    // ignored-module: score=1.0 intentionally
    const ignoredModule = modules.find(m => m.id === 'submodule/ignored-module');
    expect(ignoredModule?.attributes['coherence_score']).toBe(1.0);

    // broken-module: fallback heuristic
    const brokenModule = modules.find(m => m.id === 'submodule/broken-module');
    expect(brokenModule?.attributes['coherence_score']).toBe(0.5);

    // Verify audit logs
    const logs = mapper.getAuditLogs();
    expect(logs.length).toBe(5);

    const oldLog = logs.find(l => l.submodule === 'submodule/old-module');
    expect(oldLog?.reason).toContain('drift=45d');
    expect(oldLog?.reason).toContain('\u2192'); // checks for the arrow logging requirement
  });
});
