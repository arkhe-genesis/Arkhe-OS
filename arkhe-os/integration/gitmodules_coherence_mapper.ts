import { LFIRGraph, LFIRNode, LFIRNodeType } from '../parser/lfir';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as http from 'http';
import * as https from 'https';

const execPromise = promisify(exec);

export interface CoherenceLog {
  submodule: string;
  drift: string | number;
  score: number;
  reason: string;
}

export class GitModulesCoherenceMapper {
  private urlReachabilityCache: Map<string, boolean> = new Map();
  private auditLogs: CoherenceLog[] = [];

  // Expose these for testing/mocking
  public execCommand = execPromise;
  public checkUrlReachabilityFn = this.performUrlReachability.bind(this);

  async processLFIRGraph(graph: LFIRGraph): Promise<void> {
    const modulesNodes = graph.nodes.filter(
      n => n.type === LFIRNodeType.Module && n.id.startsWith('submodule/')
    );

    // Promise.all to perform checks in parallel as requested
    await Promise.all(
      modulesNodes.map(node => this.evaluateSubmoduleCoherence(node))
    );

    // Update global graph score
    if (modulesNodes.length > 0) {
      const validNodes = modulesNodes.filter(n => n.attributes['ignore'] !== 'all');
      const totalScore = validNodes.reduce((acc, curr) => acc + (curr.attributes['coherence_score'] || 0), 0);

      const averageCoherence = validNodes.length > 0 ? totalScore / validNodes.length : 1.0;

      const rootNode = graph.nodes.find(n => n.id.startsWith('gitmodules/'));
      if (rootNode) {
        rootNode.attributes['global_coherence'] = averageCoherence;
      }
    }
  }

  getAuditLogs(): CoherenceLog[] {
    return this.auditLogs;
  }

  private async evaluateSubmoduleCoherence(node: LFIRNode): Promise<void> {
    if (node.attributes['ignore'] === 'all') {
      node.attributes['coherence_score'] = 1.0; // Ignored deliberately
      this.auditLogs.push({
        submodule: node.id,
        drift: 0,
        score: 1.0,
        reason: 'Ignored intentionally (ignore=all)'
      });
      return;
    }

    const url = node.attributes['url'] as string;
    let score = 1.0;
    let reason = '';

    try {
      // Parallel checks inside node evaluation
      const [isReachable, driftDays] = await Promise.all([
        this.checkUrlReachabilityFn(url),
        this.checkDrift(node.attributes['path'] as string)
      ]);

      if (!isReachable) {
        score = 0.0;
        reason = `URL unreachable: ${url}`;
      } else if (driftDays > 30) {
        // Linear decay for drift
        score = Math.max(0.2, 1.0 - (driftDays / 100));
        reason = `drift=${driftDays}d \u2192 fator ${score.toFixed(2)}`;
      } else {
        score = 1.0;
        reason = `Healthy connection, drift=${driftDays}d`;
      }

      node.attributes['coherence_score'] = score;
      node.attributes['drift_days'] = driftDays;

      this.auditLogs.push({
        submodule: node.id,
        drift: driftDays,
        score,
        reason
      });

    } catch (e) {
      // Fallback for heuristic coherence if git commands fail
      score = 0.5;
      reason = 'Heuristic fallback (commands failed)';
      node.attributes['coherence_score'] = score;
      this.auditLogs.push({
        submodule: node.id,
        drift: 'unknown',
        score,
        reason
      });
    }
  }

  private async performUrlReachability(url: string): Promise<boolean> {
    if (!url) return false;
    // Assume git@ is reachable as we don't SSH probe in this lightweight step
    if (url.startsWith('git@') || url.startsWith('ssh://')) return true;

    if (this.urlReachabilityCache.has(url)) {
      return this.urlReachabilityCache.get(url)!;
    }

    return new Promise((resolve) => {
      try {
        const client = url.startsWith('https') ? https : http;
        // Strip .git for pure HEAD request
        const requestUrl = url.replace(/\.git$/, '');

        const req = client.request(requestUrl, { method: 'HEAD', timeout: 5000 }, (res) => {
          // 2xx, 3xx are fine. 401/403 also fine (private repo)
          const isReachable = res.statusCode ? res.statusCode < 500 : false;
          this.urlReachabilityCache.set(url, isReachable);
          resolve(isReachable);
        });

        req.on('error', () => {
          this.urlReachabilityCache.set(url, false);
          resolve(false);
        });

        req.on('timeout', () => {
          req.destroy();
          this.urlReachabilityCache.set(url, false);
          resolve(false);
        });

        req.end();
      } catch (err) {
        resolve(false);
      }
    });
  }

  private async checkDrift(path: string): Promise<number> {
    // Real git check: determine days since last commit in submodule vs HEAD
    // Using simple `git log -1 --format=%ct` in submodule
    try {
      // Avoid arbitrary command execution (Command Injection prevention)
      if (!/^[a-zA-Z0-9_\-\.\/]+$/.test(path) || path.includes('..')) {
        throw new Error('Invalid path for git command');
      }

      // Check commit date
      const { stdout } = await this.execCommand(`git -C ${path} log -1 --format=%ct`);
      const commitTimestamp = parseInt(stdout.trim(), 10);

      if (isNaN(commitTimestamp)) {
        throw new Error('Invalid commit timestamp');
      }

      const now = Math.floor(Date.now() / 1000);
      const diffSeconds = now - commitTimestamp;
      const diffDays = Math.max(0, Math.floor(diffSeconds / (60 * 60 * 24)));
      return diffDays;
    } catch (err) {
      throw new Error(`Git command failed for path: ${path}`);
    }
  }
}
