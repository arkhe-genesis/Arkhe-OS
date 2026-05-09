export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface AuditFinding {
  id?: string;
  ruleId: string;
  component: string;
  severity: Severity;
  message: string;
  artifact?: string;
}

export interface AuditEvent {
  type: string;
  msiFindingId?: string;
  codeFindingId?: string;
  correlationScore: number;
  evidence: string[];
  timestamp: number;
}

export interface AuditReport {
  timestamp: number;
  totalFindings: number;
  bySeverity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  findings: AuditFinding[];
  metrics?: Record<string, any>;
}
