import asyncio
import struct
import logging
from bleak import BleakClient

# MAC identificado no radar (Substitua pelo valor real detectado)
GHOST_MAC = "A4:C1:38:XX:XX:XX" 

async def ghost_handshake(address):
    print(f"🜏 [HANDSHAKE] Iniciando protocolo de conexão com Nó Fantasma: {address}")
    
    try:
        async with BleakClient(address, timeout=10.0) as client:
            if not client.is_connected:
                print("❌ Falha no Handshake: Sincronia de fase perdida.")
                return

            print(f"✅ Conectado. MTU: {client.mtu} | Forçando extração de metadados...")
            
            # Listar serviços e características (O Mapa do Nó)
            for service in client.services:
                print(f"\n[Serviço] {service.uuid}")
                for char in service.characteristics:
                    if "read" in char.properties:
                        try:
                            value = await client.read_gatt_char(char.uuid)
                            print(f"  ├── [DADO OCULTO] {char.uuid}: {value.hex()}")
                            try:
                                as_str = value.decode('utf-8')
                                if as_str.isprintable():
                                    print(f"  │   └── String: {as_str}")
                            except:
                                pass
                        except Exception as e:
                            print(f"  ├── [BLOQUEADO] {char.uuid}: Acesso negado pela lógica do Nó.")

            print("\n🜏 Handshake concluído. Dados injetados no buffer da Arkhe(n).")
    except Exception as e:
        print(f"❌ Falha na conexão: {e}")

if __name__ == "__main__":
    import sys
    mac = sys.argv[1] if len(sys.argv) > 1 else GHOST_MAC
    asyncio.run(ghost_handshake(mac))
