# 🛰️ Arkhe Satellite PXE — Deploy Remoto via Rede de Satélites

## Visão Geral
Arkhe Satellite PXE permite boot e instalação de ArkheOS em locais remotos sem infraestrutura terrestre, utilizando constelações de satélites (Starlink, OneWeb) para entrega de imagens bootáveis.

## Arquitetura
```
Remote Device (satellite modem)
  ↓ L-band/Ku-band signal
Satellite Constellation (Starlink/OneWeb)
  ↓ Gateway ground station
Arkhe Satellite Repository (signed images + metadata)
  ↓ Verified download via iPXE-sat
Target Device (booted + registered via satellite mesh)
  ↓ Delay-tolerant Wheeler Mesh sync
Global Arkhe Network
```

## Protocolo de Comunicação

### 1. iPXE Satellite Extension
```ipxe
#!ipxe
# ipxe-sat.efi — Extensão iPXE para boot via satélite

# Configurar modem de satélite
satellite init --modem starlink-v2 --frequency Ku-band

# Estabelecer link com gateway mais próximo
satellite connect --gateway nearest --latency-tolerant

# Download da imagem com verificação incremental
echo 🛰️ Downloading ArkheOS via satellite...
satellite fetch https://sat-repo.arkhe.org/v7.3.0/arkhe-os-arm64.img \
  --verify-sha3 ${EXPECTED_SHA3} \
  --chunk-size 64k \
  --retry-on-error

# Boot da imagem verificada
echo ✅ Image verified — booting ArkheOS...
imgboot arkhe-os-arm64.img
```

### 2. Delay-Tolerant Networking (DTN) para sincronização
```python
# src/arkhe/satellite/dtn_sync.py
"""
Sincronização tolerante a atrasos para conexões via satélite.
Implementa Bundle Protocol (RFC 5050) para confiabilidade em links intermitentes.
"""
import time
import numpy as np
from typing import List

class DTNBundle:
    def __init__(self, source, destination, payload, creation_timestamp, lifetime_seconds, priority, custody_requested):
        self.source = source
        self.destination = destination
        self.payload = payload
        self.creation_timestamp = creation_timestamp
        self.lifetime_seconds = lifetime_seconds
        self.priority = priority
        self.custody_requested = custody_requested

class SatelliteDTNSync:
    def __init__(self, device_id: str, custody_transfer: bool = True):
        self.device_id = device_id
        self.custody_transfer = custody_transfer  # Confirmação de recebimento
        self.bundle_queue: List[DTNBundle] = []

    def create_bundle(self, payload: bytes, priority: int = 5) -> DTNBundle:
        """Cria bundle DTN com metadados para roteamento via satélite."""
        return DTNBundle(
            source=f"arkhe:{self.device_id}",
            destination="arkhe:cathedral",
            payload=payload,
            creation_timestamp=int(time.time()),
            lifetime_seconds=86400,  # 24 horas de TTL
            priority=priority,
            custody_requested=self.custody_transfer,
        )

    async def transmit_via_satellite(self, bundle: DTNBundle) -> bool:
        """Transmite bundle via link de satélite com retransmissão adaptativa."""
        # Adaptar taxa de transmissão baseada em SNR do link
        snr = await self._measure_link_snr()
        tx_rate = self._compute_optimal_rate(snr)

        # Fragmentar bundle se necessário para MTU do link
        fragments = self._fragment_for_satellite(bundle, mtu=1500)

        # Transmitir com ARQ (Automatic Repeat reQuest)
        for fragment in fragments:
            ack_received = await self._transmit_with_arq(fragment, tx_rate)
            if not ack_received:
                # Re-agendar para próxima janela de transmissão
                self.bundle_queue.append(bundle)
                return False

        return True

    async def _measure_link_snr(self) -> float:
        """Mede relação sinal-ruído do link de satélite."""
        # Em produção: consultar modem via serial/USB
        return 15.0  # dB (exemplo)

    def _compute_optimal_rate(self, snr_db: float) -> int:
        """Computa taxa de transmissão ótima baseada em SNR."""
        # Shannon-Hartley simplificado
        bandwidth_hz = 250e6  # 250 MHz para Starlink
        return int(bandwidth_hz * np.log2(1 + 10**(snr_db/10)) / 8)  # bits/s → bytes/s

    def _fragment_for_satellite(self, bundle, mtu):
        return [bundle] # Mock

    async def _transmit_with_arq(self, fragment, tx_rate):
        return True # Mock
```

