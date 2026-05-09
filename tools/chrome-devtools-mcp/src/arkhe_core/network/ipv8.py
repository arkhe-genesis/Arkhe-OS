import struct
from dataclasses import dataclass

@dataclass(frozen=True)
class IPv8Address:
    """
    Representação de um endereço IPv8 de 64 bits.
    Estrutura: [ASN (32 bits)][Local/Zone (32 bits)]
    """
    address_int: int

    @classmethod
    def from_string(cls, addr_str: str) -> 'IPv8Address':
        """
        Converte string para IPv8Address.
        Suporta:
        - ASN.Z.N.N.N (5 partes)
        - r.r.r.r.n.n.n.n (8 partes, ASN em network byte order + Host)
        """
        parts = addr_str.split('.')
        if len(parts) == 5:
            # Formato ASN.Z.N.N.N
            asn = int(parts[0])
            rest = (int(parts[1]) << 24) | (int(parts[2]) << 16) | (int(parts[3]) << 8) | int(parts[4])
            return cls((asn << 32) | rest)
        elif len(parts) == 8:
            # Formato r.r.r.r.n.n.n.n
            asn = (int(parts[0]) << 24) | (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])
            host = (int(parts[4]) << 24) | (int(parts[5]) << 16) | (int(parts[6]) << 8) | int(parts[7])
            return cls((asn << 32) | host)
        elif len(parts) == 9:
            # Formato ASN.r.r.r.r.n.n.n.n (ASN + full IP parts)
            asn = int(parts[0])
            host = (int(parts[5]) << 24) | (int(parts[6]) << 16) | (int(parts[7]) << 8) | int(parts[8])
            # Ignora os r.r.r.r intermediários se for redundante, ou usa para compor rest se necessário.
            # No contexto da Deliberação, r.r.r.r é o prefixo de zona.
            rest = (int(parts[1]) << 24) | (int(parts[2]) << 16) | (int(parts[3]) << 8) | int(parts[4])
            # Mas espera, r.r.r.r costuma ser o ASN em byte order na especificação IPv8.
            # Vamos simplificar para o que o ZoneServer gera: ASN.127.1.0.0.10.0.0.1
            return cls((asn << 32) | host)
        else:
            raise ValueError(f"Formato de endereço IPv8 inválido: {addr_str}")

    def __str__(self) -> str:
        asn = self.address_int >> 32
        rest = self.address_int & 0xFFFFFFFF
        r1 = (rest >> 24) & 0xFF
        r2 = (rest >> 16) & 0xFF
        r3 = (rest >> 8) & 0xFF
        r4 = rest & 0xFF
        return f"{asn}.{r1}.{r2}.{r3}.{r4}"

    def to_bytes(self) -> bytes:
        return struct.pack('!Q', self.address_int)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'IPv8Address':
        return cls(struct.unpack('!Q', data)[0])

def calculate_cost_factor(distance_km: float, coherence_r: float, packet_loss: float = 0.0) -> float:
    """
    Calcula o Cost Factor (CF) conforme Deliberação #389-Ω.
    CF = (d_geo / c) + alpha * (1 - R) + beta * PacketLoss
    """
    C = 299792.458  # Velocidade da luz em km/s
    ALPHA = 1000.0  # Fator de penalidade para incoerência
    BETA = 500.0   # Fator de penalidade para perda de pacotes

    physical_floor = distance_km / C
    coherence_penalty = ALPHA * (1.0 - coherence_r)
    noise_penalty = BETA * packet_loss

    return physical_floor + coherence_penalty + noise_penalty
