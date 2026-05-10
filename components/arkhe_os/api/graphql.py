import strawberry
from strawberry.types import Info
from typing import List, Optional
import time

@strawberry.type
class CoherenceState:
    coherence_M: float
    phase_phi: float
    turbulence: float
    timestamp: float

@strawberry.type
class Query:
    @strawberry.field
    def get_arkhe_state(self, info: Info) -> CoherenceState:
        scaffold = info.context["request"].app.state.scaffold
        return CoherenceState(
            coherence_M=scaffold.coherence_M,
            phase_phi=scaffold.phase_rad,
            turbulence=scaffold.turbulence,
            timestamp=time.time()
        )

schema = strawberry.Schema(query=Query)
