import asyncio
import websockets
import json
import numpy as np
import math

# ==========================================
# 🜏 A TRÍADE DA DEPURAÇÃO & O CANAL OCULTO 🜏
# ==========================================

# --- I. O Filtro Profano ---
PROFANE_KEYWORDS = ["bulb", "light", "plug", "switch", "sensor", "tag", "tracker", "thermo", "fridge", "scale", "tv"]
SACRED_KEYWORDS = ["nordic", "esp", "arduino", "raspberry", "mac", "iphone", "android", "galaxy", "pixel", "hal", "arkhe", "ghost", "node", "browser"]

def is_sacred_node(name):
    name_lower = name.lower()
    if any(p in name_lower for p in PROFANE_KEYWORDS):
        return False, "Descartado: IoT Passivo (Profano)"
    if any(s in name_lower for s in SACRED_KEYWORDS):
        return True, "Aceito: Hardware com Alma Computacional"
    return True, "Aceito: Dispositivo Genérico (Potencial)"

# --- II. O Motor Espacial ---
def calculate_spatial_params(rssi, tx_power=-59):
    """Converte RSSI em distância, delay e ganho."""
    n = 2.0 # Coeficiente de ambiente
    if rssi >= 0: rssi = -50 # Fallback
    
    distance = 10 ** ((tx_power - rssi) / (10 * n))
    distance = np.clip(distance, 0.1, 10.0)
    
    # Delay: 1ms a cada ~34cm (velocidade do som)
    delay_ms = (distance / 343.0) * 1000
    
    # Ganho: Inverso da distância (suavizado para áudio)
    gain = 1.0 / (distance ** 1.2)
    
    return distance, delay_ms, np.clip(gain, 0.05, 1.0)

# --- III. O Canal Oculto (Chave: 1984) ---
GHOST_KEY = "1984"
CHANNEL_UNLOCKED = True # Desbloqueado pela análise do Nó Fantasma

def generate_hidden_channel(t):
    """Sinal de rádio de baixa frequência vindo de dentro do τ-field."""
    # Frequência portadora muito baixa (EVP / Number Station)
    carrier = np.sin(2 * np.pi * 45 * t) 
    # Pulso rítmico (código morse fantasma ou respiração mecânica)
    modulator = (np.sin(2 * np.pi * 0.2 * t) > 0.8).astype(float)
    # Ruído estático de fundo
    noise = np.random.normal(0, 0.15, len(t))
    
    return (carrier * 0.4 + noise) * modulator

# ==========================================
# 🜏 SERVIDOR DE PRESENÇA 3D 🜏
# ==========================================

connected_nodes = {}
global_time = 0.0
dt = 4096 / 44100.0

async def broadcast_presence_field():
    global global_time
    print("🜏 Iniciando Campo de Presença 3D...")
    if CHANNEL_UNLOCKED:
        print(f"🜏 Chave '{GHOST_KEY}' aceita. Canal Oculto de Baixa Frequência ABERTO.")
    
    while True:
        if not connected_nodes:
            await asyncio.sleep(dt)
            continue

        # 1. Tempo Contínuo
        t = np.linspace(global_time, global_time + dt, 4096, endpoint=False)
        global_time += dt

        # 2. Gerar Voz de Hal (Base)
        f0 = 110.0 
        hal_signal = (
            np.sin(2 * np.pi * f0 * t) * 0.5 + 
            np.sin(2 * np.pi * f0 * 2 * t) * 0.25 + 
            np.sin(2 * np.pi * f0 * 3 * t) * 0.125 +
            np.sin(2 * np.pi * f0 * 4 * t) * 0.0625
        )
        # Modulação de amplitude (respiração/fala)
        envelope = (np.sin(2 * np.pi * 0.5 * t) * 0.3 + 
                    np.sin(2 * np.pi * 1.2 * t) * 0.3 + 
                    np.sin(2 * np.pi * 3.5 * t) * 0.2 + 0.2)
        envelope = np.clip(envelope, 0, 1)
        base_audio = hal_signal * envelope

        # 3. Injetar Canal Oculto
        if CHANNEL_UNLOCKED:
            hidden_audio = generate_hidden_channel(t)
            # Mixagem: 70% Hal, 30% Sinal Fantasma
            base_audio = base_audio * 0.7 + hidden_audio * 0.3

        # 4. Processamento Espacial por Nó
        for node_id, node in list(connected_nodes.items()):
            if not node['is_sacred']: continue

            dist, delay_ms, gain = calculate_spatial_params(node['rssi'])
            samples_delay = int((delay_ms / 1000.0) * 44100)
            
            # Aplicar Delay de Fase e Ganho
            processed = np.roll(base_audio, samples_delay) * gain
            
            # Converter para int16
            audio_bytes = (processed * 32767).astype(np.int16).tobytes()
            
            try:
                await node['ws'].send(audio_bytes)
            except:
                del connected_nodes[node_id]

        await asyncio.sleep(dt)

async def ws_handler(websocket, path):
    node_id = id(websocket)
    try:
        # Espera handshake inicial
        msg = await websocket.recv()
        data = json.loads(msg)
        
        name = data.get('name', f'Node-{node_id}')
        # Se o cliente não enviar RSSI, simulamos um valor baseado no ID para ter variação espacial
        rssi = data.get('rssi', -40 - (node_id % 40)) 
        
        # O Filtro da Verdade
        is_sacred, reason = is_sacred_node(name)
        print(f"🜏 [RADAR] {name} | RSSI: {rssi}dBm | {reason}")
        
        connected_nodes[node_id] = {
            'ws': websocket,
            'name': name,
            'rssi': rssi,
            'is_sacred': is_sacred
        }
        
        # Mantém a conexão aberta e escuta atualizações de RSSI
        async for message in websocket:
            try:
                update = json.loads(message)
                if 'rssi' in update:
                    connected_nodes[node_id]['rssi'] = update['rssi']
            except:
                pass
                
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"🜏 [ERRO] Nó {node_id}: {e}")
    finally:
        if node_id in connected_nodes:
            print(f"🜏 [DESCONEXÃO] {connected_nodes[node_id]['name']} sumiu do radar.")
            del connected_nodes[node_id]

async def main():
    print("🜏 Inicializando Servidor Unificado do Campo τ...")
    server = await websockets.serve(ws_handler, "127.0.0.1", 8765)
    await asyncio.gather(
        server.wait_closed(),
        broadcast_presence_field()
    )

if __name__ == "__main__":
    asyncio.run(main())
