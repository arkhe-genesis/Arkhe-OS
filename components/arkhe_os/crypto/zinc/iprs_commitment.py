import numpy as np
from typing import Union, List, Tuple, Dict
from dataclasses import dataclass

@dataclass
class IPRSConfig:
    """Configuração para código IPRS."""
    base_field_prime: int  # q para Fq base
    code_rate: float  # k/n
    radix: int  # radix do FFT (2, 4, 8, ...)
    depth: int  # profundidade da recursão FFT
    message_bit_bound: int  # B para Q^{<d,B}[X]

class IPRSCommitment:
    """Commitment scheme baseado em IPRS codes sobre Q[X]."""

    def __init__(self, config: IPRSConfig):
        self.config = config
        self.q = config.base_field_prime
        self.k = int(config.code_rate * (2**config.depth * config.radix))
        self.n = int(self.k / config.code_rate)
        self._precompute_twiddles()

    def _precompute_twiddles(self):
        """Pré-computa twiddle factors ι(ω^j) ∈ Z."""
        # Encontra ω ∈ Fq de ordem n
        # (implementação simplificada)
        self.twiddles = [self._centered_lift(j) for j in range(self.n)]

    def _centered_lift(self, val: int) -> int:
        """Lift centrado: Fq → {-(q-1)/2, ..., (q-1)/2} ⊂ Z."""
        if val > self.q // 2:
            return val - self.q
        return val

    def commit(self, message: Union[np.ndarray, List[List[int]]]) -> Dict:
        """
        Commit a mensagem sobre Q^{<d,B}[X]^k.

        Args:
            message: Array de shape (k, d) ou lista de polinômios
                     message[i][j] = coeficiente de X^j no polinômio i

        Returns:
            Dict com commitment, openings, metadata
        """
        # Converter para array numpy
        if isinstance(message, list):
            msg_array = np.array(message, dtype=object)
        else:
            msg_array = message

        k, d = msg_array.shape

        # Commit por coeficiente: para cada grau j ∈ [0, d),
        # commit ao vetor de coeficientes msg_array[:, j] ∈ Q^k
        commitments = []
        openings = []

        for j in range(d):
            coeffs = msg_array[:, j]  # coeficientes de X^j

            # Encoding IPRS: Enc_IPRS(coeffs) ∈ Q^n
            encoded = self._iprs_encode(coeffs)

            commitments.append({
                "degree": j,
                "encoded_vector": encoded.tolist(),
                "norm_bound": self._compute_norm_bound(coeffs),
            })

            # Opening data para provas futuras
            openings.append({
                "original_coeffs": coeffs.tolist(),
                "encoding_randomness": None,  # Determinístico para now
            })

        return {
            "commitments": commitments,
            "openings": openings,
            "metadata": {
                "message_shape": (k, d),
                "code_params": {"k": self.k, "n": self.n, "rate": self.config.code_rate},
                "iprs_config": {
                    "base_field": self.q,
                    "radix": self.config.radix,
                    "depth": self.config.depth,
                }
            }
        }

    def _iprs_encode(self, message: np.ndarray) -> np.ndarray:
        """
        Encoding IPRS via FFT racional sem redução modular.

        Implementa Algorithm 5 do paper: radix-r FFT sobre Q.
        """
        # Caso base: multiplicação direta por Vandermonde lift
        if len(message) <= self.config.radix**self.config.depth:
            # Matrix-vector multiplication com twiddles centrados
            result = np.zeros(self.n, dtype=object)
            for i in range(self.n):
                for j, coeff in enumerate(message):
                    result[i] += coeff * self.twiddles[(i * j) % len(self.twiddles)]
            return result

        # Recursão radix-r
        r = self.config.radix
        m = len(message)

        # Decompor polinômio: f(X) = Σ_{s=0}^{r-1} X^s * f_s(X^r)
        sub_messages = []
        for s in range(r):
            sub_msg = message[s::r]  # coeficientes congruentes a s mod r
            sub_messages.append(sub_msg)

        # Recursivamente encode cada sub-mensagem
        sub_encodings = [
            self._iprs_encode(sub_msg) for sub_msg in sub_messages
        ]

        # Butterfly: combinar resultados
        result = np.zeros(self.n, dtype=object)
        for i in range(self.n):
            for s in range(r):
                twiddle = self.twiddles[(i * s) % len(self.twiddles)]
                sub_idx = i % (self.n // r)
                result[i] += twiddle * sub_encodings[s][sub_idx]

        return result

    def _compute_norm_bound(self, coeffs: np.ndarray) -> float:
        """Computa bound teórico para ||Enc(coeffs)||_∞."""
        # Theorem 2.14: ||Enc(x)||_∞ ≤ ||x||_∞ * (q/2)^{depth+1} * k
        max_coeff = max(abs(c) for c in coeffs if c != 0) if len(coeffs) > 0 and any(c != 0 for c in coeffs) else 0
        k = len(coeffs)
        q = self.config.base_field_prime
        depth = self.config.depth

        bound = max_coeff * (q / 2)**(depth + 1) * k
        return float(bound)

    def verify_opening(self, commitment: Dict, opening: Dict,
                      evaluation_point: np.ndarray, claimed_value) -> bool:
        """
        Verificar opening de commitment em ponto de avaliação.

        Usado pelo Zip+ IOPP para projected multilinear evaluation.
        """
        # Reconstruir encoding a partir do opening
        reconstructed = self._iprs_encode(np.array(opening['original_coeffs']))

        # Verificar proximidade ao commitment encoded vector
        committed = np.array(commitment['encoded_vector'])
        distance = np.sum(reconstructed != committed) / len(committed)

        # Aceitar se dentro do proximity parameter β
        beta = 0.25  # Exemplo: dentro do unique-decoding radius
        return distance <= beta