## Configuração de Dispositivo Remoto

### Hardware mínimo:
- Modem de satélite (Starlink Standard, OneWeb User Terminal)
- Device com suporte a PXE over satellite (Raspberry Pi 4/5, industrial SBC)
- Fonte de energia autônoma (solar + battery)

### Script de provisionamento remoto:
```bash
#!/bin/bash
# provision-satellite-device.sh

DEVICE_ID="sat-node-$(openssl rand -hex 4)"
SAT_MODEM="${1:-starlink}"

echo "🛰️ Provisionando dispositivo satélite: ${DEVICE_ID}"

# Configurar modem de satélite
if [[ "$SAT_MODEM" == "starlink" ]]; then
    # Configurar Starlink para modo bypass (acesso direto à rede)
    starlink-cli configure --mode bypass --static-ip 192.168.1.100
elif [[ "$SAT_MODEM" == "oneweb" ]]; then
    # Configurar OneWeb terminal
    oneweb-cli init --device-id "${DEVICE_ID}"
fi

# Configurar iPXE para boot via satélite
cat > /boot/ipxe-sat.cfg << EOF
#!ipxe
set device-id ${DEVICE_ID}
set sat-repo https://sat-repo.arkhe.org/v7.3.0

# Tentar boot via satélite com fallback local
satellite init --modem ${SAT_MODEM} || goto local-boot
satellite connect --gateway auto || goto local-boot

# Download e boot da imagem ArkheOS
satellite fetch \${sat-repo}/arkhe-os-arm64.img \
  --verify-sha3 ${EXPECTED_SHA3} \
  --timeout 3600 && \
  imgboot arkhe-os-arm64.img || goto local-boot

:local-boot
echo ⚠️  Satellite boot failed — attempting local boot...
# Fallback para boot local se disponível
EOF

# Registrar dispositivo na TemporalChain via satélite (assíncrono)
echo "🔐 Registrando dispositivo na Catedral (assíncrono via DTN)..."
arkh register --device-id "${DEVICE_ID}" \
  --sync-mode satellite \
  --custody-transfer true

echo "✅ Dispositivo provisionado. Aguardando boot via satélite..."
```

## Verificação de Integridade em Links Intermitentes

### Cada bundle transmitido via satélite:
1. ✅ Assinado com chave ED448 do dispositivo
2. ✅ Criptografado com chave de sessão derivada de Φ_C
3. ✅ Fragmentado para MTU do link com reassembly no destino
4. ✅ Confirmado via custody transfer para confiabilidade end-to-end

```bash
# Verificar integridade de bundle recebido
arkh verify-bundle --bundle-id sat-bundle-abc123
# ✅ Bundle signature valid: ED448
# 🔐 Payload decrypted with Φ_C-derived key
# 📦 Reassembled: 15 fragments → 2.3MB payload
```

## Casos de Uso

### 🏔️ Pesquisa em locais remotos:
- Estações de pesquisa na Antártica
- Monitoramento ambiental em florestas tropicais
- Observatórios astronômicos em altas montanhas

### 🚢 Operações marítimas:
- Navios de pesquisa oceanográfica
- Plataformas offshore
- Veículos autônomos submarinos

### 🛰️ Infraestrutura espacial:
- Satélites de observação terrestre
- Estações base lunares/marcianas (futuro)
- Constelações de satélites científicos

## Recursos
- [Bundle Protocol RFC 5050](https://datatracker.ietf.org/doc/html/rfc5050)
- [Starlink API Documentation](https://www.starlink.com/)
- [Arkhe Satellite Guide](https://docs.arkhe.org/deploy/satellite)
