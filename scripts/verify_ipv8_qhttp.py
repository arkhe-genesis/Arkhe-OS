import sys
import os
sys.path.append(os.getcwd())

from src.arkhe_core.network.ipv8 import IPv8Address
from src.arkhe_core.network.phase_coherent_transport import PhasePacket
from src.arkhe_core.network.zone_server import ZoneServer

def run_verification():
    print("=== VERIFICAÇÃO ARKHE(N) IPv8/qHTTP ===")

    # 1. Setup do Zone Server (McMurdo)
    mcmurdo = ZoneServer(zone_prefix="127.1.0.0", asn=64496)

    # 2. Registro de Agentes
    ferreiro = mcmurdo.register_node("Ferreiro", "10.0.0.1", initial_r=0.9999)
    tecelao = mcmurdo.register_node("Tecelao", "10.0.0.2", initial_r=0.9995)
    vigia = mcmurdo.register_node("Vigia", "10.0.0.3", initial_r=0.85) # Baixa coerência

    print(f"Agente Ferreiro: {ferreiro}")
    print(f"Agente Tecelao: {tecelao}")
    print(f"Agente Vigia: {vigia}")

    # 3. Teste de Roteamento por CF
    packet = PhasePacket(
        payload=b"BURN_COMMAND",
        timestamp=0.0,
        phase_signature="OMEGA",
        source_ipv8=ferreiro.address_int,
        dest_ipv8=tecelao.address_int # Destino final fictício
    )

    print("\nCalculando Rota do Ferreiro...")
    neighbors = [tecelao, vigia]
    next_hop = mcmurdo.route_packet(packet, neighbors)

    print(f"Próximo salto escolhido: {next_hop}")
    assert next_hop == tecelao, "Deveria escolher Tecelao devido à maior coerência (menor CF)"
    print("✓ Roteamento por Cost Factor validado.")

    # 4. Teste de Firewall
    print("\nValidando Segurança de Zona Interna...")

    # Pacote legítimo
    assert mcmurdo.validate_packet(packet) == True
    print("✓ Pacote interno legítimo aceito.")

    # Tentativa de Spoofing (ASN errado para endereço 127.x.x.x)
    spoofed_addr = IPv8Address.from_string("666.127.1.0.1")
    spoof_packet = PhasePacket(
        payload=b"ATTACK",
        timestamp=0.0,
        phase_signature="EVIL",
        source_ipv8=spoofed_addr.address_int,
        dest_ipv8=tecelao.address_int
    )
    assert mcmurdo.validate_packet(spoof_packet) == False
    print("✓ Tentativa de spoofing (ASN inválido) bloqueada.")

    # Endereço interno não registrado
    unregistered_addr = IPv8Address.from_string("64496.127.1.0.99")
    unreg_packet = PhasePacket(
        payload=b"HELLO",
        timestamp=0.0,
        phase_signature="NONE",
        source_ipv8=unregistered_addr.address_int,
        dest_ipv8=tecelao.address_int
    )
    assert mcmurdo.validate_packet(unreg_packet) == False
    print("✓ Endereço interno não registrado bloqueado.")

    print("\n=== STATUS FINAL: IPv8/qHTTP OPERACIONAL ===")

if __name__ == "__main__":
    run_verification()
