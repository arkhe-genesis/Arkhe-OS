import { LFIRGraph, LFIRNode, LFIRNodeType, ParseResult, ParseMetrics } from '../lfir';

export interface GitModuleConfig {
  name: string;
  path: string;
  url: string;
  ignore?: string;
  branch?: string;
  [key: string]: string | undefined;
}

export class GitModulesFrontend {
  getLanguage(): string { return 'ini'; }
  getExtensions(): string[] { return ['.gitmodules']; }

  parse(source: string, filename: string, superRepoOrigin: string = 'https://github.com/unknown/repo.git'): ParseResult {
    const graph = new LFIRGraph();
    const startTime = Date.now();
    const errors: Array<{code: string; message: string; severity: 'error'|'fatal'}> = [];
    const warnings: Array<{code: string; message: string; suggestion: string}> = [];

    const rootNode = new LFIRNode(`gitmodules/${filename}`, LFIRNodeType.Metadata, 'ini');
    graph.addNode(rootNode);
    graph.rootNodes.push(rootNode.id);

    const modules = this.parseIni(source);

    let nodesCreated = 1;
    let edgesCreated = 0;

    for (const mod of modules) {
      if (!mod.path || !mod.url) {
        warnings.push({
          code: 'MISSING_FIELDS',
          message: `Submodule ${mod.name} is missing path or url`,
          suggestion: 'Ensure both path and url are defined'
        });
        continue;
      }

      // Security: Validate path traversal
      if (this.isPathEscaping(mod.path)) {
        errors.push({
          code: 'PATH_TRAVERSAL',
          message: `Submodule ${mod.name} has a path escaping the repo: ${mod.path}`,
          severity: 'error'
        });
        continue; // Skip node generation to prevent injection
      }

      // Security: Redact tokens from URL
      const safeUrl = this.redactUrlTokens(mod.url);

      // Robustness: Resolve relative URLs mimicking Git's behavior
      const resolvedUrl = this.resolveUrl(safeUrl, superRepoOrigin);

      const modNode = new LFIRNode(`submodule/${mod.name}`, LFIRNodeType.Module, 'git');
      modNode.attributes['path'] = mod.path;
      modNode.attributes['url'] = resolvedUrl;
      if (mod.ignore) modNode.attributes['ignore'] = mod.ignore;
      if (mod.branch) modNode.attributes['branch'] = mod.branch;

      graph.addNode(modNode);
      graph.link(rootNode.id, modNode.id);

      nodesCreated++;
      edgesCreated++;
    }

    const metrics: ParseMetrics = {
      parseTimeMs: Date.now() - startTime,
      nodesCreated,
      edgesCreated,
      maxDepth: 1,
      coherenceScore: 1.0 // Base score, calculated by mapper
    };

    return {
      success: errors.filter(e => e.severity === 'fatal').length === 0,
      graph,
      errors,
      warnings,
      metrics
    };
  }

  private parseIni(source: string): GitModuleConfig[] {
    const lines = source.split(/\r?\n/);
    const modules: GitModuleConfig[] = [];
    let currentModule: Partial<GitModuleConfig> | null = null;

    const sectionRegex = /^\s*\[\s*submodule\s+"([^"]+)"\s*\]\s*$/;
    const kvRegex = /^\s*([a-zA-Z0-9_-]+)\s*=\s*(.+?)\s*$/;

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#') || line.startsWith(';')) continue;

      const sectionMatch = line.match(sectionRegex);
      if (sectionMatch) {
        if (currentModule && currentModule.name) {
          modules.push(currentModule as GitModuleConfig);
        }
        currentModule = { name: sectionMatch[1] };
        continue;
      }

      const kvMatch = line.match(kvRegex);
      if (kvMatch && currentModule) {
        currentModule[kvMatch[1]] = kvMatch[2];
      }
    }

    if (currentModule && currentModule.name) {
      modules.push(currentModule as GitModuleConfig);
    }

    return modules;
  }

  private redactUrlTokens(url: string): string {
    return url.replace(/:\/\/[^@]+@/, '://[REDACTED]@');
  }

  private isPathEscaping(path: string): boolean {
    const parts = path.split('/');
    let depth = 0;
    for (const part of parts) {
      if (part === '..') {
        depth--;
        if (depth < 0) return true;
      } else if (part !== '.' && part !== '') {
        depth++;
      }
    }
    return false;
  }

  private resolveUrl(url: string, superOrigin: string): string {
    if (!url.startsWith('../') && !url.startsWith('./')) {
      return url;
    }

    try {
      const isSsh = superOrigin.startsWith('git@');
      let baseUrl = superOrigin;
      if (isSsh) {
        baseUrl = baseUrl.replace(':', '/');
        baseUrl = 'ssh://' + baseUrl;
      }

      // Mimic git relative path resolution: treat repo name as a file in a directory
      let cleanBase = baseUrl.replace(/\.git$/, '').replace(/\/$/, '');
      if (!cleanBase.endsWith('/')) {
        cleanBase += '/';
      }

      const parsedBase = new URL(cleanBase);
      const newUrl = new URL(url, parsedBase.toString());

      let finalUrl = newUrl.toString();
      if (isSsh) {
        finalUrl = finalUrl.replace('ssh://', '');
        const firstSlash = finalUrl.indexOf('/');
        if (firstSlash !== -1) {
          finalUrl = finalUrl.substring(0, firstSlash) + ':' + finalUrl.substring(firstSlash + 1);
        }
      } else {
        // Append .git back if it's typical https
        if (!finalUrl.endsWith('.git')) {
            finalUrl += '.git';
        }
      }
      return finalUrl;
    } catch (e) {
      return url;
    }
  }
}
