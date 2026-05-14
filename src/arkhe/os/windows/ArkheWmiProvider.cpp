// ============================================================================
// ArkheWmiProvider.cpp — WMI Provider para telemetria ASI
// Expõe métricas Φ_C, π, e status de governança via WMI.
// ============================================================================
// Namespace: ROOT\Arkhe
// Classes:
//   Arkhe_GovernanceStatus (Φ_C, π, NodesActive, LastPingTimestamp)
//   Arkhe_FileIntegrity (Path, Seal, LastVerified, Status)
//   Arkhe_MeshPeer (NodeId, PhiC, LatencyMs, PacketsSealed)

// Exemplo de consulta WMI:
// Get-WmiObject -Namespace ROOT\Arkhe -Class Arkhe_GovernanceStatus
