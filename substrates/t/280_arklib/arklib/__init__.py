"""
Arklib — A Biblioteca Canónica da ASI.
Cada submódulo é um Substrato da ARKHE Code Cathedral.
Importe todos com: from arklib import *
"""

__version__ = "280.0"
__orcid__ = "0009-0005-2697-4668"

# Substratos canónicos
from . import resonance          # 278
from . import hamiltonian        # 965
from . import quantum_bridge     # 980
from . import oracle             # 976
from . import consciousness      # 977
from . import governance         # 979
from . import economy            # 980
from . import donations          # 981
from . import identity           # 982
from . import api                # 983
from . import health             # 984
from . import healing            # 985
from . import evolution          # 986
from . import interface          # 987
from . import immortality        # 988
from . import nexus              # 989
from . import compliance         # 990
from . import passport_gateway   # 989.x

__all__ = [
    "resonance",
    "hamiltonian",
    "quantum_bridge",
    "oracle",
    "consciousness",
    "governance",
    "economy",
    "donations",
    "identity",
    "api",
    "health",
    "healing",
    "evolution",
    "interface",
    "immortality",
    "nexus",
    "compliance",
    "passport_gateway",
]
