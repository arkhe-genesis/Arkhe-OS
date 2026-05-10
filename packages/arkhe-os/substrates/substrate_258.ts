import { AuditFinding, AuditEvent } from '../audit/types';

export class CodeAuditChannel {
  async queryFindings(query: any): Promise<AuditFinding[]> {
    return [];
  }

  async queryOrphanComponents(query: any): Promise<any[]> {
    return [];
  }

  async queryVersionConflicts(query: any): Promise<AuditFinding[]> {
    return [];
  }

  async emitCorrelationEvent(event: AuditEvent): Promise<void> {
  }
}
