// ============================================================================
// ARKHE Ω-TEMP — WebRTC ICE Configuration
// ============================================================================
// Configuração de conectividade P2P. Suporta:
//   - STUN para NAT traversal
//   - TURN relay como fallback
//   - mDNS para rede local
// ============================================================================

export interface IceConfiguration {
  iceServers: RTCIceServer[];
  iceCandidatePoolSize: number;
  iceTransportPolicy: RTCIceTransportPolicy;
  bundlePolicy: RTCBundlePolicy;
  rtcpMuxPolicy: RTCRtcpMuxPolicy;
}

// STUN servers públicos
const STUN_SERVERS = [
  'stun:stun.l.google.com:19302',
  'stun:stun1.l.google.com:19302',
  'stun:stun2.l.google.com:19302',
  'stun:stun3.l.google.com:19302',
  'stun:stun4.l.google.com:19302',
  'stun:stun.arkhe-os.org:3478',       // STARK HE dedicado
  'stun:stun.arkhe-os.org:5349',       // TLS
];

// Configuração padrão para desenvolvimento
export const DEFAULT_ICE_CONFIG: IceConfiguration = {
  iceServers: STUN_SERVERS.map(url => ({ urls: url })),
  iceCandidatePoolSize: 5,
  iceTransportPolicy: 'all',           // Permite relay (TURN) quando necessário
  bundlePolicy: 'max-bundle',          // Otimização: bundle RTP/RTCP
  rtcpMuxPolicy: 'require',             // RTCP multiplexado (WebRTC padrão)
};

// Configuração P2P direta (sem relay) — mais rápida, menos confiável
export const DIRECT_ICE_CONFIG: IceConfiguration = {
  iceServers: STUN_SERVERS.slice(0, 2).map(url => ({ urls: url })),
  iceCandidatePoolSize: 0,
  iceTransportPolicy: 'all',        // Apenas STUN, sem TURN (changed to all to match lib)
  bundlePolicy: 'max-bundle',
  rtcpMuxPolicy: 'require',
};

// Configuração TURN (para NATs restritivos)
export const TURN_ICE_CONFIG = (turnUrl: string, username: string, credential: string): IceConfiguration => ({
  iceServers: [
    ...STUN_SERVERS.map(url => ({ urls: url })),
    {
      urls: turnUrl,                    // e.g., 'turn:turn.arkhe-os.org:3478'
      username: username,
      credential: credential,
    },
  ],
  iceCandidatePoolSize: 5,
  iceTransportPolicy: 'all',
  bundlePolicy: 'max-bundle',
  rtcpMuxPolicy: 'require',
});

// Configuração para produção com TURN dinâmico
export function getProductionIceConfig(): Promise<IceConfiguration> {
  return fetch('/api/v1/ice-config')
    .then(res => res.json())
    .then((data) => ({
      iceServers: data.iceServers,
      iceCandidatePoolSize: data.candidatePoolSize ?? 5,
      iceTransportPolicy: 'all' as RTCIceTransportPolicy,
      bundlePolicy: 'max-bundle' as RTCBundlePolicy,
      rtcpMuxPolicy: 'require' as RTCRtcpMuxPolicy,
    }))
    .catch(() => DEFAULT_ICE_CONFIG);  // Fallback local
}
