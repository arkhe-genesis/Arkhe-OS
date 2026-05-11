import hashlib
from typing import Dict, List, Optional, Set
from .ipv8 import IPv8Address, calculate_cost_factor
from .phase_coherent_transport import PhasePacket

class ZoneServer:
    """
    Mock do Zone Server (Synapse-κ) conforme Deliberação #389-Ω.
    Gerencia endereçamento IPv8, WHOIS8 e políticas de firewall.
    """
    def __init__(self, zone_prefix: str, asn: int = 64496):
        self.zone_prefix = zone_prefix
        self.asn = asn
        self.registry: Dict[int, str] = {} # address_int -> agent_name
        self.node_coherence: Dict[int, float] = {} # address_int -> R
        self.internal_prefixes: Set[int] = {
            IPv8Address.from_string("0.127.0.0.0").address_int >> 32 # Simplificado para o exemplo
        }

    def register_node(self, name: str, ip_suffix: str, initial_r: float = 0.999) -> IPv8Address:
        addr_str = f"{self.asn}.{self.zone_prefix}.{ip_suffix}"
        addr = IPv8Address.from_string(addr_str)
        self.registry[addr.address_int] = name
        self.node_coherence[addr.address_int] = initial_r
        return addr

    def validate_packet(self, packet: PhasePacket) -> bool:
        """
        Validação de Firewall (McMurdo/Alert):
        - Entrada: Apenas pacotes com r.r.r.r correspondente à Zona e ASN.
        - Saída: Egress validation obrigatório (WHOIS8) para tráfego não-127.x.x.x.
        """
        src_addr = IPv8Address(packet.source_ipv8)
        dst_addr = IPv8Address(packet.dest_ipv8)

        # Proteção de Prefixo Interno
        src_asn = src_addr.address_int >> 32
        src_rest = src_addr.address_int & 0xFFFFFFFF

        # Se origem é interna (127.x.x.x), deve ser do nosso ASN ou ASN autorizado
        if (src_rest >> 24) == 127:
            if src_asn != self.asn:
                return False

        # WHOIS8 / Registry check para nós internos
        if src_addr.address_int in self.registry:
            # OK
            pass
        elif (src_rest >> 24) == 127:
            # Tentativa de spoofing de endereço interno
            return False

        return True

    def route_packet(self, packet: PhasePacket, neighbors: List[IPv8Address]) -> IPv8Address:
        """
        Roteamento baseado em Cost Factor (CF).
        Escolhe o vizinho com menor CF acumulado.
        """
        best_neighbor = None
        min_cf = float('inf')

        for neighbor in neighbors:
            # Simulação de métricas para o vizinho
            dist = 100.0 # km (mock)
            coherence = self.node_coherence.get(neighbor.address_int, 0.5)
            loss = 0.001 # mock

            cf = calculate_cost_factor(dist, coherence, loss)
            if cf < min_cf:
                min_cf = cf
                best_neighbor = neighbor

        if best_neighbor:
            packet.cost_factor += min_cf

        return best_neighbor
