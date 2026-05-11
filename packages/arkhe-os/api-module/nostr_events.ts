// arkhe-os/api-module/nostr_events.ts
// Substrato Nostr Distribution Layer

export type ArkheEventKind =
  | 1634  // NIP-34: Git Pull Request
  | 30078 // NIP-78: Application-specific data (coherence reports)
  | 30315 // NIP-315: Git commit with coherence signature
  | 9001  // Custom: Coherence verification result
  | 9002; // Custom: Meta-self emergence notification

export interface ArkheCommitEvent {
  kind: 30315;
  pubkey: string;        // npub do autor
  created_at: number;
  tags: [
    ["h", "htree"],      // Protocol identifier
    ["r", string],       // Repo reference e.g. "npub1.../arkhe-os"
    ["commit", string],  // Commit hash
    ["coherence", string], // Φ_C do commit e.g. "0.942"
    ["seal", string]     // Selo canônico do ARKHE
  ];
  content: string;       // Mensagem do commit + metadata JSON
  sig: string;           // Assinatura criptográfica
}

export interface CoherenceReportEvent {
  kind: 9001;
  pubkey: string;        // npub do runner
  created_at: number;
  tags: [
    ["e", string],       // Referência ao PR sendo verificado
    ["runner", string],  // e.g. "coherence-guardian-v1"
    ["result", "pass" | "fail"],
    ["global_coherence", string]
  ];
  content: string;       // JSON com métricas detalhadas
  sig: string;
}
