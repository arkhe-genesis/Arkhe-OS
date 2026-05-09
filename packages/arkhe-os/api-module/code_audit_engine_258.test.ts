import { CodeAuditEngine, AuditConfig } from './code_audit_engine';

describe('Code Audit Engine (Substrate 258)', () => {
  it('should run audit and generate valid report based on config', async () => {
    const engine = new CodeAuditEngine();

    const config: AuditConfig = {
      sourcePath: './meu-projeto',
      globalThreshold: 0.80,
      localThreshold: 0.80
    };

    const report = await engine.runAudit(config);

    expect(report).toBeDefined();
    expect(report.repository).toBe('meu-projeto');
    expect(report.passed).toBe(true);
    expect(report.globalCoherence).toBeGreaterThanOrEqual(config.globalThreshold);
    expect(report.findings.length).toBe(2);
    expect(report.zincProof.valid).toBe(true);
    expect(report.octraTxHash).toBeDefined();
  });
});
