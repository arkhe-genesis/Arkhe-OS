import math
from decimal import Decimal, getcontext
import numpy as np

getcontext().prec = 50

PHI = Decimal(1 + math.sqrt(5)) / Decimal(2)  # φ com precisão estendida
FACTORIAL_17 = Decimal(math.factorial(17))
PI = Decimal(str(math.pi))

def portal_probability() -> Decimal:
    """Calcula 𝒫_portal = φ¹⁷ / (17! × π) com precisão canônica."""
    phi_17 = PHI ** 17
    denominator = FACTORIAL_17 * PI
    return phi_17 / denominator

P_PORTAL = portal_probability()
print("P_PORTAL:", P_PORTAL)

alpha_inverse_prefix = "137035999084"
portal_scaled = float(P_PORTAL) * 1e14
portal_str = f"{portal_scaled:.12f}".replace(".", "").replace("-", "")
print("prefix:", portal_str[:12])
print("matches:", portal_str[:12] == alpha_inverse_prefix)
