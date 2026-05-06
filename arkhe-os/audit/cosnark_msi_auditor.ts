import { createHash } from 'crypto';
// @ts-ignore
import { groth16 } from 'snarkjs';
import { AuditReport, AuditFinding, Severity } from './types';

export interface CoSNARKProof {
  proof: string;
  publicSignals: string[];
  verificationKey: string;
}

export class CoSNARKMSIAuditor {
  private readonly CIRCUIT_NAME = 'msi_audit_report_v1';
  private readonly PROVER_KEY: string;
  private readonly VERIFICATION_KEY: string;

  constructor(proverKey: string, verificationKey: string) {
    this.PROVER_KEY = proverKey;
    this.VERIFICATION_KEY = verificationKey;
  }

  async signReport(report: AuditReport, signerId: string): Promise<CoSNARKProof> {
    const publicInputs = this._preparePublicInputs(report, signerId);
    const privateInputs = this._preparePrivateInputs(report);

    const proof = await groth16.prove(
      `${this.CIRCUIT_NAME}_prover.zkey`,
      { ...publicInputs, ...privateInputs }
    );

    return {
      proof: Buffer.from(proof.proof).toString('hex'),
      publicSignals: proof.publicSignals.map((s: string) => BigInt(s).toString(16)),
      verificationKey: this.VERIFICATION_KEY
    };
  }

  async verifyProof(proof: CoSNARKProof, expectedReportHash: string): Promise<boolean> {
    return await groth16.verify(
      JSON.parse(proof.verificationKey),
      [expectedReportHash, ...proof.publicSignals],
      proof.proof
    );
  }

  private _preparePublicInputs(report: AuditReport, signerId: string): Record<string, any> {
    const findingsHash = this._computeMerkleRoot(report.findings);

    return {
      report_hash: findingsHash,
      signer_id: this._hashSigner(signerId),
      timestamp: Math.floor(report.timestamp / 1000),
      total_findings: report.totalFindings,
      critical_count: report.bySeverity.critical,
      high_count: report.bySeverity.high
    };
  }

  private _preparePrivateInputs(report: AuditReport): Record<string, any> {
    return {
      findings_details: report.findings.map(f => ({
        rule_id: f.ruleId,
        component: f.component,
        severity: this._severityToEnum(f.severity)
      })),
      raw_metrics: report.metrics || {}
    };
  }

  private _computeMerkleRoot(findings: AuditFinding[]): string {
    const leaves = findings.map(f =>
      createHash('sha256').update(`${f.ruleId}:${f.component}:${f.severity}`).digest('hex')
    );
    if (leaves.length === 0) return createHash('sha256').update('').digest('hex');

    let level = leaves;
    while (level.length > 1) {
      const nextLevel: string[] = [];
      for (let i = 0; i < level.length; i += 2) {
        const left = level[i];
        const right = level[i + 1] || left;
        nextLevel.push(
          createHash('sha256').update(left + right).digest('hex')
        );
      }
      level = nextLevel;
    }
    return level[0];
  }

  private _hashSigner(signerId: string): string {
    return createHash('sha256').update(signerId).digest('hex').slice(0, 16);
  }

  private _severityToEnum(severity: Severity): number {
    return { 'low': 0, 'medium': 1, 'high': 2, 'critical': 3 }[severity] || 0;
  }
}
