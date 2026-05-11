import { AuditFinding, AuditEvent, Severity } from '../audit/types';
import { CodeAuditChannel } from '../substrates/substrate_258';

export interface CrossArtifactCorrelation {
  msiFinding: AuditFinding;
  codeFinding?: AuditFinding;
  correlationScore: number;
  correlationType: 'direct' | 'indirect' | 'heuristic';
  evidence: string[];
}

export class MSICodeAuditBridge {
  constructor(private auditChannel: CodeAuditChannel) {}

  async correlateFindings(
    msiFindings: AuditFinding[],
    artifactContext: {
      repository?: string;
      commitHash?: string;
      filePaths?: string[];
    }
  ): Promise<CrossArtifactCorrelation[]> {
    const correlations: CrossArtifactCorrelation[] = [];

    for (const msiFinding of msiFindings) {
      if (msiFinding.ruleId === 'MSI-002') {
        const externalFile = msiFinding.component;

        const codeFindings = await this.auditChannel.queryFindings({
          artifact: externalFile,
          repository: artifactContext.repository,
          severity: ['medium', 'high', 'critical']
        });

        for (const codeFinding of codeFindings) {
          const correlation: CrossArtifactCorrelation = {
            msiFinding,
            codeFinding,
            correlationScore: this._computeCorrelationScore(msiFinding, codeFinding),
            correlationType: 'direct',
            evidence: [
              `MSI Custom Action '${msiFinding.component}' references external code`,
              `Code audit found ${codeFinding.severity} vulnerability in ${codeFinding.artifact}`,
              `Potential attack vector: malicious installer -> vulnerable component`
            ]
          };
          correlations.push(correlation);
        }
      }

      if (msiFinding.ruleId === 'MSI-001') {
        const orphanComponents = await this.auditChannel.queryOrphanComponents({
          repository: artifactContext.repository,
          commitHash: artifactContext.commitHash
        });

        const heuristicMatch = orphanComponents.find(
          c => c.name.toLowerCase().includes(msiFinding.component.toLowerCase())
        );

        if (heuristicMatch) {
          correlations.push({
            msiFinding,
            codeFinding: {
              ruleId: 'CODE-ORPHAN',
              artifact: heuristicMatch.path,
              severity: 'low',
              message: `Component may be orphaned in source control`,
              component: heuristicMatch.name
            },
            correlationScore: 0.6,
            correlationType: 'heuristic',
            evidence: [
              `MSI component '${msiFinding.component}' lacks KeyPath`,
              `Source control shows similar file '${heuristicMatch.path}' with low commit activity`,
              `Risk: component may be unmaintained or deprecated`
            ]
          });
        }
      }

      if (msiFinding.ruleId === 'MSI-003') {
        const sharedComponent = msiFinding.component;
        const match = msiFinding.message.match(/'([^']+)'/);
        const fileName = match ? match[1] : undefined;

        const versionConflicts = await this.auditChannel.queryVersionConflicts({
          fileName,
          repository: artifactContext.repository
        });

        if (versionConflicts.length > 0) {
          correlations.push({
            msiFinding,
            codeFinding: versionConflicts[0],
            correlationScore: 0.85,
            correlationType: 'indirect',
            evidence: [
              `Unversioned file in shared MSI component`,
              `Code repository shows ${versionConflicts.length} conflicting versions`,
              `Risk: DLL Hell / version mismatch at runtime`
            ]
          });
        }
      }
    }

    for (const corr of correlations) {
      await this.auditChannel.emitCorrelationEvent({
        type: 'msi_code_correlation',
        msiFindingId: corr.msiFinding.id,
        codeFindingId: corr.codeFinding?.id,
        correlationScore: corr.correlationScore,
        evidence: corr.evidence,
        timestamp: Date.now()
      });
    }

    return correlations;
  }

  private _computeCorrelationScore(msi: AuditFinding, code: AuditFinding): number {
    const severityWeight: Record<Severity, number> = {
      'critical': 1.0,
      'high': 0.8,
      'medium': 0.5,
      'low': 0.2
    };

    const msiWeight = severityWeight[msi.severity] || 0.3;
    const codeWeight = severityWeight[code.severity] || 0.3;

    return Math.max(msiWeight, codeWeight) * 0.7 + (msiWeight + codeWeight) / 2 * 0.3;
  }
}
